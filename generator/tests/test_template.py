import pathlib
import tempfile
import unittest

from generator.template import Template


def strip_indent(raw):
    return raw.replace('\n' + ' ' * 12, '\n').lstrip('\n')


class TestTemplate(unittest.TestCase):
    def setUp(self):
        self.template_path = pathlib.Path(tempfile.mktemp())

    def tearDown(self):
        self.template_path.unlink()

    def test_render(self):
        template_in = strip_indent(
            """
            {{ some_var }}
            """
        )
        self.template_path.write_text(template_in)

        template = Template(
            self.template_path,
        )

        expected = strip_indent(
            """
            SOME_VAR
            """
        )
        actual = template.render(
            env={
                'some_var': 'SOME_VAR',
            }
        )

        self.assertEqual(actual, expected)

    def test_header_single_line(self):
        template_in = strip_indent(
            """
            {{ header }}

            {{ some_var }}
            """
        )
        self.template_path.write_text(template_in)

        template = Template(
            self.template_path,
        )

        expected = strip_indent(
            """
            # HEADER

            SOME_VAR
            """
        )
        actual = template.render(
            env={
                'header': 'HEADER',
                'some_var': 'SOME_VAR',
            }
        )

        self.assertEqual(actual, expected)

    def test_header_multi_line(self):
        template_in = strip_indent(
            """
            {{ header }}

            {{ some_var }}
            """
        )
        self.template_path.write_text(template_in)

        template = Template(
            self.template_path,
        )

        expected = strip_indent(
            """
            # HEADER 0
            # HEADER 1

            SOME_VAR
            """
        )
        actual = template.render(
            env={
                'header': [
                    'HEADER 0',
                    'HEADER 1'
                ],
                'some_var': 'SOME_VAR',
            }
        )

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
