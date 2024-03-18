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
        systemPrompt = (
            systemPrompt + f"Possible speakers: {', '.join(possibleCharacters)}"
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

    # modify the startID to be an integer:
    # modify the pointOfView to be a PointOfViewType:
    for scene in data["scenes"]:
        scene["startID"] = int(scene["startID"])
        scene["pointOfView"] = PointOfViewType(scene["pointOfView"])

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
