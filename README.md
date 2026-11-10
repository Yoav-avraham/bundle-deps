# bundle-deps

Bundle a project's npm and uv dependencies (from its lock files) for offline use.

## Install

    pip install bundle-deps          # from PyPI
    pip install git+<repo-url>       # or straight from git

## Usage

    bundle-deps <project_path> [--commit-sha SHA | --latest-commit] [--manylinux]
                [--no-pack] [--bundle-name NAME] [--output-dir DIR] [-v]

Also runnable as `python -m bundle_deps`.
