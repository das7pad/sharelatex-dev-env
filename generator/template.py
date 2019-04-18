import pathlib
import typing

import jinja2


REPO = pathlib.Path(__file__).parent.parent.parent
TEMPLATES = REPO / 'templates'  # type: pathlib.Path


class Template:
    def __init__(
        self,
        target_file: pathlib.Path,
        actual_file: pathlib.Path,
        comment_prefix: str = '# ',
    ):
        self._target = target_file
        self._actual = actual_file
        self._comment_prefix = comment_prefix

        self._template = jinja2.Template(
            source=actual_file.read_text(),
            lstrip_blocks=True,
            trim_blocks=True,
            keep_trailing_newline=True,
        )

    def render(self, env: dict):
        if 'header' in env and env['header']:
            header = env['header']  # type: typing.List[str]
            if isinstance(header, str):
                header = header.splitlines()

            env['header'] = (
                self._comment_prefix
                + ('\n' + self._comment_prefix).join(header)
            )
        return self._template.render(**env)
