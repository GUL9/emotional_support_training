import owlready2
from owlready2 import *
onto = get_ontology("ontologies/ontology.owl").load()

with onto:
    # Patient setup
    patient = onto.Patient()
    facial_expression = onto.Emotion()

    patient.has_facial_expression = [onto.Emotion()]
    user = onto.User()




