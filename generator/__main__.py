import argparse
import pathlib
import typing

from generator.project import Project


def get_args(args: typing.Optional[typing.List[str]] = None):
    parser = argparse.ArgumentParser(
        'generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        'path',
        nargs='+',
        type=pathlib.Path,
        help='One or more project paths',
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Skip writing',
    )

    return parser.parse_args(args)


def main(args):
    for raw_path in args.path:
        path = pathlib.Path(raw_path)

        project = Project.from_path(
            path=path,
            dry_run=args.dry_run,
        )
        project.process()


if __name__ == '__main__':
    main(get_args())
