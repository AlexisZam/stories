from itertools import chain, filterfalse
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


def get_romanized_ja_and_alt_titles():
    response = get(BASE_URL)
    soup = BeautifulSoup(markup=response.text, features="html.parser")
    anchors = soup.find_all("a")

    romanized_ja_titles = []
    alt_titles = []

    for anchor in anchors:
        href = anchor.get("href")

        if PurePath(href).suffix == ".html" and href != "momonokotarou.html":
            romanized_ja_title = PurePath(href).stem
            alt_ja_title, alt_romanized_ja_and_alt_en_title = (
                anchor.get_text().strip().split("、")
            )
            alt_ja_title = alt_ja_title.split(" ")[0].strip()
            (
                alt_romanized_ja_title,
                alt_en_title,
            ) = alt_romanized_ja_and_alt_en_title.split("(")
            alt_romanized_ja_title = alt_romanized_ja_title.strip().lower()
            alt_en_title = alt_en_title.replace(")", "").replace(".", "")

            assert alt_romanized_ja_title == romanized_ja_title

            romanized_ja_titles.append(romanized_ja_title)
            alt_titles.append((alt_ja_title, alt_en_title))

    return romanized_ja_titles, alt_titles


def format_sentences(sentences):
    sentences = sentences.splitlines()

    ja_sentence = filterfalse(str.isascii, sentences)
    ja_sentence = " ".join(ja_sentence)
    en_sentence = filter(str.isascii, sentences)
    en_sentence = " ".join(en_sentence)

    return ja_sentence, en_sentence


def format_words(words):
    words.replace("＝", "=")
    words.replace("=\n", "= ")
    words.replace(",\n", ", ")
    return words.splitlines()


def get_story(romanized_ja_title):
    url = urljoin(BASE_URL, romanized_ja_title + ".html")
    response = get(url)
    soup = BeautifulSoup(markup=response.text, features="html.parser")
    text = soup.get_text()

    lines = text.splitlines()
    lines = map(str.strip, lines)
    lines = filter(lambda line: line, lines)
    text = "\n".join(lines)

    text = sub(r" +", " ", text)

    titlepage, *pages = split(r"page \d+\n", text)

    title_ja, title_en = titlepage.splitlines()[:2]
    title_ja = title_ja.split()[0]

    alt_ja_sentences = []
    sentences = []
    words = []

    for page in pages:
        sections = page.split("--\n")

        assert len(sections) <= 3

        alt_ja_sentences.extend(sections[0].splitlines())

        p_sentences = format_sentences(sections[1])
        sentences.append(p_sentences)

        p_words = format_words(sections[2]) if len(sections) == 3 else []
        words.append(p_words)

    # if " ".join(alt_ja_sentences) != " ".join(ja_sentences):
    #     print(" ".join(alt_ja_sentences))
    #     print(" ".join(ja_sentences))

    return {
        "title": (title_ja, title_en),
        "sentences": sentences,
        "words": words,
    }


def get_image(romanized_ja_title):
    url = urljoin(BASE_URL, romanized_ja_title + "2.jpg")
    return get(url, stream=True).raw


if __name__ == "__main__":
    romanized_ja_titles, alt_titles = get_romanized_ja_and_alt_titles()

    stories = {
        romanized_ja_title: get_story(romanized_ja_title)
        for romanized_ja_title in romanized_ja_titles
    }

    titles = [story["title"] for story in stories.values()]
    # assert alt_titles == titles

    path = PurePath.joinpath(BASE_PATH, "stories.pkl")
    with open(path, "wb") as f:
        dump(stories, f)

    for romanized_ja_title in romanized_ja_titles:
        image = get_image(romanized_ja_title)
        path = PurePath.joinpath(BASE_PATH, "img", romanized_ja_title + ".jpg")
        with open(path, "wb") as fdst:
            copyfileobj(image, fdst)
