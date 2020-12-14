import owlready2
from owlready2 import *
onto = get_ontology("ontologies/ontology.owl").load()

with onto:
    # Patient setup

    # Emoji
    emojis = []
    dictgraphic = {'emosh': ['🙃'],
                   'happy': ['😊', '😃', '😄', '😁', '😆', '😉'],
                   'angry': ['😤', '😠', '😡', '🤬', '😒', '😣'],
                   'sad': ['☹️', '😢', '😭', '😟', '😥'],
                   'neutral': ['🙂', '😐', '🧐', '😑'],
                   'disgust': ['🤢', '🤮', '😣', '😖'],
                   'fear': ['😨', '😰', '😥', '😓'],
                   'surprise': ['😱']}
    for emotion in dictgraphic:
        for emoji in dictgraphic[emotion]:
            emojis.append(onto.Emoji(type_of_emotion=emotion,
                                     type_of_emoji=emoji,
                                     usage_frequency=0))

    sync_reasoner()

    for instance in onto.Emoji.instances():
        print(instance.type_of_emotion)





