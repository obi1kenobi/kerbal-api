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

# Get all python files or directories that need to be linted.
lintable_locations="."

# Continue on error to allow ignoring certain linters.
# Errors are manually aggregated at the end.
set +e

echo -e '*** Running isort... ***\n'
isort --check-only --settings-path=setup.cfg --diff --recursive $lintable_locations
isort_exit_code=$?
echo -e "\n*** End of isort run; exit: $isort_exit_code ***\n"

echo -e '*** Running black... ***\n'
black --check --diff .
black_exit_code=$?
echo -e "\n*** End of black run; exit: $black_exit_code ***\n"

echo -e '*** Running flake8... ***\n'
flake8 --config=setup.cfg $lintable_locations
flake_exit_code=$?
echo -e "\n*** End of flake8 run, exit: $flake_exit_code ***\n"

echo -e '*** Running mypy... ***\n'
mypy $lintable_locations
mypy_exit_code=$?
echo -e "\n*** End of mypy run, exit: $mypy_exit_code ***\n"

if  [[
        ("$flake_exit_code" != "0") ||
        ("$isort_exit_code" != "0") ||
        ("$black_exit_code" != "0") ||
        ("$mypy_exit_code" != "0")
    ]]; then
    echo -e "\n*** Lint failed. ***\n"
    echo -e "isort exit: $isort_exit_code"
    echo -e "black exit: $black_exit_code"
    echo -e "flake8 exit: $flake_exit_code"
    echo -e "mypy exit: $mypy_exit_code"
    exit 1
fi

echo -e "\n*** Lint successful. ***\n"
