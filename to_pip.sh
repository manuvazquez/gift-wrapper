#!/bin/bash

mkdir -p tests
rm -rf dist/

python3 setup.py sdist bdist_wheel

# for testing
#cat ~/.home/.pypirc_test
#twine upload --repository testpypi dist/*

# for production
twine upload dist/*
