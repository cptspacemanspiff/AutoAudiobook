from config import MODEL, client
import json
from pathlib import Path

from utils.fuzzy_parsing import LLMEnum


# Data Types:
class PointOfViewType(LLMEnum):
    _llmLookup = {
        "first person": 1,
        "second person": 2,
        "third person limited": 3,
        "third person omniscient": 4,
    }
    ERROR = 0
    FIRST_PERSON = 1
    SECOND_PERSON = 2
    THIRD_PERSON_LIMITED = 3
    THIRD_PERSON_OMNISCIENT = 4

def splitSections(text: str):
    # split the text into sections:
    paragraphs = text.split("\n\n")

    # determine if there is a scene change:
    for i in range(len(paragraphs)):
        
    return sections

def insertParagraphID(text: str):
    text = text.split("\n\n")
    # prepend id for each paragraph:
    for i in range(len(text)):
        text[i] = str(i) + ": " + text[i]

    return text

def identifyCharacter(paragraphs: list[str], scene, character1):
    text = "\n\n".join(paragraphs)

    systemPrompt = f"The following is a brief scene in a story, analyze who {character1} is in the context of the scene, respond in json"
    systemPrompt +="""
{
    'aliases' : '[alias1, alias2, alias3]'
    'purpose' : 'what is the character doing in the scene'
    'emotionalState' : 'what is the character feeling in the scene'
    'importance' : 'is the character a major, minor, or background character'
}
"""
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


def analyzeRelation(paragraphs: list[str], scene, character1, character2):
    text = "\n\n".join(paragraphs)

    systemPrompt = "Read the following story what is the relationship between {character1} and {character2}, respond in json."
# """
# {
#     'knows': "1 to 2 sentences describing the relationship"
# }
# """

    # systemPrompt = (
    #     systemPrompt
    #     + f"The story is written in {scene['pointOfViewType']} and the narrator is {scene['pointOfView']}"
    # )

    # prompts = [
    #     {"role": "system", "content": systemPrompt},
    #     {"role": "user", "content": text},
    # ]
    # print(prompts)
    # response = client.chat.completions.create(
    #     model=MODEL,
    #     response_format={"type": "json_object"},
    #     messages=prompts,
    # )
    # print(response.choices[0].message.content)
    # return json.loads(response.choices[0].message.content)


def annotateSpeaker(paragraphs: list[str], scene):
    text = "\n\n".join(paragraphs)
    systemPrompt = """Parse the following scene and annotate the speaker for each paragraph. Return the output as json in the form of:
{
    'paragraphs': [
        {paragraphID: 'Paragraph ID number', speaker: 'speaker'},
        {paragraphID: 'Paragraph ID number', speaker: 'speaker2'}
    ]
}
"""
    if len(scene["characters"]) > 0:
        systemPrompt = (
            systemPrompt + f"Possible speakers: {', '.join(scene['characters'])} \n"
        )

    systemPrompt = (
        systemPrompt
        + f"The story is written in {scene['pointOfViewType']} and the narrator is {scene['pointOfView']}"
    )

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


def summerizeScene(paragraphs: list[str]):
    text = "\n\n".join(paragraphs)

    systemPrompt = """Read the following story, separating out the major sections, return the output as json in the form of:
{
    'section':[{
        'startID': 'Paragraph ID of the start of the scene',
        'sceneSummary': 'short paragraph summarizing the scene',
        'characters': [character1, character2, character3],
        'pointOfViewType': 'The point of view writing style of the scene',
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

    # modify the startID to be an integer:
    # modify the pointOfView to be a PointOfViewType:
    for scene in data["scenes"]:
        scene["startID"] = int(scene["startID"])
        # scene["pointOfViewType"] = str(PointOfViewType(scene["pointOfViewType"]))

    return data


# this creates a new document and annotates line by line with the information.
def annotateDocument(
    directory: Path, name: str, data: list[str], annotatedSceneList: list[dict]
):
    # create directory if it doesn't exist:
    if directory.exists() == False:
        directory.mkdir()
    # create a file for each document:

    documentFile = directory.joinpath(name + ".txt")
    with open(documentFile, "w") as file:
        nextSceneIndex = 0
        currentSceneIndex = -1
        for i in range(len(data)):
            if nextSceneIndex < len(annotatedSceneList):
                if i == int(annotatedSceneList[nextSceneIndex]["scene"]["startID"]):
                    file.write(
                        f"Scene: {annotatedSceneList[nextSceneIndex]['scene']['sceneSummary']}\n"
                    )
                    file.write(
                        f"Characters: {', '.join(annotatedSceneList[nextSceneIndex]['scene']['characters'])}\n"
                    )
                    file.write(
                        f"Point of View: {annotatedSceneList[nextSceneIndex]['scene']['pointOfView']}\n"
                    )
                    file.write(
                        f"Setting: {annotatedSceneList[nextSceneIndex]['scene']['setting']}\n"
                    )
                    file.write("\n")
                    currentSceneIndex = nextSceneIndex
                    nextSceneIndex += 1
            if currentSceneIndex != -1:  # we are initialized.
                if (
                    annotatedSceneList[currentSceneIndex]["annotations"].get(str(i))
                    is not None
                ):
                    file.write(
                        f"Speaker: {annotatedSceneList[currentSceneIndex]['annotations'][str(i)]}\n"
                    )
            file.write(data[i] + "\n\n")
