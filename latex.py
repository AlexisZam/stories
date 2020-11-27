from pathlib import Path, PurePath
from pickle import load

from pylatex import Command, Document, Figure, NoEscape, Package, escape_latex
from pylatex.section import Chapter

BASE_PATH = Path(__file__).resolve()
BASE_PATH = PurePath(BASE_PATH).parent
BASE_PATH = PurePath.joinpath(BASE_PATH, "out")


def foo(romanized_ja_title, story):
    ja_title, en_title = story["title"]

    document.append(Chapter(NoEscape(ja_title + r"\\" + en_title)))

    with document.create(Figure(position="h")) as figure:
        path = PurePath.joinpath(BASE_PATH, "img", romanized_ja_title + ".jpg")
        figure.add_image(str(path))

    document.append(NoEscape(r"\begin{parcolumns}[sloppy]{2}"))
    for (ja_sentence, en_sentence), words in zip(story["sentences"], story["words"]):
        words = map(escape_latex, words)
        words = r"\\".join(words)
        s = f"\\colchunk{{{ja_sentence}\\footnotemark}}\\footnotetext{{{words}}}\\colchunk{{{en_sentence}}}\\colplacechunks"
        document.append(NoEscape(s))

    document.append(NoEscape(r"\end{parcolumns}"))


if __name__ == "__main__":
    path = PurePath.joinpath(BASE_PATH, "stories.pkl")
    with open(path, "rb") as f:
        stories = load(f)

    document = Document(documentclass="book", indent=False, geometry_options="a4paper")

    document.packages.append(Package("dblfnote"))
    document.packages.append(Package("hyperref", options="hidelinks"))
    document.packages.append(Package("parcolumns"))
    document.packages.append(Package("xeCJK"))

    document.preamble.append(
        Command("title", "Traditional Japanese Children's Stories")
    )
    document.preamble.append(Command("date", ""))
    document.append(NoEscape(r"\DFNalwaysdouble"))
    document.append(NoEscape(r"\maketitle"))
    document.append(NoEscape(r"\tableofcontents"))

    for romanized_ja_title, story in stories.items():
        foo(romanized_ja_title, story)

    path = PurePath.joinpath(BASE_PATH, "stories")
    document.generate_pdf(filepath=path, compiler="latexmk", compiler_args=["-xelatex"])
