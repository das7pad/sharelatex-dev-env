import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

from generator.project import Project, InvalidConfig


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

    def test_write_ignore(self):
        project = Project(
            name='NAME',
            path=self.project_path,
            dry_run=False,
        )
        target = self.project_path / 'dummy.txt'
        project._write(target, 'DATA')
        self.assertEqual(target.read_text(), 'DATA')

        actual = project._write(target, '\n')
        self.assertEqual(actual, -1)
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

    def test_parser_single_item_list(self):
        project_in = strip_indent(
            """
            NAME
            --arg=one,
            """
        )

        actual = Project._parse_cfg(project_in)
        expected = {
            'name': 'NAME',
            'arg': [
                'one',
            ],
        }

        self.assertDictEqual(actual, expected)

    @mock.patch('generator.project.logger.warning')
    def test_validate_cfg_no_dep(self, warning):
        actual = Project._validate_cfg(
            {
                'name': 'NAME',
                'dependencies': '',
            }
        )

        self.assertEqual(actual, 0)

        warning.assert_not_called()

    @mock.patch('generator.project.logger.warning')
    def test_validate_cfg_single_dep(self, warning):
        actual = Project._validate_cfg(
            {
                'name': 'NAME',
                'dependencies': 'single',
            }
        )

        self.assertEqual(actual, 1)

        warning.assert_called()

    @mock.patch('generator.project.logger.warning')
    def test_validate_cfg_single_redis(self, warning):
        actual = Project._validate_cfg(
            {
                'name': 'NAME',
                'dependencies': [
                    'redis',
                ],
            }
        )

        self.assertEqual(actual, 2)

        warning.assert_called()

    @mock.patch('generator.project.logger.warning')
    def test_parser_invalid_cfg(self, warning):
        project_in = strip_indent(
            """
            NAME
            --dependencies=single
            """
        )

        Project.get_cfg_path(self.project_path).write_text(project_in)

        with self.assertRaises(InvalidConfig) as context:
            Project.from_path(self.project_path)

        actual = context.exception.args
        expected = InvalidConfig(1).args

        self.assertEqual(actual, expected)

        warning.assert_called()

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

    def test_drop_script_version_(self):
        project_in = strip_indent(
            """
            NAME
            --language=LANGUAGE
            --script-version=0.0.1
            """
        )
        project_out = strip_indent(
            """
            NAME
            --language=LANGUAGE
            """
        )

        Project.get_cfg_path(self.project_path).write_text(project_in)

        project = Project.from_path(
            path=self.project_path,
        )
        self.assertTrue(project._dump_cfg())
        actual = Project.get_cfg_path(self.project_path).read_text()
        self.assertEqual(actual, project_out)

    def test_init(self):
        project_in = strip_indent(
            """
            NAME
            --language=LANGUAGE
            --node-version=1.2.3
            --dependencies=mongo,redis_api
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
            dependencies=[
                'mongo',
                'redis_api',
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
            --dependencies=mongo,
            --docker-repos=example.com/images
            --node-version=1.2.3
            """
        )
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            node_version='1.2.3',
            dependencies=[
                'mongo',
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
            --dependencies=mongo,
            --docker-repos=example.com/images
            --node-version=1.2.3
            --unknown-arg=VALUE
            """
        )
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            node_version='1.2.3',
            dependencies=[
                'mongo',
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
            """
        )
        project_1 = GenericProject(
            name='NAME',
            path=self.project_path,
            unknown_arg='VALUE',
            other_arg='1',
        )
        project_2 = GenericProject(
            name='NAME',
            path=self.project_path,
            other_arg='1',
            unknown_arg='VALUE',
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
        name = 'NAME'
        project = GenericProject(
            name=name,
            path=self.project_path,
            templates=templates,
        )
        language = project.language

        def merge_path(*path_parts: str):
            merged = templates
            for part in path_parts:
                merged = merged / '_' / part
            return merged

        preference = [
            ('NAME_COMMON', merge_path(name) / 'common'),
            ('NAME', merge_path(name)),
            ('LANG_COMMON', merge_path(language) / 'common'),
            ('LANG', merge_path(language)),
            ('GLOBAL_COMMON', templates / 'common'),
            ('GLOBAL', templates),
        ]

        for content, path in preference:
            path.mkdir(parents=True, exist_ok=True)
            (path / file).write_text(content)

        for content, _ in preference:
            template = project._get_template(
                name='dummy',
            )
            path = pathlib.Path(template.filename)
            self.assertEqual(path.read_text(), content)
            path.unlink()

    def test_get_files_to_update(self):
        templates = self.templates_path
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            templates=templates,
        )

        def touch(path: pathlib.Path):
            path.parent.mkdir(exist_ok=True)
            path.write_text('')
            return path

        touch(templates / 'macros' / 'macro_one.j2')

        touch(templates / 'level_one.j2')
        touch(templates / 'one' / 'level_two.j2')
        touch(templates / 'one' / 'two' / 'level_three.j2')
        touch(templates / 'one' / 'two' / 'three' / 'level_four.j2')

        expected = [
            'level_one',
            'one/level_two',
            'one/two/level_three',
            'one/two/three/level_four',
        ]
        actual = project._get_files_to_update()
        self.assertEqual(actual, expected)

    def test_update_file(self):
        templates = self.templates_path
        target = self.project_path / 'dummy'
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            templates=templates,
        )
        (templates / 'dummy.j2').write_text(
            'THE {{ var }}\n'
        )

        project._update_file(
            name='dummy',
            env={'var': 'CONTENT'},
        )
        self.assertEqual(target.read_text(), 'THE CONTENT\n')

    def test_whitespace_cleanup(self):
        templates = self.templates_path
        target = self.project_path / 'verbose'
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            templates=templates,
        )
        template = strip_indent(
            """
            THE {{ var }}

            {% if false %}
            SKIP
            {% endif %}

            {% if false %}
            SKIP THIS TOO
            {% endif %}

            INCLUDE ME

            {% if false %}
            SKIP THIS AS WELL
            {% endif %}
            """
        )
        (templates / 'verbose.j2').write_text(template)

        project._update_file(
            name='verbose',
            env={'var': 'CONTENT'},
        )
        expected = strip_indent(
            """
            THE CONTENT

            INCLUDE ME
            """
        )
        self.assertEqual(expected, target.read_text())

    def test_delete_orphan(self):
        class DemoProject(GenericProject):
            @staticmethod
            def _get_deleted_templates():
                return {'old'}

        project = DemoProject(
            name='NAME',
            path=self.project_path,
            templates=self.templates_path,
            update=True,
        )

        # nothing there yet to delete
        self.assertEqual(project._delete_orphan_files(), 0)

        (self.project_path / 'old').touch()

        self.assertEqual(project._delete_orphan_files(), 1)
        self.assertTrue(project._changed)

        self.assertFalse((self.project_path / 'old').exists())

    def test_process(self):
        target = self.project_path / 'dummy'
        cfg_expected = strip_indent(
            """
            NAME
            --language=LANGUAGE
            """
        )
        templates = self.templates_path
        project = GenericProject(
            name='NAME',
            path=self.project_path,
            templates=templates,
        )
        (templates / 'dummy.j2').write_text(
            '{{ name }}\n'
        )

        project.process()

        cfg_actual = project.get_cfg_path(self.project_path).read_text()

        self.assertEqual(cfg_actual, cfg_expected)
        self.assertEqual(target.read_text(), 'NAME\n')
