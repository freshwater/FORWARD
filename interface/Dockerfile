
#

FROM ubuntu:latest

RUN apt-get update


## Python

RUN apt-get install --yes python3
RUN apt-get install --yes python3-pip
RUN pip3 install --upgrade pip


## PyTorch

RUN pip3 install torch
RUN pip3 install torchvision

RUN apt-get install --yes xvfb
RUN apt-get install --yes python-opengl
RUN pip3 install gym-retro


RUN pip3 install matplotlib
RUN pip3 install scikit-learn


## ffmpeg

RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes ffmpeg


## JSX

WORKDIR /server_directory

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install --yes nodejs \
                          npm

RUN npm install @babel/core @babel/cli @babel/preset-react
RUN npm install webpack webpack-cli

COPY static /tmp
COPY src .
COPY roms roms

RUN python3 -m retro.import roms
RUN npx babel --presets @babel/react application.js -o application.js
RUN npx webpack application.js --mode=development --output application.js


WORKDIR /workfolder
