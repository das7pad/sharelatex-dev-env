import pathlib
import sys

from generator.project import Project


def main(args):
    for raw_path in args:
        path = pathlib.Path(raw_path)

        project = Project.from_path(
            path=path,
        )
        project.process()


if __name__ == '__main__':
    main(sys.argv[1:])
