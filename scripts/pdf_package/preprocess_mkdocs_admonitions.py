#!/usr/bin/env python
from __future__ import annotations

import pathlib
import re
import sys

# Supports:
# - !!! type "Title"
# - ??? type "Title"
# - ???+ type "Title"
PAT = re.compile(
    r'^(?P<indent>\s*)(?P<marker>!!!|\?\?\?\+?)(?:\s+(?P<kind>[A-Za-z_][\w-]*))?(?:\s+"(?P<title>[^"]+)")?\s*$'
)

KIND_TITLE = {
    "note": "Note",
    "info": "Info",
    "warning": "Warning",
    "danger": "Danger",
    "success": "Success",
    "tip": "Tip",
}


def sanitize_inline_markup(line: str) -> str:
    # Avoid parser edge-cases around bold + braces used in variable placeholders.
    line = re.sub(r"\*\*(\{\{[^}]+\}\})\*\*", r"`\1`", line)
    line = line.replace("「**{**」", "「`{`」")
    line = line.replace("「**/**」", "「`/`」")
    return line


def strip_one_indent(line: str) -> str:
    if line.startswith("    "):
        return line[4:]
    if line.startswith("\t"):
        return line[1:]
    return line


def is_fence(line: str) -> tuple[str, int] | None:
    s = line.lstrip()
    if s.startswith("```"):
        return ("`", len(s) - len(s.lstrip("`")))
    if s.startswith("~~~"):
        return ("~", len(s) - len(s.lstrip("~")))
    return None


def normalize_deep_indented_fences(text: str) -> str:
    """Normalize deeply indented fenced code blocks for Pandoc/CommonMark.

    In this repository, fenced blocks in list items are often indented by 8
    spaces. CommonMark-style parsing can fail there, so we shift them to 4
    spaces and ensure a blank line before opening fences.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(?P<indent>[ \t]{8,})(?P<fence>`{3,}|~{3,}).*$", line)
        if not m:
            out.append(line)
            i += 1
            continue

        indent = m.group("indent")
        reduced = indent[4:] if indent.startswith("    ") else indent
        fence = m.group("fence")

        if out and out[-1].strip() != "":
            out.append("")

        out.append(reduced + line[len(indent) :])
        i += 1

        while i < len(lines):
            inner = lines[i]
            cm = re.match(r"^(?P<i2>[ \t]*)(?P<cfence>`{3,}|~{3,})\s*$", inner)
            if cm and cm.group("cfence")[0] == fence[0] and len(cm.group("cfence")) >= len(fence):
                i2 = cm.group("i2")
                reduced2 = i2[4:] if i2.startswith("    ") else i2
                out.append(reduced2 + inner[len(i2) :])
                i += 1
                break

            if inner.startswith(indent):
                out.append(reduced + inner[len(indent) :])
            elif inner.startswith("    "):
                out.append(inner[4:])
            else:
                out.append(inner)
            i += 1

    return "\n".join(out) + "\n"


def transform(text: str) -> str:
    text = normalize_deep_indented_fences(text)
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    in_code = False
    fence_char: str | None = None
    fence_len = 0

    while i < len(lines):
        line = lines[i]
        f = is_fence(line)
        if f:
            ch, ln = f
            if not in_code:
                in_code = True
                fence_char, fence_len = ch, ln
            elif ch == fence_char and ln >= fence_len:
                in_code = False
                fence_char = None
                fence_len = 0
            out.append(line)
            i += 1
            continue

        if in_code:
            out.append(line)
            i += 1
            continue

        m = PAT.match(line)
        if not m:
            out.append(sanitize_inline_markup(line))
            i += 1
            continue

        marker = m.group("marker")
        kind = (m.group("kind") or "note").lower()
        title = m.group("title") or KIND_TITLE.get(kind, kind.capitalize())

        j = i + 1
        body: list[str] = []
        while j < len(lines):
            nxt = lines[j]
            if nxt.strip() == "":
                body.append("")
                j += 1
                continue
            if nxt.startswith("    ") or nxt.startswith("\t"):
                body.append(sanitize_inline_markup(strip_one_indent(nxt)))
                j += 1
                continue
            break

        classes = ".admonition ." + re.sub(r"[^A-Za-z0-9_-]", "-", kind)
        if marker.startswith("???"):
            classes += " .details"

        out.append(f"::: {{{classes}}}")
        out.append(f"**{title}**")
        if body and any(x.strip() for x in body):
            out.append("")
            out.extend(body)
        out.append(":::")

        i = j

    return "\n".join(out) + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: preprocess_mkdocs_admonitions.py <input.md> <output.md>")
        return 2
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(transform(text), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

