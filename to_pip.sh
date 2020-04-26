#!/bin/bash

mkdir -p tests
rm -rf dist/

python3 setup.py sdist bdist_wheel

#cat ~/.home/.pypirc_test
#twine upload --repository testpypi dist/*

twine upload dist/*

# login: __token__
# password: value of the token (starting with pypi-)
