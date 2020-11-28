from pathlib import Path, PurePath
from pickle import load

from pylatex import Command, Document, Figure, NoEscape, Package, escape_latex
from pylatex.section import Chapter

BASE_PATH = Path(__file__).resolve()
BASE_PATH = PurePath(BASE_PATH).parent
BASE_PATH = PurePath.joinpath(BASE_PATH, "out")

TITLE = "Traditional Japanese Children's Stories"
AUTHOR = "Tom Ray"

if __name__ == "__main__":
    path = PurePath.joinpath(BASE_PATH, "stories.pkl")
    with open(path, mode="rb") as f:
        stories = load(f)

    d = Document(
        documentclass="book",
        document_options="oneside",
        inputenc=None,
        indent=False,
        geometry_options="legalpaper",
    )

    d.packages.append(Package("dblfnote"))
    d.packages.append(Package("hyperref", options="hidelinks"))
    d.packages.append(Package("parcolumns"))
    d.packages.append(Package("titlepic"))
    d.packages.append(Package("xeCJK"))

    d.preamble.append(Command(command="setCJKmainfont", arguments="Noto Serif JP"))
    d.preamble.append(Command(command="setCJKsansfont", arguments="Noto Sans JP"))

    d.preamble.append(Command(command="title", arguments=TITLE))
    d.preamble.append(Command(command="author", arguments=AUTHOR))
    d.preamble.append(Command(command="date", arguments=""))
    path = PurePath.joinpath(BASE_PATH, "img", "momonokotarou.jpg")
    d.preamble.append(
        Command(
            command="titlepic",
            arguments=Command(
                command="includegraphics",
                arguments=path,
                options=NoEscape(r"width=0.6\textwidth"),
            ),
        )
    )

    d.append(Command(command="maketitle"))
    d.append(Command(command="frontmatter"))
    d.append(Command(command="tableofcontents"))
    d.append(Command(command="mainmatter"))

    for romanized_title, story in stories.items():
        title = "".join(story["title"])
        d.append(Chapter(title))

        with d.create(Figure()) as figure:
            path = PurePath.joinpath(BASE_PATH, "img", romanized_title + ".jpg")
            figure.add_image(str(path))

        d.append(
            Command(
                command="begin",
                arguments="parcolumns",
                options="sloppy",
                extra_arguments=2,
            )
        )

        for paragraph, words in zip(story["paragraphs"], story["words"]):
            paragraph[0] = escape_latex(paragraph[0])
            footnotemark = NoEscape(r"\footnotemark") if words else ""
            d.append(Command(command="colchunk", arguments=paragraph[0] + footnotemark))
            if words:
                words = map(escape_latex, words)
                words = r"\\".join(words)
                d.append(Command(command="footnotetext", arguments=NoEscape(words)))
            d.append(Command(command="colchunk", arguments=paragraph[1]))
            d.append(Command(command="colplacechunks"))

        d.append(Command(command="end", arguments="parcolumns"))

    path = PurePath.joinpath(BASE_PATH, "stories")
    d.generate_pdf(
        filepath=path, clean_tex=False, compiler="latexmk", compiler_args=["-xelatex"]
    )
