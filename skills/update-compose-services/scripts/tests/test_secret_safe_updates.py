"""Portable real-Git / mocked-Docker regression tests; never contact a daemon."""
import copy
import contextlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'update_compose_services.py'
spec = importlib.util.spec_from_file_location('safe_updates', SCRIPT)
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


class SecretSafeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='safe-update-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.git('remote', 'add', 'origin', str(self.root / 'remote'))
        (self.repo / 'Dockerfile').write_text('FROM scratch\n', encoding='utf-8')
        (self.repo / 'compose.yaml').write_text('services: {}\n', encoding='utf-8')
        (self.repo / 'app.py').write_text('old\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-m', 'base')
        self.base = self.git('rev-parse', 'HEAD')
        (self.repo / 'app.py').write_text('new\n', encoding='utf-8')
        self.git('commit', '-am', 'update')
        self.target = self.git('rev-parse', 'HEAD')
        self.git('update-ref', 'refs/remotes/origin/main', self.target)
        self.git('checkout', self.base, '--detach')
        self.git('branch', '-f', 'main', self.base)
        self.git('checkout', 'main')
        self.env = self.root / 'private.env'
        self.env.write_text('SECRET=must-not-be-read\n', encoding='utf-8')
        self.config = dict(repo=str(self.repo), remote='origin', remote_url=str(self.root / 'remote'),
                           branch='main', context='test', project='demo', compose=['compose.yaml'],
                           env_file=str(self.env), services=['app'], source_paths=['app.py'],
                           code_reviewed_no_migrations=True, rollback_allowed=True, target_sha=self.target)
        self.model = {'services': {'app': {'build': {'context': str(self.repo)}, 'read_only': True,
                                          'tmpfs': ['/tmp'], 'environment': {'SECRET': '${SECRET:?required}'}},
                                   'proxy': {'image': 'proxy:v1', 'read_only': True,
                                             'volumes': [{'type': 'bind', 'source': '/var/run/docker.sock', 'target': '/var/run/docker.sock', 'read_only': True}]},
                                   'certgen': {'build': {'context': str(self.repo)}, 'restart': 'no'}}}
        self.rows = {}
        for name in self.model['services']:
            self.rows[name] = dict(id=name + '-old', image='sha256:' + name + '-old',
                                   image_tag='proxy:v1' if name == 'proxy' else 'demo-' + name,
                                   status='exited' if name == 'certgen' else 'running',
                                   health='none', restarts=0, readonly=True, tmpfs={}, mounts=[], ports={}, network_mode='demo_net',
                                   service=name, **{'config-hash': name + '-hash', 'project.working_dir': str(self.repo),
                                                  'project.config_files': str(self.repo / 'compose.yaml'), 'oneoff': 'False'})
        self.commands = []
        self.fail_build = False
        self.rollback = False
        self.d = u.Deployment(self.config)
        self.d.docker = self.docker

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, stderr=subprocess.DEVNULL, text=True).strip()

    def docker(self, *args):
        self.commands.append(args)
        if args[:2] == ('ps', '-aq'):
            return ' '.join(self.rows)
        if args[0] == 'inspect':
            self.assertEqual(args[1:4], ('--type', 'container', '--format'))
            template = args[4]
            self.assertNotIn('.Config.Env', template)
            self.assertNotIn('{{json .Config}}', template)
            self.assertNotIn('.State.Health.Log', template)
            self.assertIn('(index .State "Health")', template)
            self.assertIn('(index .HostConfig "Tmpfs")', template)
            return '\n'.join(json.dumps(r) for r in self.rows.values())
        if args[:2] == ('image', 'tag'):
            if args[-1] == 'demo-app': self.rollback = True
            return ''
        if args[:2] == ('image', 'inspect'):
            return 'sha256:app-new'
        self.assertEqual(args[0], 'compose')
        if 'config' in args:
            self.assertIn('--no-interpolate', args)
            self.assertIn('--no-env-resolution', args)
            self.assertIn('--no-normalize', args)
            self.assertIn('--no-path-resolution', args)
            self.assertNotIn('--hash', args)
            empty = Path(args[args.index('--env-file') + 1])
            self.assertNotEqual(empty, self.env)
            self.assertEqual(empty.read_bytes(), b'')
            return json.dumps(self.model)
        self.assertEqual(args[args.index('--env-file') + 1], str(self.env))
        if 'build' in args:
            if self.fail_build: raise u.Stop('fake build failure')
            self.assertEqual(args[-1], 'app')
            return ''
        if 'up' in args:
            self.assertEqual(args[-1], 'app')
            self.assertTrue({'--no-deps', '--no-build', '--pull', 'never', '--force-recreate', '--wait'} <= set(args))
            self.rows['app']['id'] = 'app-restored' if self.rollback else 'app-new'
            self.rows['app']['image'] = 'sha256:app-old' if self.rollback else 'sha256:app-new'
            return ''
        self.fail('unexpected daemon command')

    @contextlib.contextmanager
    def secret_guard(self):
        read_bytes = Path.read_bytes
        read_text = Path.read_text
        def guarded_bytes(path):
            if path == self.env: self.fail('read actual env bytes')
            return read_bytes(path)
        def guarded_text(path, *args, **kwargs):
            if path == self.env: self.fail('read actual env text')
            return read_text(path, *args, **kwargs)
        with patch.object(Path, 'read_bytes', guarded_bytes), patch.object(Path, 'read_text', guarded_text):
            yield

    def inspect_without_secret_access(self):
        with self.secret_guard():
            return self.d.inspect()

    def test_inspect_no_secret_access_and_no_mutation(self):
        before = copy.deepcopy(self.rows)
        plan = self.inspect_without_secret_access()
        self.assertEqual(plan['target'], self.target)
        self.assertEqual(plan['image_tags'], {'app': 'demo-app'})
        self.assertEqual(self.rows, before)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)
        self.assertNotIn('must-not-be-read', json.dumps(plan))
        self.assertFalse(any('build' in a or 'up' in a for a in self.commands))

    def test_selective_apply_and_rollback_preserve_exited_non_target(self):
        plan = self.inspect_without_secret_access()
        before = copy.deepcopy(self.rows)
        with self.secret_guard(), patch.object(u.time, 'sleep'):
            self.d.apply(plan, u.digest(plan), self.root / 'state.json')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.target)
        self.assertEqual(self.rows['proxy'], before['proxy'])
        self.assertEqual(self.rows['certgen'], before['certgen'])
        saved = json.loads((self.root / 'state.json').read_text())
        self.assertEqual(saved['phase'], 'complete')
        with self.secret_guard():
            self.d.rollback(saved, u.digest(plan))
        self.assertEqual(self.rows['app']['image'], before['app']['image'])
        self.assertEqual(self.rows['certgen'], before['certgen'])

    def test_target_bind_rejected_while_non_target_socket_preserved(self):
        self.d.inspect()
        self.model['services']['app']['volumes'] = copy.deepcopy(self.model['services']['proxy']['volumes'])
        with self.assertRaisesRegex(u.Stop, 'target bind'): self.d.inspect()

    def test_raw_named_volumes_and_relative_context_preserved(self):
        self.model['services']['app']['build']['context'] = '.'
        self.model['services']['app']['volumes'] = ['data:/data', 'certs:/certs:ro']
        self.d.inspect()
        for value in ('/host:/data:ro', 'C:/host:/data', '../code:/app', '${HOST}:/data', '/anonymous'):
            with self.subTest(value=value):
                self.model['services']['app']['volumes'] = [value]
                with self.assertRaisesRegex(u.Stop, 'target bind'): self.d.inspect()

    def test_target_stopped_or_unhealthy_rejected(self):
        for key, value in (('status', 'exited'), ('health', 'unhealthy')):
            with self.subTest(key=key):
                old = self.rows['app'][key]
                self.rows['app'][key] = value
                with self.assertRaises(u.Stop): self.d.inspect()
                self.rows['app'][key] = old

    def test_exited_non_target_drift_rejected_before_build(self):
        plan = self.d.inspect()
        self.rows['certgen']['status'] = 'running'
        with self.assertRaisesRegex(u.Stop, 'plan changed'):
            self.d.apply(plan, u.digest(plan), self.root / 'state.json')
        self.assertFalse(any('build' in a or 'up' in a for a in self.commands))

    def test_exact_sha_pin_rejects_new_remote(self):
        self.config['target_sha'] = 'f' * 40
        with self.assertRaisesRegex(u.Stop, 'pinned target'): self.d.inspect()

    def test_env_metadata_change_rejects_apply(self):
        plan = self.d.inspect()
        self.env.write_text('changed-length\n', encoding='utf-8')
        with self.assertRaisesRegex(u.Stop, 'plan changed'):
            self.d.apply(plan, u.digest(plan), self.root / 'state.json')

    def test_service_env_file_metadata_and_no_resolution(self):
        self.model['services']['app']['env_file'] = [{'path': str(self.env), 'required': True}]
        plan = self.inspect_without_secret_access()
        self.assertEqual(len(plan['env_metadata']), 1)

    def test_build_failure_never_recreates(self):
        plan = self.d.inspect()
        self.fail_build = True
        with self.assertRaisesRegex(u.Stop, 'fake build'):
            self.d.apply(plan, u.digest(plan), self.root / 'state.json')
        self.assertFalse(any('up' in a for a in self.commands))
        self.assertEqual(self.rows['app']['id'], 'app-old')

    def test_dirty_worktree_and_wrong_image_tag_rejected(self):
        (self.repo / 'untracked').write_text('keep')
        with self.assertRaisesRegex(u.Stop, 'dirty'): self.d.inspect()
        (self.repo / 'untracked').unlink()
        self.rows['app']['image_tag'] = 'foreign:tag'
        with self.assertRaisesRegex(u.Stop, 'image tag'): self.d.inspect()

    def test_privilege_and_unknown_keys_still_rejected(self):
        self.model['services']['app']['privileged'] = True
        with self.assertRaisesRegex(u.Stop, 'unsupported service'): self.d.inspect()

    def test_target_and_non_target_shared_image_rejected(self):
        self.rows['proxy']['image_tag'] = 'demo-app:latest'
        with self.assertRaisesRegex(u.Stop, 'used by non-target'): self.d.inspect()

    def test_runtime_readonly_and_config_hash_drift_rejected(self):
        plan = self.d.inspect()
        for key, value in (('readonly', False), ('config-hash', 'other')):
            with self.subTest(key=key):
                original = self.rows['app'][key]
                self.rows['app'][key] = value
                with self.assertRaisesRegex(u.Stop, 'runtime configuration'):
                    self.d.verify_state(plan)
                self.rows['app'][key] = original

    def test_variable_dockerfile_is_rejected_before_path_access(self):
        self.model['services']['app']['build']['dockerfile'] = '$DOCKERFILE'
        (self.repo / '$DOCKERFILE').write_text('FROM scratch\n')
        # model validation itself, independent of clean() rejecting that test file.
        with self.assertRaisesRegex(u.Stop, 'variable Dockerfile'): self.d.model()

    def test_docker_hub_tag_aliases_are_identical(self):
        self.assertEqual(u.image_key('app'), u.image_key('docker.io/library/app:latest'))
        self.assertEqual(u.image_key('index.docker.io/library/app'), u.image_key('app'))
        self.assertNotEqual(u.image_key('localhost:5000/app'), u.image_key('app'))
        self.rows['proxy']['image_tag'] = 'docker.io/library/demo-app:latest'
        with self.assertRaisesRegex(u.Stop, 'used by non-target'): self.d.inspect()

    def test_stale_rebase_head_alone_passes_without_modification(self):
        marker = Path(self.git('rev-parse', '--absolute-git-dir')) / 'REBASE_HEAD'
        marker.write_text(self.base + '\n', encoding='utf-8')
        before = marker.stat()
        plan = self.d.inspect()
        self.assertEqual(plan['head'], self.base)
        self.assertEqual(marker.read_text(encoding='utf-8'), self.base + '\n')
        self.assertEqual(marker.stat().st_mtime_ns, before.st_mtime_ns)

    def test_active_rebase_directories_fail_closed(self):
        for name in ('rebase-merge', 'rebase-apply'):
            with self.subTest(name=name):
                marker = Path(self.git('rev-parse', '--absolute-git-dir')) / name
                marker.mkdir()
                try:
                    with self.assertRaises(u.Stop): self.d.clean()
                    self.assertTrue(marker.is_dir())
                finally:
                    marker.rmdir()

    def test_other_active_operation_markers_still_stop(self):
        for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'sequencer'):
            with self.subTest(name=name):
                marker = Path(self.git('rev-parse', '--absolute-git-dir')) / name
                marker.write_text(self.base + '\n', encoding='utf-8')
                try:
                    with self.assertRaises(u.Stop): self.d.clean()
                    self.assertTrue(marker.exists())
                finally:
                    marker.unlink()


if __name__ == '__main__':
    unittest.main()
