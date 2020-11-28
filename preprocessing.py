from itertools import filterfalse
from pathlib import Path, PurePath
from pickle import dump
from re import split, sub
from shutil import copyfileobj
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import get

BASE_PATH = Path(__file__).resolve()
BASE_PATH = PurePath(BASE_PATH).parent
BASE_PATH = PurePath.joinpath(BASE_PATH, "out")
BASE_URL = "http://life.ou.edu/stories/"


def get_romanized_titles():
    response = get(BASE_URL)
    soup = BeautifulSoup(markup=response.text, features="html.parser")

    anchors = soup.find_all(name="a")
    hrefs = map(lambda anchor: anchor.get("href"), anchors)
    hrefs = filter(lambda href: PurePath(href).suffix == ".html", hrefs)

    return list(map(lambda href: PurePath(href).stem, hrefs))


def get_story(romanized_title):
    url = urljoin(BASE_URL, romanized_title + ".html")
    response = get(url)
    soup = BeautifulSoup(markup=response.text, features="html.parser")

    text = soup.get_text()
    text = sub(r" +", " ", text)

    lines = text.splitlines()
    lines = map(str.strip, lines)
    lines = filter(lambda line: line, lines)
    text = "\n".join(lines)

    titlepage, *pages = split(r"page \d+\n", text)

    title = titlepage.splitlines()[:2]
    title[0] = filterfalse(str.isascii, title[0])
    title[0] = "".join(title[0])
    title[0] = title[0].split(sep="（")[0]

    paragraphs = []
    words = []

    for page in pages:
        sections = page.split(sep="--\n")

        lines = sections[1].splitlines()
        paragraph = filterfalse(str.isascii, lines), filter(str.isascii, lines)
        paragraph = list(map(lambda paragraph: " ".join(paragraph), paragraph))
        paragraphs.append(paragraph)

        if len(sections) == 3:
            sections[2] = sections[2].replace("＝", "=")
            sections[2] = sections[2].replace("=\n", "= ")
            sections[2] = sections[2].replace(",\n", ", ")
            lines = sections[2].splitlines()
            words.append(lines)
        else:
            words.append([])

    return {"title": title, "paragraphs": paragraphs, "words": words}


def get_image(romanized_title):
    url = urljoin(BASE_URL, romanized_title + "2.jpg")
    return get(url, stream=True).raw


if __name__ == "__main__":
    romanized_titles = get_romanized_titles()

    stories = {
        romanized_title: get_story(romanized_title)
        for romanized_title in romanized_titles
        if romanized_title != "momonokotarou"
    }

    path = PurePath.joinpath(BASE_PATH, "img")
    Path(path).mkdir(parents=True)

    path = PurePath.joinpath(BASE_PATH, "stories.pkl")
    with open(path, mode="wb") as f:
        dump(stories, f)

    for romanized_title in romanized_titles:
        image = get_image(romanized_title)
        path = PurePath.joinpath(BASE_PATH, "img", romanized_title + ".jpg")
        with open(path, mode="wb") as fdst:
            copyfileobj(image, fdst)
