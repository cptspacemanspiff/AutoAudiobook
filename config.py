from openai import OpenAI
from pathlib import Path
client = OpenAI()

# MODEL="gpt-4-0125-preview"
MODEL="gpt-3.5-turbo-0125"

CACHE_DIRECTORY = Path("cache")
CACHE = False