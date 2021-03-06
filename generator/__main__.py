import argparse
import logging
import pathlib
import sys
import typing

from generator.project import (
    Project,
    InvalidConfig,
    INHERIT,
)


def get_args(args: typing.Optional[typing.List[str]] = None):
    parser = argparse.ArgumentParser(
        'generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        'path',
        nargs='*',
        type=pathlib.Path,
        default=[pathlib.Path.cwd()],
        help='One or more project paths',
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Skip writing',
    )

    parser.add_argument(
        '--update',
        action='store_true',
        help='DEPRECATED',
    )

    parser.add_argument(
        '--node-version',
        default=INHERIT,
        help='Set the node version for a project',
    )

    return parser.parse_args(args)


def main(args: argparse.Namespace = None) -> int:
    if not args:
        args = get_args()

    for raw_path in args.path:
        path = pathlib.Path(raw_path)
        logging.root.handlers.clear()
        logging.basicConfig(
            level=logging.INFO,
            format=(
                '{name}: %(levelname)s %(name)s: %(message)s'
            ).format(
                name=path.resolve().name,
            ),
        )

        try:
            project = Project.from_path(
                path=path,
                dry_run=args.dry_run,
                node_version=args.node_version,
            )
        except InvalidConfig as err:
            return err.args[0]

        project.process()


if __name__ == '__main__':
    sys.exit(main())
