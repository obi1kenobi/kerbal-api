#!/usr/bin/env bash

# Treat undefined variables and non-zero exits in pipes as errors.
set -uo pipefail

# Ensure that the "**" glob operator is applied recursively.
# Make globs that do not match return null values.
shopt -s globstar nullglob

# Break on first error.
set -e

# Make sure the current working directory for this script is the root directory.
cd "$(git -C "$(dirname "${0}")" rev-parse --show-toplevel )"

# Assert script is running inside poetry shell
set +u
if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Please run this command in a poetry shell, or via 'poetry run'."
    exit 1
fi
set -u

black .
isort --settings-path=setup.cfg --recursive . --atomic
