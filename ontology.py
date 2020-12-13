import owlready2
owlready2.JAVA_EXE = "C:\Coding\programs\java\bin"
from owlready2 import *
onto = get_ontology("core.owl").load()

with onto:



    #Classes

    # Emotions
    class Emotion(Thing):
        pass
    class Sadness(Emotion):
        pass
    class Happiness(Emotion):
        pass
    class Anger(Emotion):
        pass
    class Neutral(Emotion):
        pass

    # States
    class State(Thing):
        def state_status(self): print("I have a status")
        pass

    class has_emotion(Thing >> Emotion):
        pass

    class ClassificationsReadySteat(State):
        equvalent_to = [State & has_emotion.min(1, Emotion)]
        def state_status(self): print("Classification Ready")
        pass
    class ClassificationsNotReadySteat(State):
        equvalent_to = [State & Not(has_emotion.some(Emotion))]
        def state_status(self): print("Classification Not Ready")
        pass

    class Module(Thing):
        pass
    class FaceModule(Module):
        pass
    class VoiceModule(Module):
        pass
    class InputModule(Module):
        pass
    class Classification(Thing):
        pass

    #ObjectProperties
    class has_current(Thing >> State):
        pass

    #DataProperties
    sadness = Sadness()
    happiness = Happiness()
    anger = Anger()
    neutral = Neutral()


    face_module = FaceModule()
    voice_module = VoiceModule()
    input_module = InputModule()

    face_state = State()
    face_state.has_emotion = [sadness]
    face_module.has_current = [face_state]

    voice_state = State()
    voice_module.has_current = [voice_state]

    print(face_state.has_emotion)
    face_state.state_status()
    close_world(Module)
    sync_reasoner()
