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
import owlready2
from owlready2 import *

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
active_emotions = ['happy', 'neutral', 'angry', 'sad']
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
ontology = None
patient = None
user = None


def init_ontology():
    global ontology, patient, user
    ontology = get_ontology("../ontologies/ontology.owl").load()
    with ontology:
        # init Patient
        patient = ontology.Patient(
            has_state=[ontology.State()],
            has_facial_expression=ontology.Emotion(type_of_emotion="none"),
            has_voice_expression=ontology.Emotion(type_of_emotion="none")
        )
        # init User
        user = ontology.User(
            has_preference_to_interact_with_interval=ontology.Time(in_seconds=10)
        )
        # init Emojis
        for emotion_type in dictgraphic.keys():
            for emoji_type in dictgraphic[emotion_type]:
                ontology.Emoji(type_of_emotion=emotion_type, type_of_emoji=emoji_type, usage_frequency=0)
        # Reason
        sync_reasoner()


def update_patient_expressions(facial_expression, voice_expression):
    global ontology, patient
    with ontology:
        if patient.has_facial_expression.type_of_emotion != facial_expression:
            patient.has_facial_expression.type_of_emotion = facial_expression
            sync_reasoner()
        if patient.has_voice_expression.type_of_emotion != voice_expression:
            patient.has_voice_expression.type_of_emotion = voice_expression
            sync_reasoner()

def get_emoji_from_emotion(emo):
    global ontology
    with ontology:
        if emo == "neutral":
            return ontology.search(type=ontology.NeutralEmoji)
        if emo == "happy":
            return ontology.search(type=ontology.HappyEmoji)
        if emo == "sad":
            return ontology.search(type=ontology.SadEmoji)
        if emo == "angry":
            return ontology.search(type=ontology.AngryEmoji)


def generate_emoji_list():
    global ontology, patient
    with ontology:
        facial_expression = patient.has_facial_expression.type_of_emotion
        voice_expression = patient.has_voice_expression.type_of_emotion
        if facial_expression == None or voice_expression == None:
            return []
        else:

            face_emojis = get_emoji_from_emotion(facial_expression)
            voice_emojis = get_emoji_from_emotion(voice_expression)

            emojis = []
            def sort_frequency(emoji):
                if emoji.usage_frequency != None:
                    return emoji.usage_frequency
                return 0

            if facial_expression != voice_expression:
                face_emojis.sort(key=sort_frequency, reverse=True)
                voice_emojis.sort(key=sort_frequency, reverse=True)
                frequent_emojis = face_emojis[:2].append(voice_emojis[:2])
                frequent_emojis.sort(key=sort_frequency, reverse=True)
                for emoji in frequent_emojis:
                    emojis.append(emoji.type_of_emoji)
            else:
                face_emojis.sort(key=sort_frequency, reverse=True)
                frequent_emojis = face_emojis[:4]
                for emoji in frequent_emojis:
                    emojis.append(emoji.type_of_emoji)

            return emojis


def update_emoji_frequency(emoji_type):
    global ontology
    with ontology:
        for emoji in ontology.Emoji.instances():
            if emoji.type_of_emoji == emoji_type:
                emoji.usage_frequency += 1
                print(emoji.usage_frequency)
                sync_reasoner()


def update_user_interaction_interval():
    global user
    if user.has_preference_to_interact_with_interval.in_seconds > 3:
        time = user.has_preference_to_interact_with_interval.in_seconds
        print("Current time interval: " + str(time))
        user.has_preference_to_interact_with_interval.in_seconds = time-1
        sync_reasoner()


@ app.route("/")
def index():
    print("index")
    global emotion, dictgraphic, start_time, time_interval, patient
    # return the rendered template
    with lock:
        emojis = generate_emoji_list()
    return render_template("index.html",
           emosh=patient.has_facial_expression.type_of_emotion,
           emoji=emojis,
           interval=user.has_preference_to_interact_with_interval.in_seconds)


@ app.route('/count', methods=['POST'])
def count():
    emoji = request.form['data']
    with lock:
        update_emoji_frequency(emoji)
        update_user_interaction_interval()
    return ('', 200)


def detect_emotion(frameCount):
    print("detect_emotion")

    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, outputFrame, emotion, patient, onto

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

        result = {key:value for (key,value) in result['emotion'].items() if key in active_emotions}
        emotion = max(result, key=lambda emotion: result[emotion])
        print(emotion)
        with lock:
            update_patient_expressions(emotion, emotion)


def generate():
    print("generate")

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
    print("response")

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

    # read and inits the ontology
    init_ontology()

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
