import pathlib
import shutil
import tempfile
import unittest

from generator.project import Project


def strip_indent(raw):
    return raw.replace('\n' + ' ' * 12, '\n').lstrip('\n')


class GenericProject(Project):
    language = 'LANGUAGE'

    @classmethod
    def register(cls):
        Project._languages[cls.language] = cls

    @classmethod
    def deregister(cls):
        del Project._languages[cls.language]


class TestProject(unittest.TestCase):
    def setUp(self):
        self.project_path = pathlib.Path(tempfile.mkdtemp())
        self.templates_path = pathlib.Path(tempfile.mkdtemp())
        GenericProject.register()

    def tearDown(self):
        shutil.rmtree(self.project_path)
        shutil.rmtree(self.templates_path)
        GenericProject.deregister()

    def test_simple_access(self):
        project = Project(
            name='NAME',
            path=self.project_path,
            arg='VAL',
        )

        self.assertIn('arg', project)
        self.assertNotIn('other_arg', project)

        self.assertEqual(project['arg'], 'VAL')
        self.assertFalse(project._changed)

        project['arg'] = 'VAL'
        self.assertFalse(project._changed)

        project['arg'] = 'OTHER_VAL'
        self.assertEqual(project['arg'], 'OTHER_VAL')
        self.assertTrue(project._changed)

    def test_write(self):
        project = Project(
            name='NAME',
            path=self.project_path,
            dry_run=False,
        )
        target = self.project_path / 'dummy.txt'
        actual = project._write(target, 'DATA')
        self.assertEqual(actual, len('DATA'))
        self.assertEqual(target.read_text(), 'DATA')

    def test_write_create_parent_dir(self):
        project = Project(
            name='NAME',
            path=self.project_path,
            dry_run=False,
        )
        target = self.project_path / 'dir' / 'nested_dir' / 'dummy.txt'
        self.assertFalse(target.exists())
        self.assertFalse(target.parent.exists())
        self.assertFalse(target.parent.parent.exists())

        project._write(target, 'DATA')

        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), 'DATA')

    def test_write_dry_run(self):
        project = Project(
            name='NAME',
            path=self.project_path,
            dry_run=True,
        )
        target = self.project_path / 'dummy.txt'
        actual = project._write(target, 'DATA')
        self.assertEqual(actual, 0)
        self.assertFalse(target.exists())

    def test_write_dry_run_skip_create_parent_dir(self):
        project = Project(
            name='NAME',
            path=self.project_path,
            dry_run=True,
        )
        target = self.project_path / 'dir' / 'nested_dir' / 'dummy.txt'

        project._write(target, 'DATA')

        self.assertFalse(target.exists())
        self.assertFalse(target.parent.exists())
        self.assertFalse(target.parent.parent.exists())

    def test_parser(self):
        project_in = strip_indent(
            """
            NAME
            --arg=val
            --other-arg=other_val
            --multi-val=one,two
            """
        )

        actual = Project._parse_cfg(project_in)
        expected = {
            'name': 'NAME',
            'arg': 'val',
            'other_arg': 'other_val',
            'multi_val': [
                'one',
                'two',
            ],
        }

        self.assertDictEqual(actual, expected)

    def test_parser_scrambled(self):
        project_in = strip_indent(
            """
            --arg=val
            NAME
            """
        )

        actual = Project._parse_cfg(project_in)
        expected = {
            'name': 'NAME',
            'arg': 'val',
        }

        self.assertDictEqual(actual, expected)

    def test_keep_scrambled(self):
        project_in = strip_indent(
            """
            --language=LANGUAGE
            NAME
            --arg=val
            """
        )

        Project.get_cfg_path(self.project_path).write_text(project_in)

        project = Project.from_path(self.project_path)

        # some deployed file changed
        project._changed = True

        actual = Project.get_cfg_path(self.project_path).read_text()
        self.assertFalse(project._dump_cfg())
        self.assertEqual(actual, project_in)

    def test_init(self):
        project_in = strip_indent(
            """
            NAME
            --language=LANGUAGE
            --node-version=1.2.3
            --acceptance-creds=None
            --dependencies=mongo,redis
            --docker-repos=example.com/images
            --unknown-arg=VALUE
            """
        )
        Project.get_cfg_path(self.project_path).write_text(project_in)

        actual = Project.from_path(self.project_path)
        expected = GenericProject(
            name='NAME',
            path=self.project_path,
            node_version='1.2.3',
            acceptance_creds=None,
            dependencies=[
                'mongo',
                'redis',
            ],
            docker_repos='example.com/images',
            unknown_arg='VALUE',
        )

        self.assertEqual(actual, expected)

    def test_serialize(self):
        expected = strip_indent(
            """
            NAME
            --language=LANGUAGE
            --acceptance-creds=None
            --dependencies=mongo,redis
            --docker-repos=example.com/images
            --node-version=1.2.3
            """
        )
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            node_version='1.2.3',
            acceptance_creds=None,
            dependencies=[
                'mongo',
                'redis',
            ],
            docker_repos='example.com/images'
        )
        actual = project._serialize_cfg()

        self.assertEqual(actual, expected)

    def test_serialize_unknown(self):
        expected = strip_indent(
            """
            NAME
            --language=LANGUAGE
            --acceptance-creds=None
            --dependencies=mongo,redis
            --docker-repos=example.com/images
            --node-version=1.2.3
            --unknown-arg=VALUE
            """
        )
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            node_version='1.2.3',
            acceptance_creds=None,
            dependencies=[
                'mongo',
                'redis',
            ],
            docker_repos='example.com/images',
            unknown_arg='VALUE',
        )
        actual = project._serialize_cfg()

        self.assertEqual(actual, expected)

    def test_serialize_sequence(self):
        expected = strip_indent(
            """
            NAME
            --language=LANGUAGE
            --other-arg=1
            --unknown-arg=VALUE
            --script-version=3.2.1
            """
        )
        project_1 = GenericProject(
            name='NAME',
            path=self.project_path,
            script_version='3.2.1',
            unknown_arg='VALUE',
            other_arg='1',
        )
        project_2 = GenericProject(
            name='NAME',
            path=self.project_path,
            unknown_arg='VALUE',
            other_arg='1',
            script_version='3.2.1',
        )
        actual_1 = project_1._serialize_cfg()
        actual_2 = project_2._serialize_cfg()

        self.assertEqual(actual_1, expected)
        self.assertEqual(actual_2, expected)

    def test_env(self):
        project = GenericProject(
            name='NAME',
            path=self.project_path,
        )
        env = project._get_env()
        self.assertFalse(env['has_install_deps'])

        (self.project_path / 'install_deps.sh').touch()
        env = project._get_env()
        self.assertTrue(env['has_install_deps'])

    def test_get_template_path_preference(self):
        templates = self.templates_path
        file = 'dummy.j2'
        script_version = '1.2.3'
        name = 'NAME'
        project = GenericProject(
            name=name,
            path=self.project_path,
            templates=templates,
            script_version=script_version,
        )
        language = project.language

        preference = [
            ('VERSION_NAME', [script_version, name]),
            ('NAME', [name]),
            ('VERSION_LANG', [script_version, language]),
            ('LANG', [language]),
            ('VERSION', [script_version]),
            ('GLOBAL', []),
        ]

        for content, path_parts in preference:
            path = templates
            for part in path_parts:
                path = path / '_' / part

            path.mkdir(parents=True, exist_ok=True)
            (path / file).write_text(content)

        for content, _ in preference:
            template = project._get_template(
                name='dummy',
            )
            path = pathlib.Path(template.filename)
            self.assertEqual(path.read_text(), content)
            path.unlink()

    def test_update_file(self):
        templates = self.templates_path
        target = self.project_path / 'dummy'
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            templates=templates,
        )
        (templates / 'dummy.j2').write_text(
            'THE {{ var }}'
        )

        project._update_file(
            name='dummy',
            env={'var': 'CONTENT'},
        )
        self.assertEqual(target.read_text(), 'THE CONTENT')

    def test_delete_orphan(self):
        class DemoProject(GenericProject):
            def _get_files_to_update(self):
                if self['script_version'] == '0.0.0':
                    return ['old']
                return ['new']

        templates = self.templates_path
        (templates / 'old.j2').touch()
        (templates / 'new.j2').touch()

        project = DemoProject(
            name='NAME',
            path=self.project_path,
            templates=templates,
            script_version='0.0.0',
            update=True,
        )
        (self.project_path / 'old').touch()

        self.assertTrue((self.project_path / 'old').exists())
        project._delete_orphan_files()
        self.assertFalse((self.project_path / 'old').exists())

    def test_process(self):
        class DemoProject(GenericProject):
            def _get_files_to_update(self):
                return ['dummy']

        target = self.project_path / 'dummy'
        cfg_expected = strip_indent(
            """
            NAME
            --language=LANGUAGE
            """
        )
        templates = self.templates_path
        project = DemoProject(
            name='NAME',
            path=self.project_path,
            templates=templates,
        )
        (templates / 'dummy.j2').write_text(
            '{{ name }}'
        )

        project.process()

        cfg_actual = project.get_cfg_path(self.project_path).read_text()

        self.assertEqual(cfg_actual, cfg_expected)
        self.assertEqual(target.read_text(), 'NAME')
