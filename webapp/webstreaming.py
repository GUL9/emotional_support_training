# base code from Adrian Rosebrock's tutorial on Motion Detection: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/

# import the necessary packages
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for
import threading
import argparse
import datetime
import imutils
import time
import cv2
from deepface import DeepFace
import random
import atexit

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
time_interval = 10
start_time = 0
outputFrame = None
lock = threading.Lock()
# initialize a flask object
app = Flask(__name__)
# initialize the video stream and allow the camera sensor to
# warmup for 2 seconds
# vs = VideoStream(usePiCamera=1).start()
vs = VideoStream(src=0).start()
time.sleep(2.0)
emotion = 'emosh'
dictgraphic = {'emosh': ['🙃'],
               'happy': ['😊', '😃', '😄', '😁', '😆', '😉'],
               'angry': ['😤', '😠', '😡', '🤬', '😒', '😣'],
               'sad': ['☹️', '😢', '😭', '😟', '😥'],
               'neutral': ['🙂', '😐', '🧐', '😑'],
               'disgust': ['🤢', '🤮', '😣', '😖'],
               'fear': ['😨', '😰', '😥', '😓'],
               'surprise': ['😱']}
counter = {'🙃': 0,
           '😊': 0,
           '😃': 0,
           '😄': 0,
           '😁': 0,
           '😆': 0,
           '😉': 0,
           '😤': 0,
           '😠': 0,
           '😡': 0,
           '🤬': 0,
           '😒': 0,
           '😣': 0,
           '☹️': 0,
           '😢': 0,
           '😭': 0,
           '😟': 0,
           '😥': 0,
           '🙂': 0,
           '😐': 0,
           '🧐': 0,
           '😑': 0,
           '🤢': 0,
           '🤮': 0,
           '😣': 0,
           '😖': 0,
           '😨': 0,
           '😰': 0,
           '😥': 0,
           '😓': 0,
           '😱': 0}


@ app.route("/")
def index():
    global emotion, dictgraphic, start_time, time_interval
    # return the rendered template
    return render_template("index.html", emosh=emotion, emoji=sorted(dictgraphic[emotion], key=counter.get, reverse=True), interval=time_interval)


@ app.route('/count', methods=['POST'])
def count():
    global time_interval
    id = request.form['data']
    counter[id.strip()] += 1
    if time_interval > 5:
        time_interval -= 1
    return ('', 200)


def detect_emotion(frameCount):
    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, outputFrame, emotion

    with lock:
        # check if the output frame is available, otherwise skip
        # the iteration of the loop
        if outputFrame is None:
            frame = vs.read()
            frame = imutils.resize(frame, width=400)
            outputFrame = frame.copy()

    # total = 0
    # loop over frames from the video stream
    while True:
        # Our operations on the current output frame come here
        result = DeepFace.analyze(
            outputFrame, actions=['emotion'], enforce_detection=False)

        # # print(result)
        emotion = max(result['emotion'], key=result['emotion'].get)


def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock, time_interval, start_time

    # loop over frames from the output stream
    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        outputFrame = frame.copy()
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')


@ app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@ app.route('/response')
def response():
    global emotion, dictgraphic, time_interval
    return render_template("index.html", emosh=emotion, emoji=sorted(dictgraphic[emotion], key=counter.get, reverse=True), interval=time_interval)


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # construct the argument parser and parse command line arguments

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True,
                    help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,
                    help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=32,
                    help="# of frames used to construct the background model")
    args = vars(ap.parse_args())
    # start a thread that will perform emotion detection
    t = threading.Thread(target=detect_emotion, args=(
        args["frame_count"],))
    t.daemon = True
    t.start()

    # start the flask app
    app.run(host=args["ip"], port=args["port"], debug=True,
            threaded=True, use_reloader=False)

# release the video stream pointer
vs.stop()
