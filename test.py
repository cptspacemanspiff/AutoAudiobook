import hashlib
import json
from pathlib import Path
from enum import Enum

from utils.cache import cacheDict
from utils.fuzzy_parsing import LLMEnum
import scene_analyzer

from config import CACHE, CACHE_DIRECTORY, client, MODEL

def jsonPrint(x: dict):
    print(json.dumps(x, indent=4))


# test = PointOfViewType.FIRST_PERSON
# test2 = PointOfViewType("first person")
# test3 = PointOfViewType("1st person")
# test4 = PointOfViewType("orange")


# isSame("giraffe", "elephant")
# isSame("love", "lust")
# isSame("third person", "third person limited")
# isSubset("giraffe", "animal")
# isSubset("animal", "giraffe")
# isSubset("third person limited", "third person limited")
# isSubset("third person omniscient", "third person limited")
# isSubset("third person limited", "third person")

# read in a text file in same directory:
testStory = "partofthesystem.txt"
# testStory = "Dusty.txt"

annotatedDirectory = Path("annotated")

# testStory = "Dusty.txt"
with open(testStory, "r") as file:
    # convert to list of paragraphs with id's:
    data = scene_analyzer.insertParagraphID(file.read())
    # print(data)
    # resp = cacheDict(CACHE_DIRECTORY, CACHE, scene_analyzer.summerizeScene, data)

    # jsonPrint(resp)

    # sortedScenes = sorted(resp["scenes"], key=lambda x: int(x["startID"]))
    
    systemPrompt = """Read the following story excerpts, and identify line breaks.
    
"""

    prompts = [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": "\n\n".join(data)},
    ]
    # print(prompts)
    response = client.chat.completions.create(
        model = "gpt-3.5-turbo-0125",
        response_format={"type": "json_object"},
        messages=prompts,
        n=3

    )
    for each in response.choices:
        print(each.message.content)
    quit()


    # add stopID to the scene:
    previousSceneStart = None
    for scene in reversed(sortedScenes):
        if previousSceneStart is not None:
            scene["stopID"] = previousSceneStart
        else:
            scene["stopID"] = len(data)
        previousSceneStart = int(scene["startID"])

    # add sceneID    
    sceneID = 0
    for scene in sortedScenes:
        scene["sceneID"] = sceneID
        sceneID += 1

    # Work forward through the scenes and build up character relationship tables.
    for scene in sortedScenes:
        for character in scene['characters']:
            annotations = cacheDict(
                CACHE_DIRECTORY,
                CACHE,
                scene_analyzer.identifyCharacter,
                data[int(scene["startID"]) : int(scene["stopID"])],
                scene,
                character
            )
        




    quit()
    # stop id is not reliable, assume all one scene, and work backwards.
    annotatedSceneList = []
    for scene in sortedScenes:
        annotations = cacheDict(
            CACHE_DIRECTORY,
            CACHE,
            scene_analyzer.annotateSpeaker,
            data[int(scene["startID"]) : previousSceneStart],
            scene,
        )
        # from the list of annotated paragraphs, build up a dictionary of annotated paragraphs:
        annotationDict = {}
        for annotation in annotations["paragraphs"]:
            annotationDict[annotation["paragraphID"]] = annotation["speaker"]
        annotatedSceneList.append({"scene": scene, "annotations": annotationDict})
        break
    annotatedSceneList = list(reversed(annotatedSceneList))

    scene_analyzer.annotateDocument(
        annotatedDirectory, testStory, data, annotatedSceneList
    )

    # annotateSpeaker(data[0:11])
    # verify correctness:
