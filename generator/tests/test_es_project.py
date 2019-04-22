import pathlib
import shutil
import tempfile
import unittest

from generator.project import Project
from generator.project.es import ESProject


def strip_indent(raw):
    return raw.replace('\n' + ' ' * 12, '\n').lstrip('\n')


class TestESProject(unittest.TestCase):
    def setUp(self):
        self.project_path = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.project_path)

    def test_subclass_init(self):
        project_in = strip_indent(
            """
            NAME
            --language=es
            """
        )
        Project.get_cfg_path(self.project_path).write_text(project_in)

        actual = Project.from_path(self.project_path)
        expected = ESProject(
            name='NAME',
            path=self.project_path,
        )

        self.assertEqual(actual, expected)

    def test_serialize_sequence(self):
        expected = strip_indent(
            """
            NAME
            --language=es
            --node-version=1.2.3
            --acceptance-creds=None
            --dependencies=mongo,redis
            --docker-repos=example.com/images
            --other-arg=1
            --unknown-arg=VALUE
            --script-version=3.2.1
            """
        )
        project_1 = ESProject(
            name='NAME',
            path=self.project_path,
            script_version='3.2.1',
            node_version='1.2.3',
            dependencies=[
                'mongo',
                'redis',
            ],
            docker_repos='example.com/images',
            acceptance_creds=None,
            unknown_arg='VALUE',
            other_arg='1',
        )
        project_2 = ESProject(
            name='NAME',
            path=self.project_path,
            unknown_arg='VALUE',
            docker_repos='example.com/images',
            node_version='1.2.3',
            dependencies=[
                'mongo',
                'redis',
            ],
            script_version='3.2.1',
            acceptance_creds=None,
            other_arg='1',
        )
        actual_1 = project_1._serialize_cfg()
        actual_2 = project_2._serialize_cfg()

        self.assertEqual(actual_1, expected)
        self.assertEqual(actual_2, expected)
