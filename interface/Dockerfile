
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
RUN pip3 install pandas


# ## ffmpeg
#
# RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes ffmpeg
#
#
# ## Spark
#
# RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes default-jdk \
#                                                          scala
#
# WORKDIR /downloads
# RUN apt-get install --yes curl
#
# RUN curl -LO https://archive.apache.org/dist/spark/spark-3.0.0/spark-3.0.0-bin-hadoop2.7.tgz
# RUN tar xvf spark-*
# RUN mv spark-3.0.0-bin-hadoop2.7 /opt/spark
#
# ENV SPARK_HOME=/opt/spark
# ENV PYSPARK_PYTHON=/usr/bin/python3
# ENV PATH="/opt/spark/bin:/opt/spark/sbin:${PATH}"
#
# ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-${py4j_version}-src.zip"
# # ENV SPARK_OPTS="--driver-java-options=-Xms1024M --driver-java-options=-Xmx4096M --driver-java-options=-Dlog4j.logLevel=info"
#
# RUN pip3 install pyspark
#
#
# ## Jupyter
#
# RUN pip3 install jupyter


## JSX

WORKDIR /server_directory

RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes nodejs \
                                                         npm

RUN npm install @babel/core @babel/cli @babel/preset-react
RUN npm install webpack webpack-cli

COPY static /tmp
COPY src .
COPY roms roms

RUN python3 -m retro.import roms
RUN npx babel --presets @babel/react application.js -o application.js
RUN npx webpack ./application.js --mode=development --output-path='.' --output-filename=application.js


ENV JUPYTER_TOKEN=token

WORKDIR /workfolder
