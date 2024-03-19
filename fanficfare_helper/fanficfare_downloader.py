import subprocess
import json
import pathlib
import re
from argparse import ArgumentParser


# by default use the config file in the current directory:
CONFIG_FILE_DEFAULT = pathlib.Path(__file__).parent.resolve().joinpath("config.ini")
DOWNLOAD_PATH = pathlib.Path(__file__).parent.parent.resolve().joinpath("downloads")


def getStoryInfo(url, configFile=CONFIG_FILE_DEFAULT):
    arglist = ["fanficfare", "-m", "-j", "-z", "-c", configFile, '--no-output', url]
    rc = subprocess.run(arglist, capture_output=True)
    # convert the json to a dictionary:
    storyData = json.loads(rc.stdout)
    return storyData


def getChapterText(
    url, chapterNum, directory, author, title, configFile=CONFIG_FILE_DEFAULT
):
    # format of directory structure: <author>/<title>/<chapterNum>.<title>.txt
    # directory = pathlib.Path(directory).joinpath(author).joinpath(title)
    pathlib.Path(directory).joinpath().mkdir(parents=True, exist_ok=True)
    arglist = [
        "fanficfare",
        "-c",
        configFile,
        "-f",
        "txt",
        "-b",
        str(chapterNum),
        "-e",
        str(chapterNum),
        "-o",
        "output_filename=" + str(chapterNum) + "-" + str(title) + """${formatext}""",
        url,
    ]
    print(arglist)
    rc = subprocess.run(arglist, capture_output=False, cwd=directory)


# 
def downloadStory(url, rootDirectory):
    storyInfo = getStoryInfo(url)

    numChapters = int(storyInfo["numChapters"])
    title = storyInfo["title"]
    pathTitle = re.sub(r"[^\w_.-]", "_", title)
    author = storyInfo["author"]
    pathAuthor = re.sub(r"[^\w_.-]", "_", author)

    directory = pathlib.Path(rootDirectory).joinpath(pathAuthor).joinpath(pathTitle)
    pathlib.Path(directory).joinpath().mkdir(parents=True, exist_ok=True)

    # write the story info to a file:
    with open(
        pathlib.Path(directory)
        .joinpath(f"storyInfo-{pathTitle}.json"),
        "w",
    ) as f:
        json.dump(storyInfo, f)

    for i in range(1, numChapters + 1):
        getChapterText(
            url,
            i,
            directory,
            pathAuthor,
            pathTitle,
        )


def cliDownload():
    parser = ArgumentParser(
        description="Download a story from a URL, using fanficfare, separating chapters into individual text files."
    )
    parser.add_argument("url", help="URL of the story to download")
    parser.add_argument("directory", help="download_directory")
    args = parser.parse_args()

    downloadStory(args.url, args.directory)

if __name__ == "__main__":
    print("Running testFanFicFare.py")
    # downloadStory("https://archiveofourown.org/works/53155222/chapters/134498068", DOWNLOAD_PATH)
    cliDownload()
