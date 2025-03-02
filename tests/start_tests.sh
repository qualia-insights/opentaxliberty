#!/bin/bash
#
# Shell script to start the testing container, export variables, and execute
# the tests

podman run -it --rm \
	--mount type=bind,source=$HOME,target=/workspace \
	opentaxliberty:20250301 \
	sh -c "cd /workspace/code/qualia_insights/opentaxliberty/tests && pytest-3 -s"
