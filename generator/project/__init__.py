import pathlib
import typing

from generator.template import Template
from generator.template import TEMPLATES


class Project:
    _languages = {}  # type: typing.Dict[str, typing.Type[Project]]
    language = ''
    _template_cache = {}

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

        for line in raw.splitlines():
            if line[:2] != '--':
                kwargs['name'] = line
                continue

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

    def _dump_cfg(self):
        path = self.get_cfg_path(self._path)
        if path.exists():
            if not self._changed:
                return False

            # did the config actually changed?
            reloaded = self._parse_cfg(path.read_text())
            del reloaded['name']
            del reloaded['language']
            if self._kwargs == reloaded:
                return False

        return self._write(
            path=path,
            content=self._serialize_cfg(),
        )

    def _write(
        self,
        path: pathlib.Path,
        content: str,
    ):
        if self._dry_run:
            print('[DRY RUN] skipping write to {path}'.format(path=path))
            return 0

        return path.write_text(content)

    def _get_env(self):
        env = {
            'name': self._name,
            'language': self.language,
            'has_install_deps': (self._path / 'install_deps.sh').exists(),
            'has_entrypoint': (self._path / 'entrypoint.sh').exists(),
        }
        env.update(self._kwargs)
        return env

    def _get_template_path(
        self,
        name: str,
        templates: pathlib.Path = TEMPLATES,
    ):
        languages = []
        for cls in self.__class__.mro():
            if issubclass(cls, Project):
                languages.append(cls.language)

        for language in languages:
            path = templates / language / name
            if path.exists():
                return path

    def _get_template(
        self,
        name: str,
        comment_prefix: str = None,
        templates: pathlib.Path = TEMPLATES,
    ):
        key = (self.__class__, name)
        if key in self._template_cache:
            return self._template_cache[key]
        path = self._get_template_path(
            name=name,
            templates=templates,
        )

        kwargs = {}
        if comment_prefix is not None:
            kwargs['comment_prefix'] = comment_prefix,

        template = Template(
            path=path,
            **kwargs
        )
        self._template_cache[key] = template
        return template

    def _update_file(
        self,
        name: str,
        env: dict,
        comment_prefix: str = None,
        templates: pathlib.Path = TEMPLATES,
    ):
        target = self._path / name
        if target.exists():
            current = target.read_text()
        else:
            current = ''

        template = self._get_template(
            name=name + '.j2',
            comment_prefix=comment_prefix,
            templates=templates,
        )

        new = template.render(env)
        if current == new:
            return False

        self._changed = True
        self._write(target, new)
        return True

    def _get_files_to_update(
        self,
    ) -> typing.List[typing.Tuple[str, typing.Optional[str]]]:
        return []

    def process(
        self,
        templates: pathlib.Path = TEMPLATES,
    ):
        files = self._get_files_to_update()
        env = self._get_env()
        for file, comment_prefix in files:
            self._update_file(
                name=file,
                env=env,
                comment_prefix=comment_prefix,
                templates=templates,
            )

        self._dump_cfg()