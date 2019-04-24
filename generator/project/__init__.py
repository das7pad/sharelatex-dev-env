import copy
import logging
import pathlib
import typing

import jinja2

from generator.version import __version__

REPO = pathlib.Path(__file__).parent.parent.parent
TEMPLATES = REPO / 'templates'  # type: pathlib.Path


logger = logging.getLogger(__name__)


class Project:
    _languages = {}  # type: typing.Dict[str, typing.Type[Project]]
    language = ''
    insert_marker = 'INSERT_MARKER'

    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        dry_run: bool = False,
        update: bool = False,
        templates: pathlib.Path = TEMPLATES,
        **kwargs
    ):
        self._name = name
        self._path = path
        self._dry_run = dry_run
        self._kwargs = kwargs
        self._org_kwargs = copy.deepcopy(kwargs)
        self._update = update
        self._changed = False

        if update:
            self['script_version'] = __version__

        search_path = []
        for cls in self.__class__.mro():
            if not issubclass(cls, Project):
                continue

            if 'script_version' in kwargs:
                search_path.append(
                    templates / kwargs['script_version'] / cls.language
                )
            search_path.append(templates / cls.language)

        self._template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                searchpath=search_path,
            ),
            lstrip_blocks=True,
            trim_blocks=True,
            keep_trailing_newline=True,
        )

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
        update: bool = False,
    ) -> 'Project':
        raw = cls.get_cfg_path(path).read_text()
        kwargs = cls._parse_cfg(raw)

        target = cls._get_subclass(kwargs['language'])
        del kwargs['language']

        return target(
            path=path,
            dry_run=dry_run,
            update=update,
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

    def _get_cfg_fields(
        self,
    ) -> typing.List[str]:
        return [
            'language',
            self.insert_marker,
            'script_version',
        ]

    def _serialize_cfg(
        self,
    ) -> str:
        cfg = self._kwargs.copy()
        cfg['language'] = self.language

        field_preference = self._get_cfg_fields()

        unknown_fields = set(cfg.keys()) - set(field_preference)
        pos = field_preference.index(self.insert_marker)

        for key in sorted(unknown_fields, reverse=True):
            field_preference.insert(pos, key)

        def get_pos(item):
            return field_preference.index(item[0])

        lines = [
            self._name,
        ]
        for field, value in sorted(cfg.items(), key=get_pos):
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
            logger.info(
                '[DRY RUN] skipping write to %s',
                path,
            )
            return 0

        path.parent.mkdir(parents=True, exist_ok=True)
        return path.write_text(content)

    def _get_possible_project_files(
        self,
    ) -> typing.Dict[str, str]:
        return {
            'has_install_deps': 'install_deps.sh',
            'has_entrypoint': 'entrypoint.sh',
            'has_setup_env': 'setup_env.sh',
        }

    def _get_env(self):
        env = {
            'version': __version__,
            'name': self._name,
            'language': self.language,
        }
        for label, file in self._get_possible_project_files().items():
            env[label] = (self._path / file).exists()

        env.update(self._kwargs)
        return env

    def _get_template(
        self,
        name: str,
    ):
        return self._template_env.get_template(
            name=name + '.j2',
        )

    def _update_file(
        self,
        name: str,
        env: dict,
    ):
        target = self._path / name
        if target.exists():
            current = target.read_text()
        else:
            current = None

        template = self._get_template(
            name=name,
        )

        new = template.render(**env)
        if current == new:
            return False

        self._changed = True
        self._write(target, new)
        return True

    def _get_files_to_update(
        self,
    ) -> typing.List[str]:
        return [
            '.github/ISSUE_TEMPLATE.md',
            '.github/PULL_REQUEST_TEMPLATE.md',
        ]

    def _delete_orphan_files(
        self,
    ) -> int:
        kwargs = self._kwargs
        self._kwargs = self._org_kwargs
        old_files = set(self._get_files_to_update())

        self._kwargs = kwargs
        new_files = set(self._get_files_to_update())

        diff = old_files - new_files
        if not diff:
            return 0

        self._changed = True
        for file in diff:
            path = self._path / file
            if path.exists():
                path.unlink()

        return len(diff)

    def process(
        self,
    ):
        self._delete_orphan_files()

        files = self._get_files_to_update()
        env = self._get_env()
        for file in files:
            self._update_file(
                name=file,
                env=env,
            )

        self._dump_cfg()
