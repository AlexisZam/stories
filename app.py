# from difflib import HtmlDiff
from itertools import chain
from re import split, sub

from bs4 import BeautifulSoup
from flask import Flask, render_template
from requests import get

URL = "http://life.ou.edu/stories/"


def get_links_and_alt_titles():
    response = get(URL)
    a_elements = BeautifulSoup(markup=response.text, features="html.parser").find_all(
        "a"
    )

    links = []
    alt_ja_titles, alt_en_titles = [], []

    for a_element in a_elements:
        link = a_element.get("href")

        if (
            link.endswith(".html")
            and link != "momonokotarou.html"
            and link.startswith("s")
        ):
            link = link.replace(".html", "")
            alt_ja_title, alt_link_and_alt_en_title = (
                a_element.get_text().strip().split("、")
            )
            alt_ja_title = alt_ja_title.split(" ")[0].strip()
            alt_link, alt_en_title = alt_link_and_alt_en_title.split("(")
            alt_link = alt_link.strip().lower()
            alt_en_title = alt_en_title.replace(")", "").replace(".", "")

            assert alt_link == link

            links.append(link)
            alt_ja_titles.append(alt_ja_title)
            alt_en_titles.append(alt_en_title)

    return links, list(zip(alt_ja_titles, alt_en_titles))


def get_story(link):
    response = get(f"{URL}/{link}.html")
    text = BeautifulSoup(markup=response.text, features="html.parser").get_text()

    text = "\n".join(
        line.strip() for line in text.splitlines() if line and not line.isspace()
    )

    text = sub(r" +", " ", text).replace("＝", "=")

    title, *pages = [en_sentence for en_sentence in split(r"page \d+\n", text)]

    title_ja, title_en = title.splitlines()[:2]
    title_ja = title_ja.split()[0]

    alt_ja_sentences = []
    ja_sentences, en_sentences = [], []
    ja_words, en_words = [], []

    for page in pages:
        p_alt_ja_sentences, p_sentences, *p_words = page.split("--\n")

        alt_ja_sentences.extend(p_alt_ja_sentences.splitlines())

        p_sentences = p_sentences.splitlines()
        p_en_sentences, p_ja_sentences = [], []
        i = 0
        while i < len(p_sentences):
            ja_sentence, en_sentence = [], []
            while not p_sentences[i].isascii():
                ja_sentence.append(p_sentences[i])
                i += 1
            while i < len(p_sentences) and p_sentences[i].isascii():
                en_sentence.append(p_sentences[i])
                i += 1
            p_en_sentences.append(" ".join(en_sentence))
            p_ja_sentences.append(" ".join(ja_sentence))
        en_sentences.append(p_en_sentences)
        ja_sentences.append(p_ja_sentences)

        if p_words:
            i = 0
            p_en_words, p_ja_words = [], []
            p_words = p_words[0].splitlines()
            while i < len(p_words):
                # while i < len(lines) and (
                #     lines[i].endswith(",") or lines[i].endswith("=")
                # ):
                #     i += 1
                #     line += " " + lines[i]
                words = list(map(str.strip, p_words[i].split("=")))
                if len(words) != 2:
                    print(words)
                p_ja_words.append(words[0])
                p_en_words.append(", ".join(words[1:]))
                i += 1
            ja_words.append(p_ja_words)
            en_words.append(p_en_words)

    return {
        "title": (title_ja, title_en),
        "alt_ja_sentences": alt_ja_sentences,
        "sentences": list(zip(chain(*ja_sentences), chain(*en_sentences))),
        "words": list(zip(chain(*ja_words), chain(*en_words))),
    }

    # print("\n".join(vocabulary))

    # if " ".join(story) != " ".join(ja_sentences):
    #     print(" ".join(story))
    #     print(" ".join(ja_sentences))
    # diff = HtmlDiff().make_file(" ".join(story), " ".join(ja_sentences), context=True)
    # with open(link, "w") as f:
    #     f.write(diff)


links, alt_titles = get_links_and_alt_titles()

stories = {link: get_story(link) for link in links}

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", links_and_alt_titles=zip(links, alt_titles))


@app.route("/<path>/<subpath>")
def zoo(path, subpath):
    if subpath == "story":
        story = True
        return render_template(
            "story.html",
            title=stories[path]["title"],
            sentences=stories[path]["sentences"],
            story=story,
        )
    elif subpath == "vocabulary":
        story = False
        return render_template(
            "story.html",
            title=stories[path]["title"],
            words=stories[path]["words"],
            story=story,
        )
