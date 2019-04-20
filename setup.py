import pathlib

from setuptools import (
    find_packages,
    setup,
)


if __name__ == '__main__':
    REPO = pathlib.Path(__file__).parent  # type: pathlib.Path

    setup(
        name='generator',
        version=(
            (REPO / 'generator' / 'version.py').read_text().split()[-1][1:-2]
        ),
        packages=find_packages(),
        install_requires=[
            line
            for line in (
                (REPO / 'requirements.txt').read_text().splitlines()
            )
            if line[:1] != '#'
        ],
        entry_points={
            'console_scripts': [
                'generate=generator.__main__:main'
            ]
        },
    )
