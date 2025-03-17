#!/bin/bash
#
# This script starts the Open Tax Liberty FastAPI server
# the environment variable LOG_LEVEL sets the log level DEBUG or INFO

podman run -it --rm -p 8000:8000 \
	--mount type=bind,source=$HOME,target=/workspace \
	opentaxliberty:20250316 \
	sh -c "export LOG_LEVEL=DEBUG && cd /workspace/code/qualia_insights/opentaxliberty && fastapi dev opentaxliberty.py --host 0.0.0.0"
