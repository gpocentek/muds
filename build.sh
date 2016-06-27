#!/bin/sh

set -e

rm -rf dist
python setup.py sdist
#cd dist
#tar xf *gz
#rm *gz
#mv * muds
#tar czf muds.tgz muds
#ls
#cd ..
docker build -t muds/latest .
