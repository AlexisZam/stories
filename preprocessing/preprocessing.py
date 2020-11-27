from itertools import chain
from json import dump
from pathlib import Path, PurePath
from re import split, sub
from shutil import copyfileobj
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import get

BASE_PATH = Path(__file__).resolve()
BASE_PATH = PurePath(BASE_PATH).parent
BASE_PATH = PurePath.joinpath(BASE_PATH, "..", "frontend", "src")
BASE_URL = "http://life.ou.edu/stories/"


def get_titles():
    response = get(BASE_URL)
    soup = BeautifulSoup(markup=response.text, features="html.parser")
    anchors = soup.find_all("a")

    romanized_ja_titles = []
    alt_ja_titles, alt_en_titles = [], []

    for anchor in anchors:
        romanized_ja_title = anchor.get("href")

        if (
            romanized_ja_title.endswith(".html")
            and romanized_ja_title != "momonokotarou.html"
        ):
            romanized_ja_title = romanized_ja_title.replace(".html", "")
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
            alt_ja_titles.append(alt_ja_title)
            alt_en_titles.append(alt_en_title)

    return romanized_ja_titles, list(zip(alt_ja_titles, alt_en_titles))


def format_p_alt_ja_sentences(p_alt_ja_sentences):
    return p_alt_ja_sentences.splitlines()


def format_p_sentences(p_sentences):
    p_sentences = p_sentences.splitlines()

    i = 0
    p_ja_sentences, p_en_sentences = [], []

    while i < len(p_sentences):
        ja_sentence, en_sentence = [], []
        while not p_sentences[i].isascii():
            ja_sentence.append(p_sentences[i])
            i += 1
        while i < len(p_sentences) and p_sentences[i].isascii():
            en_sentence.append(p_sentences[i])
            i += 1

        p_ja_sentences.append(" ".join(ja_sentence))
        p_en_sentences.append(" ".join(en_sentence))

    return p_ja_sentences, p_en_sentences


def format_p_words(p_words):
    p_words.replace(",\n", ", ")
    p_words.replace("=\n", "= ")
    p_words = p_words[0].splitlines()

    p_ja_words, p_en_words = [], []

    for p_word in p_words:
        words = list(map(str.strip, p_word.split("=")))
        # if len(words) != 2:
        #     print(words)
        p_ja_words.append(words[0])
        p_en_words.append(", ".join(words[1:]))

    return p_ja_words, p_en_words


def get_story(romanized_ja_title):
    url = urljoin(BASE_URL, romanized_ja_title + ".html")
    response = get(url)
    text = BeautifulSoup(markup=response.text, features="html.parser").get_text()

    text = "\n".join(
        line.strip() for line in text.splitlines() if line and not line.isspace()
    )

    text = sub(r" +", " ", text).replace("＝", "=")

    titlepage, *pages = split(r"page \d+\n", text)

    title_ja, title_en = titlepage.splitlines()[:2]
    title_ja = title_ja.split()[0]

    alt_ja_sentences = []
    ja_sentences, en_sentences = [], []
    ja_words, en_words = [], []

    for page in pages:
        sections = page.split("--\n")

        assert len(sections) <= 3

        p_alt_ja_sentences = format_p_alt_ja_sentences(sections[0])
        alt_ja_sentences.extend(p_alt_ja_sentences)

        p_ja_sentences, p_en_sentences = format_p_sentences(sections[1])
        ja_sentences.append(p_ja_sentences)
        en_sentences.append(p_en_sentences)

        if len(sections) == 3:
            p_ja_words, p_en_words = format_p_words(sections[2])
            ja_words.append(p_ja_words)
            en_words.append(p_en_words)

    # if " ".join(alt_ja_sentences) != " ".join(ja_sentences):
    #     print(" ".join(alt_ja_sentences))
    #     print(" ".join(ja_sentences))

    return {
        "title": (title_ja, title_en),
        "sentences": list(zip(chain(*ja_sentences), chain(*en_sentences))),
        "words": list(zip(chain(*ja_words), chain(*en_words))),
    }


def get_image(romanized_ja_title):
    url = urljoin(BASE_URL, romanized_ja_title + "2.jpg")
    return get(url, stream=True).raw


romanized_ja_titles, alt_titles = get_titles()

stories = {
    romanized_ja_title: get_story(romanized_ja_title)
    for romanized_ja_title in romanized_ja_titles
}

titles = [story["title"] for story in stories.values()]
# assert alt_titles == titles

path = PurePath.joinpath(BASE_PATH, "stories.json")
with open(path, "w") as fp:
    dump(stories, fp)

for romanized_ja_title in romanized_ja_titles:
    image = get_image(romanized_ja_title)
    path = PurePath.joinpath(BASE_PATH, "img", romanized_ja_title + ".jpg")
    with open(path, "wb") as fdst:
        copyfileobj(image, fdst)
