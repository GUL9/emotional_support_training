import owlready2
from owlready2 import *
onto = get_ontology("ontologies/ontology.owl").load()

with onto:
    # Patient setup
    patient = onto.Patient()
    patient_state = onto.State()
    facial_expression = onto.Emotion()
    voice_expression = onto.Emotion()

    patient.has_state.append(patient_state)
    #patient.has_facial_expression.append(facial_expression)


    # User setup
    user = onto.User()






