import pathlib
import typing


class Project:
    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        **kwargs
    ):
        self._name = name
        self._path = path
        self._kwargs = kwargs
        self._changed = False

    def __contains__(self, item):
        return item in self._kwargs

    def __getitem__(self, item):
        return self._kwargs[item]

    def __setitem__(self, key, value):
        if key in self and self[key] == value:
            return value

        self._kwargs[key] = value
        self._changed = True
        return value

    @classmethod
    def from_path(
        cls,
        path: pathlib.Path,
    ) -> 'Project':
        raw = cls.get_cfg_path(path).read_text()
        kwargs = cls._parse_cfg(raw)
        return cls(
            path=path,
            **kwargs
        )

    @staticmethod
    def get_cfg_path(path: pathlib.Path) -> pathlib.Path:
        return path / 'buildscript.txt'

    @staticmethod
    def _parse_cfg(
        raw: str,
    ) -> typing.Dict[str, typing.Union[str, typing.List[str]]]:
        kwargs = {}
        kwargs['name'], *arguments = raw.splitlines()

        for line in arguments:
            argument, value = line[2:].split('=', 1)

            if ',' in value:
                value = value.split(',')

            if value == 'None':
                value = None

            kwargs[argument.replace('-', '_')] = value

        return kwargs

    def process(
        self,
    ):
        self.get_cfg_path(self._path).write_text(self._serialize_cfg())

    def _serialize_cfg(
        self,
    ) -> str:
        lines = [
            self._name,
        ]

        for field, value in self._kwargs.items():
            if isinstance(value, list):
                value = ','.join(value)
            lines.append(
                '--{field}={value}'.format(
                    field=field.replace('_', '-'),
                    value=value,
                )
            )

        lines.append('')
        return '\n'.join(lines)
