
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

RUN pip install matplotlib

WORKDIR /workfolder

# RUN Xvfb :99 &
# ENV DISPLAY=:99

COPY ["Super Mario Bros..nes", "/workfolder"]

RUN python3 -m retro.import /workfolder

ENV JUPYTER_TOKEN=token

# ENTRYPOINT ["/bin/bash", "-c", "DISPLAY=:99 jupyter notebook --ip=0.0.0.0 --allow-root"]
# ENTRYPOINT ["/bin/bash", "-c", "xvfb-run jupyter notebook --ip=0.0.0.0 --allow-root"]
