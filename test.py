import owlready2
from owlready2 import *
onto = get_ontology("ontologies/ontology.owl").load()

with onto:
    patient = onto.Patient()
    user = onto.User()

