
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

WORKDIR /nodefolder
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install --yes nodejs \
                          npm

RUN npm install @babel/core @babel/cli @babel/preset-react
# RUN npm install --save-dev @babel/core @babel/preset-react

RUN mkdir /not_tmp
COPY ["static", "/tmp/"]
COPY ["src/", "/not_tmp/"]
COPY ["roms", "/not_tmp/roms"]

RUN python3 -m retro.import /not_tmp/roms
RUN npx babel --presets @babel/react /not_tmp/application.js -o /not_tmp/application.js


WORKDIR /workfolder
