import pathlib
import typing


class Project:
    _languages = {}  # type: typing.Dict[str, typing.Type[Project]]
    language = None

    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        dry_run: bool = False,
        **kwargs
    ):
        self._name = name
        self._path = path
        self._dry_run = dry_run
        self._kwargs = kwargs
        self._changed = False

    def __eq__(self, other):
        if not isinstance(other, Project):
            return False

        if self._name != other._name:
            return False

        if self._path != other._path:
            return False

        if self.language != other.language:
            return False

        if self._kwargs != other._kwargs:
            return False
        return True

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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._languages[cls.language] = cls

    @classmethod
    def _get_subclass(
        cls,
        language: str,
    ) -> 'typing.Type[Project]':
        for lang, target in cls._languages.items():
            if language == lang:
                return target
        return cls

    @classmethod
    def from_path(
        cls,
        path: pathlib.Path,
        dry_run: bool = False,
    ) -> 'Project':
        raw = cls.get_cfg_path(path).read_text()
        kwargs = cls._parse_cfg(raw)

        target = cls._get_subclass(kwargs['language'])
        del kwargs['language']

        return target(
            path=path,
            dry_run=dry_run,
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
            '--language={}'.format(self.language)
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

    def _write(
        self,
        path: pathlib.Path,
        content: str,
    ):
        if self._dry_run:
            print('[DRY RUN] skipping write to {path}'.format(path=path))
            return 0

        return path.write_text(content)

    def process(
        self,
    ):
        self._write(self.get_cfg_path(self._path), self._serialize_cfg())
