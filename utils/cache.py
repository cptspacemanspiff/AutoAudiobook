import hashlib 
from pathlib import Path
import pickle
import json

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