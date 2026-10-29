"""Measure manuscript elements (LaTeX or Markdown) and compare them with a limits profile."""
import re

# Generic example profiles. Always confirm the current limits in your target journal's guide.
PRESETS = {
    "short-letter": {"title_chars": 90, "abstract_words": 150, "body_words": 2500, "references": 30,
                     "figures": 4, "tables": 2, "display_items": 4, "keywords_min": 3, "keywords_max": 6},
    "research-article": {"title_chars": 150, "abstract_words": 250, "body_words": 6000, "references": 60,
                         "figures": 8, "tables": 5, "keywords_min": 4, "keywords_max": 8},
    "review": {"title_chars": 150, "abstract_words": 300, "body_words": 10000, "references": 200,
               "figures": 10, "tables": 8, "keywords_min": 4, "keywords_max": 10},
    "conference-abstract": {"title_chars": 120, "abstract_words": 300, "body_words": 0, "references": 5,
                            "figures": 1, "tables": 1},
}


def _words(text):
    return len(re.findall(r"[A-Za-z0-9\u00c0-\u024f]+(?:[-'][A-Za-z0-9]+)*", text))


def _strip_tex(t):
    t = re.sub(r"(?<!\\)%.*", "", t)
    t = re.sub(r"\\begin\{(equation|align|figure|table|tabular)\*?\}.*?\\end\{\1\*?\}", " ", t, flags=re.S)
    t = re.sub(r"\$[^$]*\$", " x ", t)
    t = re.sub(r"\\(?:cite\w*|ref|eqref|label|url|includegraphics)\s*(?:\[[^\]]*\])?\{[^}]*\}", " ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", t)
    return t.replace("{", " ").replace("}", " ")


def measure_latex(tex):
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    title = re.search(r"\\title\s*(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", tex_nc)
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex_nc, re.S)
    kw = re.search(r"\\(?:keywords|begin\{keywords\})\s*\{?(.*?)(?:\}|\\end\{keywords\})", tex_nc, re.S)
    body = re.search(r"\\begin\{document\}(.*?)(?:\\bibliography\{|\\printbibliography|\\begin\{thebibliography\}|\\end\{document\})",
                     tex_nc, re.S)
    body_text = body.group(1) if body else tex_nc
    if abstract:
        body_text = body_text.replace(abstract.group(0), " ")
    if kw:
        body_text = body_text.replace(kw.group(0), " ")
    body_text = re.sub(r"\\maketitle|\\title\{.*?\}", " ", body_text)
    cites = set()
    for group in re.findall(r"\\[A-Za-z]*cite[A-Za-z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}", tex_nc):
        cites.update(k.strip() for k in group.split(",") if k.strip())
    bibitems = len(re.findall(r"\\bibitem", tex_nc))
    figures = len(re.findall(r"\\begin\{figure\*?\}", tex_nc))
    tables = len(re.findall(r"\\begin\{table\*?\}", tex_nc))
    return {
        "title_chars": len(" ".join(_strip_tex(title.group(1)).split())) if title else 0,
        "abstract_words": _words(_strip_tex(abstract.group(1))) if abstract else 0,
        "body_words": _words(_strip_tex(body_text)),
        "references": max(len(cites), bibitems),
        "figures": figures,
        "tables": tables,
        "display_items": figures + tables,
        "keywords": len([k for k in re.split(r"[;,]|\\sep", kw.group(1)) if k.strip()]) if kw else 0,
    }


def measure_markdown(md):
    title = re.search(r"^#\s+(.+)$", md, re.M)
    abstract = re.search(r"^#+\s*abstract\s*$(.*?)(?=^#|^\**keywords\**\s*:)", md, re.S | re.I | re.M)
    kw = re.search(r"^\**keywords\**\s*:\s*(.+)$", md, re.I | re.M)
    refs_sec = re.search(r"^#+\s*references\s*$(.*)", md, re.S | re.I | re.M)
    body = md[:refs_sec.start()] if refs_sec else md
    if abstract:
        body = body.replace(abstract.group(0), "")
    if title:
        body = body.replace(title.group(0), "")
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)|^\|.*\|$|^keywords:.*$", " ", body, flags=re.M | re.I)
    refs = len(re.findall(r"^\s*(?:\d+\.|\[\d+\]|-)\s+\S", refs_sec.group(1), re.M)) if refs_sec else 0
    figures = len(re.findall(r"!\[[^\]]*\]\(", md))
    tables = len(re.findall(r"^\|?\s*:?-{3,}", md, re.M))
    return {"title_chars": len(title.group(1).strip()) if title else 0,
            "abstract_words": _words(abstract.group(1)) if abstract else 0,
            "body_words": _words(body), "references": refs, "figures": figures, "tables": tables,
            "display_items": figures + tables,
            "keywords": len([k for k in re.split(r"[;,]", kw.group(1)) if k.strip()]) if kw else 0}


def measure(text, kind=None):
    if kind == "markdown" or (kind is None and "\\begin{document}" not in text and "\\section" not in text):
        return measure_markdown(text)
    return measure_latex(text)


def check_limits(measured, limits):
    """Return rows (item, value, limit, status) with status ok / over / under."""
    rows = []
    for item, limit in limits.items():
        if item in ("keywords_min", "keywords_max"):
            continue
        if not limit:
            continue
        v = measured.get(item, 0)
        rows.append((item, v, limit, "over" if v > limit else "ok"))
    if "keywords_min" in limits or "keywords_max" in limits:
        k = measured["keywords"]
        lo, hi = limits.get("keywords_min", 0), limits.get("keywords_max", 99)
        rows.append(("keywords", k, "%d-%d" % (lo, hi), "under" if k < lo else "over" if k > hi else "ok"))
    return rows
