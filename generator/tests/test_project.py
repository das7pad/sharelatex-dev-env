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
        GenericProject.register()

    def tearDown(self):
        shutil.rmtree(self.project_path)
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
            --node-version=1.2.3
            --acceptance-creds=None
            --dependencies=mongo,redis
            --docker-repos=example.com/images
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
            --node-version=1.2.3
            --acceptance-creds=None
            --dependencies=mongo,redis
            --docker-repos=example.com/images
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

    def test_get_template_path(self):
        project = GenericProject(
            name='NAME',
            path=self.project_path,
        )

        templates = pathlib.Path(tempfile.mkdtemp())
        file = 'dummy.j2'
        try:
            (templates / GenericProject.language).mkdir(exist_ok=True)
            (templates / GenericProject.language / file).write_text('CHILD')
            (templates / file).write_text('PARENT')

            path = project._get_template_path(
                name=file,
                templates=templates,
            )
            self.assertEqual(path.read_text(), 'CHILD')

            (templates / GenericProject.language / file).unlink()
            path = project._get_template_path(
                name=file,
                templates=templates,
            )
            self.assertEqual(path.read_text(), 'PARENT')
        finally:
            shutil.rmtree(templates)

    def test_get_template_cached(self):
        project = GenericProject(
            name='NAME',
            path=self.project_path,
        )

        templates = pathlib.Path(tempfile.mkdtemp())
        file = 'dummy.j2'
        other_file = 'not_dummy.j2'
        try:
            (templates / file).touch()
            (templates / other_file).touch()

            template_0 = project._get_template(
                name=file,
                templates=templates,
            )
            template_1 = project._get_template(
                name=file,
                templates=templates,
            )
            self.assertIs(template_0, template_1)

            template_2 = project._get_template(
                name=other_file,
                templates=templates,
            )
            self.assertIsNot(template_0, template_2)

        finally:
            shutil.rmtree(templates)

    def test_process(self):
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
        project.process()

        cfg_actual = project.get_cfg_path(self.project_path).read_text()
        cfg_expected = strip_indent(
            """
            NAME
            --language=LANGUAGE
            --node-version=1.2.3
            --acceptance-creds=None
            --dependencies=mongo,redis
            --docker-repos=example.com/images
            """
        )
        self.assertEqual(cfg_actual, cfg_expected)
