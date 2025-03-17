# ============================================================================
# Open Tax Liberty - Python program to make IRS 1040 forms
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ============================================================================
# this is a small container for open tax liberty project 
# 2024 tax season
#
# includes Python, ipython, pytest, and pypdf
#
# To build container:
#	nohup podman image build -f Containerfile -t opentaxliberty:20250316 . > ~/temp/20250316_opentaxliberty.log 2>&1 &
#
# run container and produce a shell:
#   podman run -it --rm --mount type=bind,source=$HOME,target=/workspace opentaxliberty:20250316 
#
# run the container with FastAPI development mode
#   podman run -it --rm -p 8000:8000 --mount type=bind,source=$HOME,target=/workspace opentaxliberty:20250316 sh -c "cd /workspace/code/qualia_insights/opentaxliberty && fastapi dev opentaxliberty.py --host 0.0.0.0"
FROM alpine:latest

MAINTAINER rovitotv@gmail.com

RUN apk update && apk upgrade
RUN apk add --no-cache py3-pip
RUN apk add --no-cache py3-pytest
RUN apk add --no-cache py3-mypy
RUN apk add --no-cache ipython
RUN apk add --no-cache curl

RUN pip3 install --upgrade --break-system-packages pip 
RUN pip3 install --break-system-packages pypdf
RUN pip3 install --break-system-packages "fastapi[standard]"

ENV SHELL /bin/ash
