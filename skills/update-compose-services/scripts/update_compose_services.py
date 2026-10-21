#!/usr/bin/env python3
"""Conservative, explicit Compose code updates. Python 3.10+, Windows/Linux."""
import argparse
import contextlib
import hashlib
import json
import os
import ntpath
import posixpath
from pathlib import Path, PureWindowsPath, PurePosixPath
import re
import subprocess
import stat
import sys
import tempfile
import time


class Stop(Exception):
    pass


def require(ok, message):
    if not ok:
        raise Stop(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def run(argv, cwd):
    environment = {k: v for k, v in os.environ.items() if not k.upper().startswith('COMPOSE_')}
    result = subprocess.run(argv, cwd=cwd, env=environment, capture_output=True, text=True, encoding='utf-8', errors='strict', timeout=600, shell=False)
    # Neither command arguments nor external output are safe to print.
    require(result.returncode == 0, 'external command failed (output suppressed)')
    return result.stdout.strip()


def path_key(value, windows=None):
    """Compare host paths without interpreting Windows paths as POSIX paths."""
    windows = os.name == 'nt' if windows is None else windows
    pure = PureWindowsPath(value) if windows else PurePosixPath(value)
    require(pure.is_absolute(), 'absolute host path required')
    return ntpath.normcase(ntpath.normpath(str(pure))) if windows else posixpath.normpath(str(pure))


def relative_source(value):
    # One portable Git-relative spelling; reject drives, UNC, traversal and ADS.
    require(isinstance(value, str) and value and not value.startswith('-'), 'invalid relative path')
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    require(not posix.is_absolute() and not windows.drive and not windows.root
            and '..' not in posix.parts and '\\' not in value and ':' not in value
            and all(part not in ('', '.') for part in value.split('/')), 'invalid relative path')
    return value


def file_metadata(path):
    """Detect ordinary edits/replacements without opening confidential files."""
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not (getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)),
            'env must be a regular non-symlink file')
    return {k: getattr(info, k) for k in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')}


def image_key(tag):
    # Docker Hub's implicit registry/library and latest are the same local tag.
    require(isinstance(tag, str) and tag and '$' not in tag, 'literal image tag required')
    first = tag.split('/', 1)[0]
    if '/' not in tag or not ('.' in first or ':' in first or first == 'localhost'):
        tag = 'docker.io/' + tag
    if tag.startswith('index.docker.io/'):
        tag = 'docker.io/' + tag[len('index.docker.io/'):]
    if tag.startswith('docker.io/') and '/' not in tag[len('docker.io/'):]:
        tag = 'docker.io/library/' + tag[len('docker.io/'):]
    return tag if '@' in tag or ':' in tag.rsplit('/', 1)[-1] else tag + ':latest'


def target_volume_safe(volume):
    if isinstance(volume, dict):
        return volume.get('type') == 'volume' and bool(volume.get('source'))
    # Unnormalized short syntax: allow named volumes only. Unknown/variable or
    # host-path sources fail closed, including Windows drive/UNC paths.
    if isinstance(volume, str) and ':' in volume:
        source = volume.split(':', 1)[0]
        return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', source)) and not re.match(r'^[A-Za-z]:[/\\]', volume)
    return False


class Deployment:
    def __init__(self, config):
        self.c = config
        require(set(config) == {'repo', 'remote', 'remote_url', 'branch', 'context', 'project',
                               'compose', 'env_file', 'services', 'source_paths',
                               'code_reviewed_no_migrations', 'rollback_allowed', 'target_sha'}, 'invalid configuration keys')
        require(isinstance(config['target_sha'], str) and re.fullmatch(r'[0-9a-f]{40}', config['target_sha']), 'exact target SHA required')
        for key in ('remote', 'branch', 'context', 'project'):
            require(isinstance(config[key], str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', config[key]), 'invalid identifier')
        require(not re.search(r'://[^/]*@', config['remote_url']), 'credential-bearing remote unsupported')
        path_key(config['repo'])
        path_key(config['env_file'])
        self.repo = Path(config['repo']).resolve(strict=True)
        require(config['services'] and len(set(config['services'])) == len(config['services']), 'empty/duplicate allowlist')
        require(all(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', s) for s in config['services']), 'invalid service')
        require(config['source_paths'] and config['code_reviewed_no_migrations'] is True, 'source review required')
        for p in config['compose'] + config['source_paths']:
            relative_source(p)
        require(config['compose'], 'compose files required')
        self.env = Path(config['env_file']).absolute()
        file_metadata(self.env)

    def git(self, *args):
        # A real empty directory works with native Git on both Windows and Linux.
        with tempfile.TemporaryDirectory(prefix='compose-update-hooks-') as hooks:
            return run(['git', '-c', 'core.hooksPath=' + hooks, '-c', 'core.fsmonitor=false',
                        '-c', 'core.quotePath=false', *args], self.repo)

    def docker(self, *args):
        return run(['docker', '--context', self.c['context'], *args], self.repo)

    def compose(self, *args, diagnostic=False):
        if diagnostic:
            # Explicit empty interpolation file prevents Compose loading the real .env.
            # Service env_file content is disabled by --no-env-resolution at the caller.
            with tempfile.TemporaryDirectory(prefix='compose-update-no-env-') as folder:
                empty = Path(folder) / 'empty.env'
                empty.touch()
                return self._compose(empty, *args)
        return self._compose(self.env, *args)

    def _compose(self, env, *args):
        argv = ['compose', '--project-name', self.c['project'], '--project-directory', str(self.repo), '--env-file', str(env)]
        for p in self.c['compose']:
            argv += ['-f', str(self.repo / p)]
        return self.docker(*argv, *args)

    def clean(self):
        require(path_key(self.git('rev-parse', '--show-toplevel')) == path_key(str(self.repo)), 'not repository root')
        require(self.git('branch', '--show-current') == self.c['branch'], 'unexpected branch')
        require(not self.git('status', '--porcelain', '--untracked-files=all'), 'dirty/untracked worktree')
        # REBASE_HEAD may remain after a completed rebase; it is not an active
        # operation marker. Git-resolved rebase state directories are decisive.
        for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'rebase-merge', 'rebase-apply', 'sequencer'):
            p = Path(self.git('rev-parse', '--git-path', name))
            require(not (self.repo / p).exists(), 'git operation in progress')
        require(self.git('remote', 'get-url', self.c['remote']) == self.c['remote_url'], 'remote mismatch')
        require(not any(line.startswith('120000 ') for line in self.git('ls-files', '--stage').splitlines()), 'symlinks unsupported')
        require(not any(line.startswith('160000 ') for line in self.git('ls-files', '--stage').splitlines()), 'submodules unsupported')

    def model(self):
        for p in self.c['compose']:
            text = (self.repo / p).read_text(encoding='utf-8-sig')
            require(not re.search(r'^\s*(include|profiles|extends|develop|provider)\s*:', text, re.M), 'special compose unsupported')
        model = json.loads(self.compose('config', '--no-interpolate', '--no-env-resolution', '--no-normalize', '--no-path-resolution', '--format', 'json', diagnostic=True))
        services = model.get('services', {})
        require(set(self.c['services']) <= services.keys(), 'service mismatch')
        tags = []
        allowed = {'build', 'image', 'command', 'entrypoint', 'environment', 'env_file', 'ports',
                   'expose', 'networks', 'volumes', 'depends_on', 'healthcheck', 'restart', 'labels',
                   'container_name', 'working_dir', 'user', 'init', 'stop_grace_period', 'logging', 'read_only', 'tmpfs'}
        for name, service in services.items():
            require(not (set(service) - allowed), 'unsupported service settings')
            if name in self.c['services']:
                require(all(target_volume_safe(v) for v in service.get('volumes', [])), 'target bind/anonymous mounts unsupported')
                require(service.get('build'), 'local build required')
                build = service['build']
                require(isinstance(build, dict) and set(build) <= {'context', 'dockerfile', 'args', 'target'}, 'special build unsupported')
                context = build['context']
                require(isinstance(context, str) and '$' not in context, 'variable build context unsupported')
                require(path_key(str((self.repo / context).resolve(strict=True))) == path_key(str(self.repo)), 'build context must be repo root')
                dockerfile_path = relative_source(build.get('dockerfile', 'Dockerfile'))
                require('$' not in dockerfile_path, 'variable Dockerfile unsupported')
                dockerfile = self.repo / dockerfile_path
                require(dockerfile.resolve(strict=True).is_relative_to(self.repo) and dockerfile.is_file()
                        and not dockerfile.is_symlink(), 'Dockerfile must be a regular file inside repo')
            # Compose's established default name for a build-only service. Verify against
            # the running container before building; do not change the Compose model.
            image = service.get('image') or self.c['project'] + '-' + name
            require(isinstance(image, str) and '$' not in image, 'variable image tags unsupported')
            tags.append(image_key(image))
        require(len(tags) == len(set(tags)), 'shared image tags unsupported')
        return model

    def env_metadata(self, model):
        paths = {self.env}
        for service in model['services'].values():
            for entry in service.get('env_file', []):
                value = entry['path'] if isinstance(entry, dict) else entry
                require(isinstance(value, str) and '$' not in value, 'variable env path unsupported')
                path = Path(value)
                paths.add(path if path.is_absolute() else self.repo / path)
        return {str(p): file_metadata(p) for p in sorted(paths, key=str)}

    def image_tags(self, model, before):
        tags = {}
        for name in self.c['services']:
            tag = model['services'][name].get('image') or self.c['project'] + '-' + name
            require(image_key(before[name]['image_tag']) == image_key(tag), 'running image tag differs from compose')
            tags[name] = before[name]['image_tag']
        canonical = {image_key(tag) for tag in tags.values()}
        require(len(canonical) == len(tags), 'shared image tags unsupported')
        for name, row in before.items():
            if name not in tags:
                require(image_key(row['image_tag']) not in canonical, 'target image tag used by non-target')
        return tags

    def containers(self):
        ids = self.docker('ps', '-aq', '--filter', 'label=com.docker.compose.project=' + self.c['project']).split()
        require(ids, 'no existing containers')
        # Never retrieve Config.Env, healthcheck output, commands, or arbitrary labels.
        fields = {'id': '.Id', 'image': '.Image', 'image_tag': '.Config.Image',
                  'status': '.State.Status', 'restarts': '.RestartCount',
                  'readonly': '.HostConfig.ReadonlyRootfs', 'tmpfs': '(index .HostConfig "Tmpfs")',
                  'mounts': '.Mounts', 'ports': '(index .HostConfig "PortBindings")',
                  'network_mode': '.HostConfig.NetworkMode'}
        template = '{' + ','.join(json.dumps(k) + ':{{json ' + v + '}}' for k, v in fields.items())
        for key in ('service', 'config-hash', 'project.working_dir', 'project.config_files', 'oneoff'):
            template += ',' + json.dumps(key) + ':{{json (index .Config.Labels "com.docker.compose.' + key + '")}}'
        template += ',"health":{{with (index .State "Health")}}{{json .Status}}{{else}}"none"{{end}}}'
        rows = [json.loads(line) for line in self.docker('inspect', '--type', 'container', '--format', template, *ids).splitlines()]
        result = {}
        for row in rows:
            require((row.get('oneoff') or 'False').lower() == 'false', 'oneoff unsupported')
            require(path_key(row.get('project.working_dir') or '') == path_key(str(self.repo)), 'project repository mismatch')
            files = (row.get('project.config_files') or '').split(',')
            require({path_key(p) for p in files} == {path_key(str(self.repo / p)) for p in self.c['compose']}, 'project compose mismatch')
            name = row['service']
            require(name not in result, 'scaled/duplicate service unsupported')
            result[name] = row
        return result

    def inspect(self):
        self.clean()
        head = self.git('rev-parse', 'HEAD')
        target = self.git('rev-parse', '--verify', 'refs/remotes/' + self.c['remote'] + '/' + self.c['branch'] + '^{commit}')
        require(target == self.c['target_sha'], 'remote differs from pinned target SHA')
        self.git('merge-base', '--is-ancestor', head, target)
        tree = self.git('ls-tree', '-r', target)
        require(not any(line.startswith(('120000 ', '160000 ')) for line in tree.splitlines()), 'target symlink/submodule unsupported')
        paths = self.git('diff', '--name-only', head, target, '--').splitlines()
        for p in paths:
            require(any(p == x or p.startswith(x.rstrip('/') + '/') for x in self.c['source_paths']), 'change outside reviewed source paths')
            require(not re.search(r'(^|/)(migrations?|\.env[^/]*)(/|$)', p, re.I), 'migration/env changes unsupported')
        for p in self.c['compose']:
            require(not self.git('diff', head, target, '--', p), 'compose change unsupported')
        model = self.model()
        before = self.containers()
        require(set(before) == set(model['services']), 'running project does not match compose')
        require(all(before[n]['status'] == 'running' and before[n]['health'] in ('none', 'healthy') for n in self.c['services']), 'target baseline unhealthy')
        tags = self.image_tags(model, before)
        return {'version': 2, 'config': self.c, 'head': head, 'target': target,
                'model_hash': digest(model), 'env_metadata': self.env_metadata(model), 'image_tags': tags,
                'before': before, 'changed_paths': paths}

    def verify_state(self, plan, old=False):
        now = self.containers()
        require(set(now) == set(plan['before']), 'container set changed')
        for name, baseline in plan['before'].items():
            if name not in self.c['services']:
                require(now[name] == baseline, 'non-target changed')
            else:
                require(now[name]['status'] == 'running' and now[name]['health'] in ('healthy', 'none'), 'target unhealthy')
                require(all(now[name].get(k) == baseline.get(k) for k in
                            ('config-hash', 'image_tag', 'readonly', 'tmpfs', 'mounts', 'ports', 'network_mode')),
                        'target runtime configuration changed')
                if old:
                    require(now[name]['image'] == baseline['image'], 'rollback image mismatch')
        return now

    def recreate(self):
        self.compose('up', '-d', '--no-deps', '--no-build', '--pull', 'never', '--force-recreate',
                     '--wait', '--wait-timeout', '60', *self.c['services'])

    def apply(self, plan, approval, state):
        require(digest(plan) == approval, 'approval mismatch')
        require(self.inspect() == plan, 'plan changed')
        require(not state.exists(), 'state already exists')
        saved = {'plan': plan, 'phase': 'started'}
        write_private(state, saved)
        # Keep immutable old images reachable before build moves any service tags.
        for name in self.c['services']:
            self.docker('image', 'tag', plan['before'][name]['image'],
                        'compose-update-backup:' + approval[:20] + '-' + name)
        self.git('merge', '--ff-only', '--no-edit', plan['target'])
        self.clean()
        require(self.git('rev-parse', 'HEAD') == plan['target'], 'SHA mismatch')
        require(digest(self.model()) == plan['model_hash'], 'effective configuration changed')
        require(self.containers() == plan['before'], 'containers changed before build')
        self.compose('build', *self.c['services'])
        model = self.model()
        expected = {name: self.docker('image', 'inspect', '--format', '{{.Id}}', plan['image_tags'][name]) for name in self.c['services']}
        require(self.containers() == plan['before'], 'containers changed during build')
        require(digest(self.model()) == plan['model_hash'], 'configuration changed during build')
        self.clean()
        require(self.c == plan['config'], 'config changed during build')
        require(self.git('rev-parse', 'HEAD') == plan['target'], 'HEAD changed during build')
        require(self.env_metadata(model) == plan['env_metadata'], 'env metadata changed during build')
        saved['built'] = expected
        saved['phase'] = 'built'
        write_private(state, saved, replace=True)
        self.recreate()
        settled = self.verify_state(plan)
        time.sleep(1)
        saved['after'] = self.verify_state(plan)
        require(saved['after'] == settled, 'target not stable')
        require(all(saved['after'][n]['image'] == image for n, image in expected.items()), 'built image mismatch')
        saved['phase'] = 'complete'
        write_private(state, saved, replace=True)

    def rollback(self, saved, approval):
        plan = saved['plan']
        require(digest(plan) == approval and self.c['rollback_allowed'] is True, 'rollback not approved')
        self.clean()
        require(self.git('rev-parse', 'HEAD') == plan['target'], 'rollback HEAD mismatch')
        require(digest(self.model()) == plan['model_hash'], 'rollback configuration changed')
        require(self.env_metadata(self.model()) == plan['env_metadata'], 'rollback env metadata changed')
        now = self.containers()
        require(set(now) == set(plan['before']), 'container set changed')
        for name, baseline in plan['before'].items():
            if name not in self.c['services']:
                require(now[name] == baseline, 'non-target changed')
        # Restore only approved service tags; preserve the original Compose labels/config.
        model = self.model()
        for name in self.c['services']:
            permitted = {plan['before'][name]['image'], saved.get('built', {}).get(name)}
            require(now[name]['image'] in permitted, 'unexpected rollback image')
            if saved.get('phase') == 'complete':
                require(now[name] == saved['after'][name], 'target changed after apply')
        for name in self.c['services']:
            self.docker('image', 'tag', plan['before'][name]['image'], plan['image_tags'][name])
        self.recreate()
        self.verify_state(plan, old=True)


def write_private(path, value, replace=False):
    if not replace:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as out:
            json.dump(value, out, ensure_ascii=True, sort_keys=True)
        return
    # Never truncate/follow the old path. Close the temporary before Windows rename.
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)
            and not (getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)),
            'private state must be a regular file')
    fd, temporary = tempfile.mkstemp(prefix='.compose-update-', dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as out:
            json.dump(value, out, ensure_ascii=True, sort_keys=True)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextlib.contextmanager
def file_lock(path, windows=None):
    """Nonblocking OS lock; closing the descriptor releases it even on process exit."""
    windows = os.name == 'nt' if windows is None else windows
    with path.open('a+b') as stream:
        if windows:
            import msvcrt
            stream.seek(0)
            try:
                # Lock byte zero, including for an empty file; never append/delete a lock inode.
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise Stop('cannot acquire update lock (busy or inaccessible)') from None
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise Stop('cannot acquire update lock (busy or inaccessible)') from None
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)


@contextlib.contextmanager
def locked(deployment):
    # Git common dir coordinates worktrees and different config file names.
    common = Path(deployment.git('rev-parse', '--git-common-dir'))
    with file_lock(deployment.repo / common / 'compose-update.lock'):
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect', 'fetch', 'apply', 'rollback'])
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--state', type=Path)
    parser.add_argument('--approve')
    args = parser.parse_args()
    try:
        for private_path in (args.config, args.plan, args.state):
            if private_path is not None:
                path_key(str(private_path))
        d = Deployment(json.loads(args.config.read_text(encoding='utf-8-sig')))
        if args.action == 'inspect':
            plan = d.inspect()
            if args.plan:
                write_private(args.plan, plan)
            print(json.dumps({'approval': digest(plan), 'head': plan['head'], 'target': plan['target'],
                              'services': d.c['services'], 'changed_count': len(plan['changed_paths'])}))
        else:
            with locked(d):
                if args.action == 'fetch':
                    d.clean()
                    d.git('fetch', '--no-tags', d.c['remote'], 'refs/heads/' + d.c['branch'] + ':refs/remotes/' + d.c['remote'] + '/' + d.c['branch'])
                else:
                    require(args.approve and args.state, 'approval and state required')
                    if args.action == 'apply':
                        require(args.plan, 'plan required')
                        plan = json.loads(args.plan.read_text(encoding='utf-8-sig'))
                        require(plan['config'] == d.c, 'config mismatch')
                        d.apply(plan, args.approve, args.state)
                    else:
                        saved = json.loads(args.state.read_text(encoding='utf-8-sig'))
                        require(saved['plan']['config'] == d.c, 'config mismatch')
                        d.rollback(saved, args.approve)
            print('OK')
        return 0
    except Stop as error:
        print('STOP: ' + str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        # Do not expose secret values/paths from exception strings.
        print('STOP: safety check or command failed; private state may require review', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
