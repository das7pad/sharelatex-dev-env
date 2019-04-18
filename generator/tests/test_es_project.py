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

    def test_update_node_version(self):
        nvm_rc = self.project_path / '.nvmrc'
        nvm_rc.write_text('1.2.3\n')

        project = ESProject(
            name='NAME',
            path=self.project_path,
            node_version='2.3.4',
        )
        project._update_nvmrc()

        self.assertTrue(project._changed)
        self.assertEqual(nvm_rc.read_text(), '2.3.4\n')
