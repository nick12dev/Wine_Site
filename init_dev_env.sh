#!/usr/bin/env bash

source "$(pipenv --venv)/bin/activate"
pipenv install --dev

git config core.hooksPath .githooks


pipenv shell
