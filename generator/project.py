import pathlib
import typing


class Project:
    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        language: str,
        node_version: str,
        acceptance_creds: typing.Optional[str],
        dependencies: typing.List[str],
        docker_repos: str,
        **kwargs
    ):
        self._name = name
        self._path = path
        self._language = language
        self._node_version = node_version
        self._acceptance_creds = acceptance_creds
        self._dependencies = dependencies
        self._docker_repos = docker_repos

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

    def _serialize_cfg(
        self,
    ) -> str:
        lines = [
            self._name,
        ]

        fields = [
            '_language',
            '_node_version',
            '_acceptance_creds',
            '_dependencies',
            '_docker_repos',
        ]
        for field in fields:
            value = self.__dict__[field]
            if isinstance(value, list):
                value = ','.join(value)
            lines.append(
                '--{field}={value}'.format(
                    field=field[1:].replace('_', '-'),
                    value=value,
                )
            )

        lines.append('')
        return '\n'.join(lines)
