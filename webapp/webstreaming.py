# base code from Adrian Rosebrock's tutorial on Motion Detection: https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/

# import the necessary packages
from imutils.video import VideoStream
from flask import Response, Flask, render_template, request, redirect, url_for, jsonify
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
import pyaudio
import os
import wave
import pickle
import time
from sys import byteorder
from array import array
from struct import pack
from sklearn.neural_network import MLPClassifier

# import pickle
# import speechRecognition.test as test
# import speechRecognition.utils as utils

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)


outputFrame = None
lock = threading.Lock()
ontology_lock = threading.Lock()
# initialize a flask object
app = Flask(__name__)
# initialize the video stream and allow the camera sensor to
# warmup for 2 seconds
# vs = VideoStream(usePiCamera=1).start()
vs = VideoStream(src=0).start()
time.sleep(2.0)

time_interval = 5000

# VOICE_MODEL = pickle.load(
#     open("speechRecognition/result/mlp_classifier.model", "rb"))
PATH_TO_ONTOLOGY = "ontologies/ontology.owl"
PATH_TO_SAVE_REASONED_ONTOLOGY = "ontologies/saved.owl"

#PATH_TO_SOUND_FILE = "sound/soundfile.wav"
should_classify_voice = False
should_classify_face = False
# Time intervals
DEFAULT_TIME_INTERVAL = 5000
MAX_TIME_INTERVAL = 30000
MIN_TIME_INTERVAL = 3000
DISMISS_TIME_CHANGE = 5000
EMOJI_TIME_CHANGE = 1000
# User actions
EMOJI = "emoji"
DISMISS = "dismiss"
active_user_actions = [EMOJI, DISMISS]
# Emotions
NEUTRAL = "neutral"
HAPPY = "happy"
ANGRY = "angry"
SAD = "sad"
active_emotions = [NEUTRAL, HAPPY, ANGRY, SAD]
active_emojis = {
    HAPPY: ['😊', '😃', '😄', '😁', '😆', '😉'],
    ANGRY: ['😤', '😠', '😡', '🤬', '😒', '😣'],
    SAD: ['😔', '😢', '😭', '😟', '😥', '🥺'],
    NEUTRAL: ['🙂', '😐', '🧐', '😑', '🧑', '👩'],
}
# Ontology globals
ontology = None
patient = None
user = None


def init_ontology():
    global ontology, patient, user
    ontology = get_ontology(PATH_TO_ONTOLOGY).load()
    with ontology:
        # init Patient: neutral expressions
        patient = ontology.Patient(
            has_state=[ontology.State()],
            has_facial_expression=ontology.Emotion(type_of_emotion=NEUTRAL),
            has_voice_expression=ontology.Emotion(type_of_emotion=NEUTRAL)
        )
        # init User: default time interval
        user = ontology.User(has_preference_to_interact_with_interval=ontology.Time(
            in_seconds=DEFAULT_TIME_INTERVAL))
        # init Emojis: corresponding emotion type and 0 frequency
        for emotion_type in active_emojis.keys():
            for emoji_type in active_emojis[emotion_type]:
                ontology.Emoji(type_of_emotion=emotion_type,
                               type_of_emoji=emoji_type, usage_frequency=0)
        # Reason
        ontology.save(PATH_TO_SAVE_REASONED_ONTOLOGY)
        sync_reasoner()


def update_patient_facial_expressions(facial_expression):
    # Update if expression has changed; reason if updated
    global ontology, patient
    with ontology:
        if patient.has_facial_expression.type_of_emotion != facial_expression:
            patient.has_facial_expression.type_of_emotion = facial_expression
            sync_reasoner()
            ontology.save("ontologies/saved.owl")


# def update_patient_voice_expressions(voice_expression):
#     # Update if expression has changed; reason if updated
#     global ontology, patient
#     with ontology:
#         if patient.has_voice_expression.type_of_emotion != voice_expression:
#             patient.has_voice_expression.type_of_emotion = voice_expression
#             sync_reasoner()
#             ontology.save("ontologies/saved.owl")


def get_emoji_from_emotion(emotion):
    # Returns list of all Emoji-instances for given emotion
    global ontology
    with ontology:
        if emotion == NEUTRAL:
            return ontology.search(type=ontology.NeutralEmoji)
        if emotion == HAPPY:
            return ontology.search(type=ontology.HappyEmoji)
        if emotion == SAD:
            return ontology.search(type=ontology.SadEmoji)
        if emotion == ANGRY:
            return ontology.search(type=ontology.AngryEmoji)


def generate_emoji_list():
    # Returns list of Emojis (string representation);
    # Total 4 emojis; 2 from facial expression, 2 from voice expression
    global ontology, patient
    with ontology:
        facial_expression = patient.has_facial_expression.type_of_emotion
        #voice_expression = patient.has_voice_expression.type_of_emotion
        # Get all emojis of corresponding expressions
        face_emojis = get_emoji_from_emotion(facial_expression)
        #voice_emojis = get_emoji_from_emotion(voice_expression)

        emojis = []

        def sort_frequency(emoji):
            if emoji.usage_frequency != None:
                return emoji.usage_frequency
            return 0
        # When expressions differ; pick 2 from each
        # if facial_expression != voice_expression:
        #     face_emojis.sort(key=sort_frequency, reverse=True)
        #     voice_emojis.sort(key=sort_frequency, reverse=True)
        #     frequent_emojis = face_emojis[:2]+voice_emojis[:2]
        #     frequent_emojis.sort(key=sort_frequency, reverse=True)
        #     for emoji in frequent_emojis:
        #         emojis.append(emoji.type_of_emoji)
        # # When expressions are the same; pick 4 from one
        # else:
        face_emojis.sort(key=sort_frequency, reverse=True)
        frequent_emojis = face_emojis[:4]
        for emoji in frequent_emojis:
            emojis.append(emoji.type_of_emoji)

        return emojis


def update_emoji_frequency(emoji_type):
    # Increment usage frequency for given emoji type
    global ontology
    with ontology:
        for emoji in ontology.Emoji.instances():
            if emoji.type_of_emoji in emoji_type:
                emoji.usage_frequency += 1
                # print("Usage Frequency for" + emoji_type +
                #       str(emoji.usage_frequency))
                sync_reasoner()
                ontology.save("ontologies/saved.owl")


def update_user_interaction_interval(input_type):
    # Increment or decrement interaction time interval
    global user
    if input_type == EMOJI:
        if user.has_preference_to_interact_with_interval.in_seconds > MIN_TIME_INTERVAL:
            user.has_preference_to_interact_with_interval.in_seconds -= EMOJI_TIME_CHANGE

    if input_type == DISMISS:
        if user.has_preference_to_interact_with_interval.in_seconds < MAX_TIME_INTERVAL:
            user.has_preference_to_interact_with_interval.in_seconds += DISMISS_TIME_CHANGE

    sync_reasoner()
    ontology.save("ontologies/saved.owl")
    # print("Current time interval: " +
    #       str(user.has_preference_to_interact_with_interval.in_seconds))


@ app.route("/")
def index():
    global patient, user, ontology_lock
    # return the rendered template
    with ontology_lock:
        emojis = generate_emoji_list()
    return render_template("index.html",
                           face=patient.has_facial_expression.type_of_emotion,
                           voice=patient.has_voice_expression.type_of_emotion,
                           emojis=emojis,
                           interval=user.has_preference_to_interact_with_interval.in_seconds)


@ app.route('/count', methods=['POST'])
def count():
    emoji = request.form['data']
    with ontology:
        update_emoji_frequency(emoji)
        update_user_interaction_interval(EMOJI)
    return ('', 200)


@ app.route('/dismiss', methods=['POST'])
def dismiss():
    global ontology_lock
    with ontology_lock:
        update_user_interaction_interval(DISMISS)
    return ('', 200)


# def detect_voice_expression():
#     global user, ontology_lock
#     while True:
#         # Record to file until nex interval
#         # print("Starting voice classification")
#         with ontology_lock:
#             record_time = user.has_preference_to_interact_with_interval.in_seconds/1000 - 0.2
#         test.record_to_file(PATH_TO_SOUND_FILE, record_time)
#         features = utils.extract_feature(
#             PATH_TO_SOUND_FILE, mfcc=True, chroma=True, mel=True).reshape(1, -1)
#         emotion = str(VOICE_MODEL.predict(features)[0])
#         # print("Voice: " + emotion)

#         with ontology_lock:
#             update_patient_voice_expressions(emotion)


def detect_face_expression(frameCount):
    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, outputFrame,  patient, ontology_lock

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
        # Get current user interaction interval time
        with ontology_lock:
            accumulation_time = user.has_preference_to_interact_with_interval.in_seconds/1000 - 0.2
        stop_time = time.time() + accumulation_time
        # print("Starting face classification")
        # Accumulate emotion scores until next interaction
        accumulation = DeepFace.analyze(
            outputFrame, actions=['emotion'], enforce_detection=False)['emotion']
        while time.time() < stop_time:
            result = DeepFace.analyze(outputFrame, actions=[
                                      'emotion'], enforce_detection=False)['emotion']
            for emotion in result.keys():
                accumulation[emotion] += result[emotion]
        # Update facial expression with the emotion with highest score during the accumulation time
        result = {key: value for (
            key, value) in accumulation.items() if key in active_emotions}
        emotion = max(result, key=lambda emotion: result[emotion])
        # print("Face: " + emotion)
        with ontology_lock:
            update_patient_facial_expressions(emotion)


def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

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


@app.route('/_update', methods=['GET'])
def update():
    global patient, user, ontology_lock
    with ontology_lock:
        emojis = generate_emoji_list()
    return jsonify(face=patient.has_facial_expression.type_of_emotion,
                   voice=patient.has_voice_expression.type_of_emotion,
                   emojis=emojis,
                   interval=user.has_preference_to_interact_with_interval.in_seconds)


@ app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@ app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # construct the argument parser and parse command line arguments

    # ap = argparse.ArgumentParser()
    # ap.add_argument("-i", "--ip", type=str, required=True,
    #                 help="ip address of the device")
    # ap.add_argument("-o", "--port", type=int, required=True,
    #                 help="ephemeral port number of the server (1024 to 65535)")
    # ap.add_argument("-f", "--frame-count", type=int, default=32,
    #                 help="# of frames used to construct the background model")
    # args = vars(ap.parse_args())
    

    # read and init the ontology
    init_ontology()

    # start face emotion detection thread
    face_thread = threading.Thread(
        target=detect_face_expression, args=(32,))
    face_thread.daemon = True
    face_thread.start()
    # # start voice emotion detection thread
    # voice_thread = threading.Thread(target=detect_voice_expression)
    # voice_thread.daemon = True
    # voice_thread.start()

    # # start the flask app
    # app.run(host=args["ip"], port=args["port"], debug=True,
    #         threaded=True, use_reloader=False)
    
    # start the flask app
    app.run(host='0.0.0.0', port='8000', debug=True,
            threaded=True, use_reloader=False)
    
# release the video stream pointer
vs.stop()
