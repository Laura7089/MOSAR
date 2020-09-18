FROM python:3.5.10-slim

RUN apt-get update
RUN apt-get install -y morse-simulator blender=2.79.b+dfsg0-7 alsa-utils

COPY ./MORSE/cubemodule-builder.py /usr/lib/python3/dist-packages/morse/builder/robots/cubemodule.py
COPY ./MORSE/cubemodule-robot.py /usr/lib/python3/dist-packages/morse/robots/cubemodule.py
COPY ./MORSE/cubemodule.blend /usr/share/morse/data/robots/cubemodule.blend

RUN printf "\nfrom .cubemodule import *\n" >> /usr/lib/python3/dist-packages/morse/builder/robots/__init__.py

RUN usermod -aG audio root

ENTRYPOINT /bin/bash
