# journal-limits-checker

**Check, before you submit, whether your manuscript fits the journal: title length, abstract
and body word counts, references, figures, tables and keywords, all in one table.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Desk rejections and "please shorten" returns cost weeks. Every journal sets limits on several
elements at once, and they change between article types. When a paper is transferred to another
journal, every limit must be rechecked. This tool measures the manuscript and compares it with a
limits profile in seconds.

## Features

- Measures LaTeX (`\title`, `abstract`, `\keywords`, figures/tables incl. starred, unique cited keys or
  `\bibitem`s) and Markdown (`# Title`, `## Abstract`, `Keywords:`, images, tables, numbered references)
- Body words exclude abstract, comments, math, floats, citations and bibliography
- Generic presets (`short-letter`, `research-article`, `review`, `conference-abstract`), JSON
  profiles for your journal, and single overrides with `--set`
- Percent of each limit used; exit code 1 if anything is over/under (CI-ready)

## Usage

```bash
pip install .
journal-limits-checker main.tex -l examples/my_journal.json
journal-limits-checker paper.md -p short-letter --set references=25
```

Presets are illustrative only; copy the real numbers from your journal's author guidelines.

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
