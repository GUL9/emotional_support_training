import owlready2
owlready2.JAVA_EXE = "C:\Coding\programs\java\bin"
from owlready2 import *
onto = get_ontology("ontology.owl").load()




with onto:
    face_module = onto.FaceModule()
    face_module_state = onto.State()
    face_module.has_current = [face_module_state]

    voice_module = onto.VoiceModule()
    voice_module_state = onto.State()
    voice_module.has_current = [voice_module_state]

    input_module = onto.InputModule()
    input_module_state = onto.State()
    input_module.has_current = [input_module_state]


    patient = onto.Patient()
    patient_state = onto.State()


    sync_reasoner(keep_tmp_file = True)
