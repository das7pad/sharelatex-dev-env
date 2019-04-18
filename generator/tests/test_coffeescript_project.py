import pathlib
import shutil
import tempfile
import unittest

from generator.project import Project
from generator.project.coffeescript import CoffeeScriptProject


def strip_indent(raw):
    return raw.replace('\n' + ' ' * 12, '\n').lstrip('\n')


class TestCoffeeScriptProject(unittest.TestCase):
    def setUp(self):
        self.project_path = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.project_path)
        Project._template_cache.clear()

    def test_subclass_init(self):
        project_in = strip_indent(
            """
            NAME
            --language=coffeescript
            """
        )
        Project.get_cfg_path(self.project_path).write_text(project_in)

        actual = Project.from_path(self.project_path)
        expected = CoffeeScriptProject(
            name='NAME',
            path=self.project_path,
        )

        self.assertEqual(actual, expected)
