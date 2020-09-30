
#

FROM ubuntu:latest

RUN apt-get update


## Python

RUN apt-get install --yes python3
RUN apt-get install --yes python3-pip
RUN pip3 install --upgrade pip


## Jupyter, version with run button

RUN pip3 install jupyter

RUN pip3 uninstall --yes notebook
RUN pip3 install notebook==5.6.0 

RUN pip3 uninstall --yes tornado
RUN pip3 install tornado==5.1.1


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


## Spark

RUN apt-get install --yes curl

RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes default-jdk \
                                                         scala

WORKDIR /downloads
RUN curl -LO https://archive.apache.org/dist/spark/spark-3.0.0/spark-3.0.0-bin-hadoop2.7.tgz
RUN tar xvf spark-*
RUN mv spark-3.0.0-bin-hadoop2.7 /opt/spark

ENV SPARK_HOME=/opt/spark
ENV PYSPARK_PYTHON=/usr/bin/python3
ENV PATH="/opt/spark/bin:/opt/spark/sbin:${PATH}"

ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-${py4j_version}-src.zip"
# ENV SPARK_OPTS="--driver-java-options=-Xms1024M --driver-java-options=-Xmx4096M --driver-java-options=-Dlog4j.logLevel=info"

RUN pip3 install pyspark


## JSX

WORKDIR /nodefolder
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install --yes nodejs

RUN npm install --save-dev @babel/core @babel/cli @babel/preset-env @babel/preset-react

RUN mkdir /not_tmp
COPY ["static", "/tmp/"]
COPY ["src/", "/not_tmp/"]
COPY ["roms", "/not_tmp/roms"]

RUN python3 -m retro.import /not_tmp/roms
# RUN npx babel --presets @babel/env,@babel/react /not_tmp/application.js -o /not_tmp/application.js
RUN npx babel --presets @babel/react /not_tmp/application.js -o /not_tmp/application.js


WORKDIR /workfolder
