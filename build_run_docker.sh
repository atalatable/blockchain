#!/bin/sh

if [ "$#" = 1 ]; then
    docker build -t "$1" .
    docker run -it "$1"
else
    echo "You should give a name for the docker image"
    echo "usage: $0 name"
fi