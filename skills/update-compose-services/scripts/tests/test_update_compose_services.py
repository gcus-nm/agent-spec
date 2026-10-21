import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'update_compose_services.py'
spec = importlib.util.spec_from_file_location('updates', SCRIPT)
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


@unittest.skipIf(os.name == 'nt', 'POSIX fake-executable integration; use WindowsCompatibilityTests on Windows')
class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='更新 空白 ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / '日本語 repo'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.git('remote', 'add', 'origin', str(self.root / 'remote'))
        (self.repo / 'Dockerfile').write_text('FROM scratch\n', encoding='utf-8')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/app.py').write_text('old')
        (self.repo / 'compose.yaml').write_text('services:\n  app:\n    image: app:local\n')
        self.git('add', '.')
        self.git('commit', '-m', 'base')
        self.base = self.git('rev-parse', 'HEAD')
        (self.repo / 'src/app.py').write_text('new')
        self.git('commit', '-am', 'update')
        self.target = self.git('rev-parse', 'HEAD')
        self.git('update-ref', 'refs/remotes/origin/main', self.target)
        self.git('checkout', '-B', 'main', self.base)
        self.env = self.root / 'private-env'
        self.env.write_text('SECRET=do-not-print-this\n')
        self.config = dict(repo=str(self.repo), remote='origin', remote_url=str(self.root / 'remote'), branch='main',
                           context='test', project='test', compose=['compose.yaml'], env_file=str(self.env),
                           services=['app'], source_paths=['src'], code_reviewed_no_migrations=True, rollback_allowed=True, target_sha=self.target)
        self.model = {'services': {'app': {'image': 'app:local', 'build': {'context': str(self.repo)}},
                                   'db': {'image': 'db:local'}}}
        self.rows = {n: {'Id': n + '-old', 'Image': 'sha256:' + n + '-old', 'Config': {'Labels': {
            'com.docker.compose.service': n, 'com.docker.compose.config-hash': n+'-hash', 'com.docker.compose.project.working_dir': str(self.repo),
            'com.docker.compose.project.config_files': str(self.repo / 'compose.yaml')}}, 'State': {'Status': 'running'}, 'RestartCount': 0} for n in ('app', 'db')}
        self.commands = []
        self.fail_build = False
        self.health_fail = False
        # Fake Docker executable uses persisted state, argv and captured output like the real CLI.
        fake = self.root / 'docker'
        fake.write_text('''#!/usr/bin/env python3
import json,sys,pathlib
root=pathlib.Path(__file__).parent
s=json.loads((root/'docker-state').read_text())
a=sys.argv[3:]
with (root/'commands').open('a') as f: f.write(json.dumps(a)+'\\n')
if a[:2]==['ps','-aq']: print('app db')
elif a[0]=='inspect':
 assert '--format' in a and '.Config.Env' not in a[a.index('--format')+1]
 for n,r in s['rows'].items():
  l=r['Config']['Labels']
  print(json.dumps(dict(id=r['Id'],image=r['Image'],image_tag=n+':local',status=r['State']['Status'],health=r['State'].get('Health',{}).get('Status','none'),restarts=r['RestartCount'],**{k:l.get('com.docker.compose.'+k) for k in ('service','config-hash','project.working_dir','project.config_files','oneoff')})))
elif a[:2]==['image','inspect']: print('sha256:app-new')
elif a[:2]==['image','tag']:
 if a[-1]=='app:local':
  s['rollback']=True;(root/'docker-state').write_text(json.dumps(s))
elif 'config' in a and '--hash' in a: print('app app-hash\\n'+'db db-hash')
elif 'config' in a: print(json.dumps(s['model']))
elif 'build' in a:
 if s['fail_build']: print('do-not-print-this',file=sys.stderr);sys.exit(1)
elif 'up' in a:
 r=s['rows']['app'];r['Id']='app-new';r['Image']='sha256:app-new'
 if s.get('rollback'): r['Image']='sha256:app-old'
 if s['health_fail']: r['State']['Health']={'Status':'unhealthy'}
 (root/'docker-state').write_text(json.dumps(s))
else: sys.exit(9)
''')
        fake.chmod(0o700)
        self.path = patch.dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ['PATH'])
        self.path.start()
        self.addCleanup(self.path.stop)
        self.save()
        self.d = u.Deployment(self.config)

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, stderr=subprocess.DEVNULL, text=True).strip()

    def save(self):
        (self.root / 'docker-state').write_text(json.dumps(dict(model=self.model, rows=self.rows, fail_build=self.fail_build, health_fail=self.health_fail)))

    def log(self):
        return [json.loads(x) for x in (self.root / 'commands').read_text().splitlines()]

    def apply(self, plan):
        self.d.apply(plan, u.digest(plan), self.root / 'state')

    def test_success_and_rollback(self):
        plan = self.d.inspect()
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)
        self.apply(plan)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.target)
        self.d.rollback(json.loads((self.root / 'state').read_text()), u.digest(plan))
        log = self.log()
        for a in log:
            self.assertFalse(set(a) & {'down', 'prune', 'reset', 'clean', 'stash'})
            if 'up' in a:
                self.assertEqual(a[-1], 'app')
                self.assertTrue({'--no-deps', '--no-build', '--pull', 'never'} <= set(a))
        self.assertNotIn('do-not-print-this', (self.root / 'state').read_text())

    def test_dirty_untracked(self):
        for path in ('src/app.py', 'new'):
            with self.subTest(path=path):
                p = self.repo / path
                original = p.read_text() if p.exists() else None
                p.write_text('dirty')
                with self.assertRaises(u.Stop): self.d.inspect()
                if original is None: p.unlink()
                else: p.write_text(original)

    def test_divergence(self):
        (self.repo / 'src/app.py').write_text('local')
        self.git('commit', '-am', 'diverge')
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_wrong_branch(self):
        self.git('checkout', '-b', 'unexpected')
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_git_operation(self):
        (self.repo / '.git/MERGE_HEAD').write_text(self.target)
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_empty_allowlist(self):
        self.config['services'] = []
        with self.assertRaises(u.Stop): u.Deployment(self.config)

    def test_wrong_service(self):
        self.config['services'] = ['missing']
        with self.assertRaises(u.Stop): u.Deployment(self.config).inspect()

    def test_changed_plan(self):
        plan = self.d.inspect()
        self.env.write_text('changed')
        with self.assertRaises(u.Stop): self.apply(plan)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)

    def test_changed_refs(self):
        plan = self.d.inspect()
        self.git('update-ref', 'refs/remotes/origin/main', self.base)
        with self.assertRaises(u.Stop): self.apply(plan)

    def test_build_failure_no_recreate(self):
        plan = self.d.inspect()
        self.fail_build = True
        self.save()
        with self.assertRaises(u.Stop): self.apply(plan)
        self.assertFalse(any('up' in a for a in self.log()))

    def test_unhealthy(self):
        plan = self.d.inspect()
        self.health_fail = True
        self.save()
        with self.assertRaises(u.Stop): self.apply(plan)

    def test_non_target_changed(self):
        plan = self.d.inspect()
        self.rows['db']['Id'] = 'foreign'
        self.save()
        with self.assertRaises(u.Stop): self.apply(plan)
        self.assertFalse(any('build' in a for a in self.log()))

    def test_double_start(self):
        with u.locked(self.d):
            with self.assertRaises(u.Stop):
                with u.locked(self.d): pass

    def test_shared_tag_and_bind_mount(self):
        self.model['services']['db']['image'] = 'app:local'
        self.save()
        with self.assertRaises(u.Stop): self.d.inspect()
        self.model['services']['db']['image'] = 'db:local'
        self.model['services']['app']['volumes'] = [{'type': 'bind', 'source': str(self.repo), 'target': '/app'}]
        self.save()
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_project_provenance(self):
        self.rows['app']['Config']['Labels']['com.docker.compose.project.working_dir'] = '/different'
        self.save()
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_compose_change(self):
        self.git('checkout', '-B', 'candidate', self.target)
        (self.repo / 'compose.yaml').write_text('services: {}')
        self.git('commit', '-am', 'config change')
        self.git('update-ref', 'refs/remotes/origin/main', self.git('rev-parse', 'HEAD'))
        self.git('checkout', 'main')
        self.config['source_paths'].append('compose.yaml')
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_approval_and_rollback_denial(self):
        plan = self.d.inspect()
        with self.assertRaises(u.Stop): self.d.apply(plan, 'wrong', self.root / 'state')
        self.assertFalse((self.root / 'state').exists())
        self.config['rollback_allowed'] = False
        with self.assertRaises(u.Stop): self.d.rollback({'plan': plan}, u.digest(plan))

    def test_profile_and_privilege_rejected(self):
        self.model['services']['app']['privileged'] = True
        self.save()
        with self.assertRaises(u.Stop): self.d.inspect()
        del self.model['services']['app']['privileged']
        self.save()
        (self.repo / 'compose.yaml').write_text('services: {}\ninclude: other.yaml\n')
        self.git('commit', '-am', 'unsupported include')
        self.git('update-ref', 'refs/remotes/origin/main', self.git('rev-parse', 'HEAD'))
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_candidate_symlink_rejected(self):
        self.git('checkout', '-B', 'candidate', self.target)
        (self.repo / 'src/link').symlink_to('/outside')
        self.git('add', 'src/link')
        self.git('commit', '-m', 'symlink')
        self.git('update-ref', 'refs/remotes/origin/main', self.git('rev-parse', 'HEAD'))
        self.git('checkout', 'main')
        with self.assertRaises(u.Stop): self.d.inspect()

    def test_running_configuration_changed_after_plan(self):
        plan = self.d.inspect()
        self.rows['app']['Config']['Labels']['com.docker.compose.config-hash'] = 'changed'
        self.save()
        with self.assertRaises(u.Stop): self.apply(plan)

    def test_external_dockerfile_rejected(self):
        for value in ('../outside/Dockerfile', '/outside/Dockerfile', 'C:/outside/Dockerfile'):
            with self.subTest(value=value):
                self.model['services']['app']['build']['dockerfile'] = value
                self.save()
                with self.assertRaises(u.Stop): self.d.inspect()

    def test_private_state_symlink_rejected_without_touching_target(self):
        original = self.root / 'original'
        original.write_text('keep')
        link = self.root / 'link'
        link.symlink_to(original)
        with self.assertRaises(u.Stop): u.write_private(link, {'new': True}, replace=True)
        self.assertEqual(original.read_text(), 'keep')

    def test_secret_output_suppressed(self):
        config = self.root / 'config.json'
        config.write_text(json.dumps(self.config))
        self.fail_build = True
        self.save()
        plan = self.root / 'plan'
        result = subprocess.run([sys.executable, str(SCRIPT), 'inspect', '--config', str(config), '--plan', str(plan)], capture_output=True, text=True)
        approval = json.loads(result.stdout)['approval']
        result = subprocess.run([sys.executable, str(SCRIPT), 'apply', '--config', str(config), '--plan', str(plan), '--state', str(self.root / 'state'), '--approve', approval], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('do-not-print-this', result.stdout + result.stderr + plan.read_text())


class WindowsCompatibilityTests(unittest.TestCase):
    """Run Windows-specific branches with stdlib mocks; no Windows host/service access."""

    def test_windows_drive_unc_and_separator_normalization(self):
        self.assertEqual(u.path_key('C:/Users/Owner/日本語 repo', windows=True),
                         u.path_key('c:\\Users\\Owner\\日本語 repo\\', windows=True))
        self.assertEqual(u.path_key('//server/share/日本語 repo', windows=True),
                         u.path_key('\\\\SERVER\\share\\日本語 repo', windows=True))
        for value in ('C:relative', '\\root-only', 'relative', ''):
            with self.subTest(value=value), self.assertRaises(u.Stop):
                u.path_key(value, windows=True)
        self.assertNotEqual(u.path_key('C:/project', windows=True), u.path_key('D:/project', windows=True))
        self.assertNotEqual(u.path_key('/Repo', windows=False), u.path_key('/repo', windows=False))

    def test_portable_source_paths_reject_windows_escapes(self):
        for value in ('C:/absolute', 'C:relative', '//server/share', '\\root', '..', 'src/../secret',
                      'src\\..\\secret', 'src:stream', './src', 'src//app'):
            with self.subTest(value=value), self.assertRaises(u.Stop):
                u.relative_source(value)
        self.assertEqual(u.relative_source('src/日本語 file.py'), 'src/日本語 file.py')

    def fake_msvcrt(self):
        import types
        calls = []
        held = set()

        def locking(fd, mode, size):
            self.assertEqual(os.lseek(fd, 0, os.SEEK_CUR), 0)
            self.assertEqual(size, 1)
            inode = os.fstat(fd).st_ino
            calls.append(mode)
            if mode == 2:
                if inode in held:
                    raise OSError('locked')
                held.add(inode)
            elif mode == 0:
                held.remove(inode)
            else:
                self.fail('blocking/unknown Windows lock requested')

        return types.SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0, locking=locking), calls

    def test_windows_lock_busy_release_and_reuse(self):
        api, calls = self.fake_msvcrt()
        with tempfile.TemporaryDirectory(prefix='ロック 空白 ') as folder:
            p = Path(folder) / 'update.lock'
            with patch.dict(sys.modules, msvcrt=api):
                with u.file_lock(p, windows=True):
                    with self.assertRaises(u.Stop):
                        with u.file_lock(p, windows=True): self.fail('double entry')
                with u.file_lock(p, windows=True): pass
            self.assertTrue(p.exists())  # Never unlink a lock another process may already hold.
            self.assertEqual(calls, [2, 2, 0, 2, 0])

    def test_windows_lock_released_on_body_failure(self):
        api, calls = self.fake_msvcrt()
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, msvcrt=api):
            p = Path(folder) / 'lock'
            with self.assertRaises(RuntimeError):
                with u.file_lock(p, windows=True): raise RuntimeError('body')
            with u.file_lock(p, windows=True): pass
        self.assertEqual(calls, [2, 0, 2, 0])

    def test_windows_lock_failure_does_not_unlock_unowned_region(self):
        from unittest.mock import Mock
        api = Mock(LK_NBLCK=2, LK_UNLCK=0)
        api.locking.side_effect = OSError('access denied')
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, msvcrt=api):
            with self.assertRaises(u.Stop):
                with u.file_lock(Path(folder) / 'lock', windows=True): self.fail('entered')
        self.assertEqual(api.locking.call_count, 1)

    def test_constructor_rejects_drive_relative_before_filesystem_access(self):
        config = dict(repo='C:relative', remote='origin', remote_url='https://example.invalid/repo', branch='main',
                      context='local', project='app', compose=['compose.yaml'], env_file='C:/private/env',
                      services=['app'], source_paths=['src'], code_reviewed_no_migrations=True, rollback_allowed=False, target_sha='a'*40)
        original_key = u.path_key
        with patch.object(u, 'path_key', side_effect=lambda p: original_key(p, windows=True)):
            with patch.object(u, 'Path') as paths:
                with self.assertRaises(u.Stop): u.Deployment(config)
                paths.assert_not_called()

    def test_windows_argv_and_case_insensitive_environment_filter(self):
        from unittest.mock import Mock
        argv = ['docker.exe', '--context', 'local', 'compose', '-f', 'C:\\日本語 repo\\compose.yaml']
        with patch.object(u.subprocess, 'run', return_value=Mock(returncode=0, stdout='日本語\n')) as call:
            with patch.dict(os.environ, {'Compose_Profiles': 'dangerous', 'COMPOSE_FILE': 'other', 'SystemRoot': 'test-root'}):
                self.assertEqual(u.run(argv, 'C:\\日本語 repo'), '日本語')
        args, kwargs = call.call_args
        self.assertEqual(args[0], argv)
        self.assertFalse(kwargs['shell'])
        self.assertEqual(kwargs['encoding'], 'utf-8')
        self.assertEqual(kwargs['cwd'], 'C:\\日本語 repo')
        self.assertFalse(any(k.upper().startswith('COMPOSE_') for k in kwargs['env']))
        self.assertEqual({k.upper(): v for k, v in kwargs['env'].items()}['SYSTEMROOT'], 'test-root')

    def test_atomic_state_replace_closes_file_before_rename(self):
        original_replace = os.replace
        seen = []

        def replace_file(source, target):
            # Windows forbids replacing an open temporary; verify it can be reopened.
            with open(source, 'r+b') as stream:
                seen.append(json.load(stream))
            original_replace(source, target)

        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / '状態.json'
            u.write_private(state, {'phase': 'started'})
            with patch.object(u.os, 'replace', side_effect=replace_file):
                u.write_private(state, {'phase': 'complete'}, replace=True)
            self.assertEqual(json.loads(state.read_text(encoding='utf-8')), {'phase': 'complete'})
            self.assertEqual(seen, [{'phase': 'complete'}])
            self.assertEqual(list(Path(folder).iterdir()), [state])

    def test_powershell_bom_json_and_utf8_private_output(self):
        import io
        from unittest.mock import Mock
        config = {'services': ['app'], 'repo': 'C:/日本語 repo'}
        plan = {'head': 'a'*40, 'target': 'b'*40, 'changed_paths': ['src/日本語.py']}
        fake = Mock(c=config)
        fake.inspect.return_value = plan
        with tempfile.TemporaryDirectory() as folder:
            config_path = Path(folder) / '設定.json'
            output = Path(folder) / '計画.json'
            config_path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8-sig')
            with patch.object(u, 'Deployment', return_value=fake) as constructor:
                with patch.object(sys, 'argv', ['update', 'inspect', '--config', str(config_path), '--plan', str(output)]):
                    with patch.object(sys, 'stdout', io.StringIO()): self.assertEqual(u.main(), 0)
            constructor.assert_called_once_with(config)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8')), plan)


if __name__ == '__main__':
    unittest.main()
