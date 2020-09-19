
#

FROM ubuntu:latest

RUN apt-get update

RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip

RUN pip3 install jupyter

RUN pip3 uninstall --yes notebook
RUN pip3 install notebook==5.6.0 

RUN pip3 uninstall --yes tornado
RUN pip3 install tornado==5.1.1

## RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg
## RUN pip install sk-video
## RUN pip3 install Pillow
## RUN pip3 install scikit-image

RUN pip3 install torch
RUN pip3 install torchvision

RUN apt-get install --yes xvfb
RUN apt-get install --yes python-opengl
RUN pip3 install gym-retro

RUN pip3 install matplotlib

RUN pip3 install scikit-learn



## SPARK

RUN apt-get install --yes curl

RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes default-jdk \
                                                         scala

RUN java --version

WORKDIR /downloads
RUN curl -LO https://archive.apache.org/dist/spark/spark-3.0.0/spark-3.0.0-bin-hadoop2.7.tgz
RUN tar xvf spark-*
RUN mv spark-3.0.0-bin-hadoop2.7 /opt/spark

ENV SPARK_HOME=/opt/spark
ENV PYSPARK_PYTHON=/usr/bin/python3
ENV PATH="/opt/spark/bin:/opt/spark/sbin:${PATH}"
# echo "export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin" >> ~/.profile
# echo "export PYSPARK_PYTHON=/usr/bin/python3" >> ~/.profile

# RUN /opt/spark/sbin/start-master.sh

ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-${py4j_version}-src.zip"
# ENV SPARK_OPTS="--driver-java-options=-Xms1024M --driver-java-options=-Xmx4096M --driver-java-options=-Dlog4j.logLevel=info"

RUN pip3 install pyspark

WORKDIR /workfolder

# RUN Xvfb :99 &
# ENV DISPLAY=:99

COPY ["roms", "/workfolder"]

RUN python3 -m retro.import /workfolder

ENV JUPYTER_TOKEN=token

# ENTRYPOINT ["/bin/bash", "-c", "DISPLAY=:99 jupyter notebook --ip=0.0.0.0 --allow-root"]
# ENTRYPOINT ["/bin/bash", "-c", "xvfb-run jupyter notebook --ip=0.0.0.0 --allow-root"]
