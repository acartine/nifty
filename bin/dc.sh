#!/bin/bash
# calls docker compose up given a list of profiles
command=$1
flags=

if [ "$command" = "up" ]; then
    flags=" -d --wait"
fi

shift
for profile in $@; do
    profiles=" ${profiles} --profile ${profile}"
done

docker compose ${profiles} ${command} ${flags}
