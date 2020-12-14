import owlready2
from owlready2 import *
onto = get_ontology("ontologies/ontology.owl").load()

with onto:
    # Patient setup
    patient = onto.Patient()
    patient_state = onto.State()
    facial_expression = onto.Emotion()
    facial_expression.type_of_emotion.append("happiness")
    voice_expression = onto.Emotion()

    patient.has_state.append(patient_state)
    patient.has_facial_expression.append(facial_expression)

    # User setup
    start_interval = 0
    time = onto.Time()
    time.in_seconds.append(start_interval)
    user = onto.User()
    user.has_preference_to_interact_in.append(time)
    user_state = onto.User()
    user.has_state.append(user_state)

    for instance in onto.WantInteraction.instances():
        print("hej")

    for instance in onto.ExpressingEmotion.instances():
        print("heja")



