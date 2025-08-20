# lh-index-ingestion-job
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

<!-- TOC depthFrom:2 depthTo:3 -->

- [Documentation](#documentation)
- [Installation](#installation)
- [Tests](#testing)
  - [Ruff code formatter](#run-the-code-formatter)
  - [Ruff linter - ruff check](#run-the-linter)
  - [Unit tests - pytest](#run-the-unit-tests)
- [Resources](#resources)

<!-- /TOC -->

## Documentation

## Installation

### Initial setup
There are git-hooks associated with this repository which are meant to automate some workflow and
place some checks on the code and the repo to ensure best practises. The hooks are located in the
.githooks folder. This folder needs to be setup with the following command -

```bash
make gitsetup
```

### Dependencies

Dependencies are managed by [Poetry](https://python-poetry.org/)

- With dev dependencies:

The `install` command reads the `pyproject.toml` file from the current project, resolves the dependencies, and installs them.
```bash
$ poetry install
```

If there is a `poetry.lock` file in the current directory, it will use the exact versions from there instead of resolving them. This ensures that everyone using the library will get the same versions of the dependencies.

- Without dev dependencies:

You can specify to the command that you do not want the development dependencies installed by passing the --no-dev option.

```bash
$ poetry install --no-dev
```

#### Update dependencies
In order to get the latest versions of the dependencies and to update the `poetry.lock` file, you should use the update command.

```bash
$ poetry update
```

This will resolve all dependencies of the project and write the exact versions into `poetry.lock`.

Alternatively, ff you just want to update a few packages and not all, you can list them as such:

```bash
$ poetry update requests toml
```

### Add a dependency

The add command adds required packages to your pyproject.toml and installs them.

```bash
$ poetry add pendulum@^2.0.5
```

## Testing

### Run the code formatter

This runs ruff formatter
```bash
$ make format
```

### Run the linter

This test check syntax error.
```bash
$ make lint
```

### Run the unit tests

```bash
$ make pytest
```

### Run the git hooks (commit and branch convention checking)

```bash
$ make commitlint
```

### Run the code formatter, optional static type checker, linter, and unit tests

```bash
$ make test
```
## Ruff

### Format

To format the files
```bash
ruff format
```

### Check
To check the files, you can add `-fix` to fix small issues such as import ordering, etc.
```bash
ruff check
```

## Pre-commit

### Install pre-commit

```bash
pip install pre-commit
```

### Install the pre-commit rules
```bash
pre-commit install
```

### How to run it

1. A `git commit` will trigger it.
2. Using `pre-commit run --all-files`.

## Resources

- [poetry](https://python-poetry.org/docs/)
- [pytest](https://docs.pytest.org/en/stable/)