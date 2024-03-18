import hashlib
from openai import OpenAI
import json
import pickle
from pathlib import Path
from enum import Enum
client = OpenAI()

# MODEL="gpt-4-0125-preview"
MODEL="gpt-3.5-turbo-0125"

# checks if two things are the same:
def isSame(a: str, b: str) -> bool:
    
    userPrompt = f"""Is {a} the same as {b}?"""
    prompts = [
        {"role": "system", "content": "For the following question, respond with 'yes' or 'no'"},
        {"role": "user", "content": userPrompt},
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=prompts,
    )
    print(userPrompt+": "+response.choices[0].message.content)
    if response.choices[0].message.content.lower() == "yes":
        return True
    else:
        return False

# checks if one thing is a subset of the other:
# all giraffes are animals
# not all animals are giraffes
def isSubset(subset: str, superset: str) -> bool:
    userPrompt = f"""Is {subset} a subset of {superset}?"""
    prompts = [
        {"role": "system", "content": "For the following question, respond with 'yes' or 'no'"},
        {"role": "user", "content": userPrompt},
    ]
    # print(prompts)
    response = client.chat.completions.create(
        model=MODEL,
        messages=prompts,
    )
    print(userPrompt+": "+response.choices[0].message.content)
    if response.choices[0].message.content.lower() == "yes":
        return True
    else:
        return False


class LLMEnum(Enum):
    # container to parse the enum responses from the LLM:
    # LLMLookup : dict
    # base case if enum cannot be parsed:
    # ERROR = 0
    _llmLookup : dict
    def __str__(self):
        return self.name

    @classmethod
    def _missing_(cls, value : str):
        index = cls._llmLookup.value.get(value)
        if index is None:
            for key in cls._llmLookup.value.keys():
                if cacheDict("cache",True, isSame, key, value.lower()):
                    index = cls._llmLookup.value[key]
                    break
        if index is None:
            index = 0
        return cls(index)

class PointOfViewType(LLMEnum):
    _llmLookup = {
        "first person": 1,
        "second person": 2,
        "third person limited": 3,
        "third person omniscient": 4
    }
    ERROR = 0
    FIRST_PERSON = 1
    SECOND_PERSON = 2
    THIRD_PERSON_LIMITED = 3
    THIRD_PERSON_OMNISCIENT = 4

test = PointOfViewType.FIRST_PERSON
test2 = PointOfViewType("first person")
test3 = PointOfViewType("1st person")
test4 = PointOfViewType("orange")

def insertParagraphID(text: str):
    text = text.split("\n\n")
    # prepend id for each paragraph:
    for i in range(len(text)):
        text[i] = str(i) + ": " + text[i]

    return text


def annotateSpeaker(paragraphs: list[str], possibleCharacters: list[str] = []):
    text = "\n\n".join(paragraphs)
    systemPrompt = """Parse the following scene and annotate the speaker for each paragraph. Return the output as json in the form of:
{
    'paragraphs': [
        {paragraphID: 'Paragraph ID number', speaker: 'speaker'},
        {paragraphID: 'Paragraph ID number', speaker: 'speaker2'}
    ]
}
"""
    if len(possibleCharacters) > 0:
        systemPrompt = systemPrompt + f"Possible speakers: {', '.join(possibleCharacters)}"

    prompts = [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": text},
    ]
    print(prompts)
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=prompts,
    )
    print(response.choices[0].message.content)
    return json.loads(response.choices[0].message.content)


def summerizeScene(paragraphs: str):
    text = "\n\n".join(paragraphs)

    systemPrompt = """Parse the following scenes, return the output as json in the form of:
{
    'scenes':[{
        'startID': 'Paragraph ID of the start of the scene',
        'sceneSummary': 'short paragraph summarizing the scene',
        'characters': [character1, character2, character3],
        'PointOfViewType': 'The point of view writing style of the scene',
        'pointOfView': 'character1'
        'setting': 'location'
    }]
}
"""
    prompts = [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": text},
    ]
    # print(prompts)
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=prompts,
    )
    print(response.choices[0].message.content)
    # convert json to dictionary and return:
    data = json.loads(response.choices[0].message.content)
    return data

def stableDictHash(x):
    return hashlib.sha224(json.dumps(x, sort_keys=True).encode(encoding = 'UTF-8', errors = 'strict')).hexdigest()

def cacheDict(root: Path, cache: bool, function: callable, *args, **kwargs):
    if root.exists() == False:
        root.mkdir()
    data = None
    name = stableDictHash({"args": args, "kwargs" : kwargs, "function": function.__name__})
    filepath = root.joinpath(name + ".pkl")
    if cache and filepath.exists():
        with open(filepath, "rb") as file:
            data = pickle.load(file)
            # print(f"loaded from cache {data}")
    else:
        data = function(*args, **kwargs)
        # data = {"test":1}
        pickle.dump(data, open(filepath, "wb"))
    return data

def jsonPrint(x : dict):
    print(json.dumps(x, indent=4))

def annotateDocument(directory, name, data, annotatedSceneList):
    # create directory if it doesn't exist:
    if directory.exists() == False:
        directory.mkdir()
    # create a file for each document:
    
    documentFile = directory.joinpath(name + ".txt")
    with open(documentFile, "w") as file:
        nextSceneIndex = 0
        currentSceneIndex = -1
        for i in range(len(data)):
            if  nextSceneIndex < len(annotatedSceneList):
                if i == int(annotatedSceneList[nextSceneIndex]["scene"]["startID"]):
                    file.write(f"Scene: {annotatedSceneList[nextSceneIndex]['scene']['sceneSummary']}\n")
                    file.write(f"Characters: {', '.join(annotatedSceneList[nextSceneIndex]['scene']['characters'])}\n")
                    file.write(f"Point of View: {annotatedSceneList[nextSceneIndex]['scene']['pointOfView']}\n")
                    file.write(f"Setting: {annotatedSceneList[nextSceneIndex]['scene']['setting']}\n")
                    file.write("\n")
                    currentSceneIndex = nextSceneIndex
                    nextSceneIndex += 1
            if currentSceneIndex != -1: # we are initialized.
                if annotatedSceneList[currentSceneIndex]["annotations"].get(str(i)) is not None:
                    file.write(f"Speaker: {annotatedSceneList[currentSceneIndex]['annotations'][str(i)]}\n")
            file.write(data[i] + "\n\n")




# isSame("giraffe", "elephant")
# isSame("love", "lust")
# isSame("third person", "third person limited")
# isSubset("giraffe", "animal")
# isSubset("animal", "giraffe")
# isSubset("third person limited", "third person limited")
# isSubset("third person omniscient", "third person limited")
# isSubset("third person limited", "third person")
quit()

# read in a text file in same directory:
# testStory = "partofthesystem.txt"
testStory = "Dusty.txt"
cache = False
cacheRoot = Path("cache")

annotatedDirectory = Path("annotated")

# testStory = "Dusty.txt"
with open(testStory, "r") as file:
    # convert to list of paragraphs with id's:
    data = insertParagraphID(file.read())
    # print(data)
    resp = cacheDict(cacheRoot, cache, summerizeScene, data)

    jsonPrint(resp)

    sortedScenes = sorted(resp["scenes"], key=lambda x: int(x["startID"]))

    # quit()
    # stop id is not reliable, assume all one scene, and work backwards.
    previousSceneStart = None
    annotatedSceneList = []
    for scene in reversed(sortedScenes):
        annotations = cacheDict(
            cacheRoot,
            cache,
            annotateSpeaker,
            data[int(scene["startID"]) : previousSceneStart],
            scene["characters"]
        )
        # add stopID to scene:
        if previousSceneStart is not None:
            scene["stopID"] = previousSceneStart
        else:
            scene["stopID"] = len(data)
        previousSceneStart = int(scene["startID"])
        # from the list of annotated paragraphs, build up a dictionary of annotated paragraphs:
        annotationDict = {}
        for annotation in annotations['paragraphs']:
            annotationDict[annotation['paragraphID']] = annotation['speaker']
        annotatedSceneList.append({"scene" : scene, "annotations" : annotationDict})
    annotatedSceneList = list(reversed(annotatedSceneList))
    
    annotateDocument(annotatedDirectory, testStory, data, annotatedSceneList)


    # annotateSpeaker(data[0:11])
    # verify correctness:
