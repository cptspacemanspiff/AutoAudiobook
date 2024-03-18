from enum import Enum
from utils.cache import cacheDict
# pull in configuration info:
from config import client, MODEL, CACHE_DIRECTORY, CACHE

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
                if cacheDict(CACHE_DIRECTORY , CACHE, isSame, key, value.lower()):
                    index = cls._llmLookup.value[key]
                    break
        if index is None:
            index = 0
        return cls(index)