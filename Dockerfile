FROM nvcr.io/nvidia/cuda:10.0-cudnn7-runtime-ubuntu18.04

RUN DEBIAN_FRONTEND=noninteractive apt-get -qq update \
 && DEBIAN_FRONTEND=noninteractive apt-get -qqy install python3-pip ffmpeg git less nano libsm6 libxext6 libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN pip3 install \
  https://download.pytorch.org/whl/cu100/torch-1.0.0-cp36-cp36m-linux_x86_64.whl \
  -r requirements.txt


ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV MODEL=/app/vox.pt
ENV DRIVING_VIDEO=/app/driving.mp4

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt-get install python3-tk -y

COPY . /app/