#!/bin/bash
#
# Shell script to start the testing container, export variables, and execute
# the tests

podman run -it --rm \
	--mount type=bind,source=/home/rovitotv,target=/home/rovitotv \
	opentaxliberty:20250223 \
	sh -c "cd qualia_insights/opentaxliberty/tests && pytest-3 -s"
