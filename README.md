# bundle-deps

Bundle a project's **npm** and **uv** dependencies, read from its lock files, into a single
archive for offline or air-gapped installs. It can also build a *delta* bundle containing only
the dependencies added since an earlier commit.

Python 3.11+. Depends on `requests` and `tqdm`. Needs `git` on `PATH` for delta mode.

## Install

    pip install bundle-deps          # from PyPI
    pip install git+<repo-url>       # or straight from git

## Usage

    bundle-deps <project_path> [--commit-sha SHA | --latest-commit] [--manylinux]
                [--no-pack] [--bundle-name NAME] [--output-dir DIR] [-v]

Also runnable as `python -m bundle_deps`.

| Option | Description |
| --- | --- |
| `project_path` | Project directory. It is searched recursively for lock files. |
| `--commit-sha SHA` | Delta mode: skip dependencies already present at this commit. |
| `--latest-commit` | Delta mode against `HEAD^` of the remote repo. |
| `--manylinux` | For uv, keep only manylinux wheels and pure-Python (`-any.whl`) wheels. |
| `--no-pack` | Output a plain folder instead of a `.tar.gz`. |
| `--bundle-name NAME` | Bundle name. Default: `<YYYYmmdd_HHMMSS>-<GITHUB_SHA>`. |
| `--output-dir DIR` | Where to write the result. Default: the current directory. |
| `-v`, `--verbose` | Print each file as it downloads instead of a progress bar. |

### Examples

    # full bundle of everything in the lock files
    bundle-deps ./my-app

    # only what is new since a previous release, Linux-friendly wheels
    bundle-deps ./my-app --commit-sha 1a2b3c4 --manylinux --output-dir ./out

## What it does

1. Finds every `package-lock.json` and `uv.lock` under `project_path`.
2. Collects the packages, versions and URLs from them.
3. In delta mode, clones the repo (URL from `GITHUB_SERVER_URL` and `GITHUB_REPOSITORY`, or the
   `origin` remote), exports the chosen commit, reads its lock files, and drops every
   `name@version` that already existed there.
4. Downloads the rest into a temp dir:
   - npm: one `.tgz` per package (the `resolved` URL).
   - uv: every wheel, plus the sdist.
5. Packs the result and removes the temp dir.

If no lock files are found, or nothing needs downloading, no bundle is written.

## Output layout

```
<bundle-name>.tar.gz
└── <bundle-name>/
    ├── npm-dependencies.tgz   # all npm tarballs
    └── uv/                    # wheels and sdists
```

Either part is omitted if it has no dependencies. With `--no-pack` you get the
`<bundle-name>/` folder directly.

## Using the bundle offline

    # npm
    tar xzf npm-dependencies.tgz -C ./npm-cache
    npm install --offline ./npm-cache/*.tgz

    # uv
    uv pip install --no-index --find-links ./uv <package>

## Notes

- Delta mode compares exact `name@version` strings, so a version bump counts as new.
- Packages without a download URL are reported and skipped.
- Exit code is `1` with an `error:` message on bad paths or failed git, read or archive steps.
