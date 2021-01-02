
###############################################################################
FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 -y
RUN apt-get install python3.7 python3.7-dev python3-pip -y
RUN python3.7 -m pip install pyaudio==0.2.11
CMD python3.7 -c "import pyaudio"
