#!/bin/sh

# files generated via django-admin inside
# docker container are owned by root
sudo chown -R $(whoami):$(whoami) sisyphus
