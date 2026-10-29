import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from journal_limits_checker.cli import main
from journal_limits_checker.core import check_limits, measure

TEX = r"""\documentclass{article}
\title{A Short {Title} Here}
\begin{document}
\maketitle
\begin{abstract}
One two three four five.
\end{abstract}
\keywords{alpha, beta; gamma}
\section{Intro}
Body text has six words \cite{a,b}. % hidden comment words
\begin{figure}\caption{x}\end{figure}
\begin{figure*}\caption{y}\end{figure*}
\begin{table}\caption{z}\end{table}
More \citep{c, a}.
\bibliography{refs}
\end{document}
"""
MD = """# My Paper Title

## Abstract
Short abstract of six words.

Keywords: a, b, c, d

## Introduction
Seven words of body text right here.

![fig](a.png)

| a | b |
|---|---|
| 1 | 2 |

## References
1. Ref one
2. Ref two
"""


class MeasureTests(unittest.TestCase):
    def test_latex(self):
        m = measure(TEX)
        self.assertEqual(m["title_chars"], len("A Short Title Here"))
        self.assertEqual(m["abstract_words"], 5)
        self.assertEqual(m["references"], 3)
        self.assertEqual((m["figures"], m["tables"], m["display_items"]), (2, 1, 3))
        self.assertEqual(m["keywords"], 3)
        self.assertEqual(m["body_words"], 7)   # Intro + "Body text has six words" + "More"

    def test_markdown(self):
        m = measure(MD)
        self.assertEqual((m["abstract_words"], m["references"], m["figures"], m["tables"], m["keywords"]),
                         (5, 2, 1, 1, 4))
        self.assertEqual(m["title_chars"], len("My Paper Title"))


class CheckTests(unittest.TestCase):
    def test_status(self):
        rows = {r[0]: r[3] for r in check_limits(measure(TEX), {"figures": 1, "tables": 3, "keywords_min": 4,
                                                                  "keywords_max": 6, "body_words": 0})}
        self.assertEqual(rows, {"figures": "over", "tables": "ok", "keywords": "under"})

    def test_cli_override(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.tex")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(TEX)
            with redirect_stdout(io.StringIO()) as buf:
                self.assertEqual(main([p, "--set", "figures=1"]), 1)
            self.assertIn("OVER  figures", buf.getvalue())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main([p, "--set", "keywords_min=3"]), 0)


if __name__ == "__main__":
    unittest.main()
