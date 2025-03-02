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
#	nohup podman image build -f opentaxliberty.pm -t opentaxliberty:20250223 . > ~/temp/20250223_opentaxliberty.log 2>&1 &
#
# to run container:
#   podman run -it --rm --mount type=bind,source=/home/rovitotv,target=/home/rovitotv opentaxliberty:20250223 
FROM alpine:latest

MAINTAINER rovitotv@gmail.com

RUN apk update && apk upgrade
RUN apk add --no-cache py3-pip
RUN apk add --no-cache py3-pytest
RUN apk add --no-cache ipython

RUN pip3 install --upgrade --break-system-packages pip 
RUN pip3 install --break-system-packages pypdf

WORKDIR /home/rovitotv/code/
ENV SHELL /bin/ash
