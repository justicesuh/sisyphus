#!/bin/sh

docker exec -it sisyphus_django uv run manage.py startapp $1
docker exec -it sisyphus_django mv $1 sisyphus

sh ./scripts/recursive_chown.sh
rm sisyphus/$1/tests.py
mkdir -p sisyphus/$1/tests
touch sisyphus/$1/tests/__init__.py
sed -i "s/    name = '$1'/    name = 'sisyphus.$1'/" sisyphus/$1/apps.py

echo "'sisyphus.$1',"
