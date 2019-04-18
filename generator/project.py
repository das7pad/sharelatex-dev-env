import pathlib
import typing


class Project:
    def __init__(
        self,
        name: str,
        language: str,
        node_version: str,
        acceptance_creds: typing.Optional[str],
        dependencies: typing.List[str],
        docker_repos: str,
        **kwargs
    ):
        self._name = name
        self._language = language
        self._node_version = node_version
        self._acceptance_creds = acceptance_creds
        self._dependencies = dependencies
        self._docker_repos = docker_repos

    @classmethod
    def from_cfg(
        cls,
        path: pathlib.Path,
    ) -> 'Project':
        raw = path.read_text()
        kwargs = cls._parse_cfg(raw)
        return cls(**kwargs)

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
