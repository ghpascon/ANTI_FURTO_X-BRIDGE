#!/usr/bin/env bash
poetry cache clear pypi --all --no-interaction
poetry lock 
poetry install
