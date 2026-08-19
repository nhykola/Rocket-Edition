#!/usr/bin/env python3
"""Shared, ROM-free helpers for Rocket Edition localization tools."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

TEXT_RE = re.compile(r"^(?P<indent>\s*)= (?P<text>.*)$")
ORG_RE = re.compile(r"^\s*#org\s+(\S+)", re.IGNORECASE)
LAYOUT_NAMES = {"\\n", "\\l", "\\p"}
BRACKET_TECHNICAL = re.compile(
    r"\[(?:player|buffer[123]|\$|ME|blue_fr|black_fr|\.|Ke)\]", re.IGNORECASE
)
HEX_COMMAND = re.compile(r"\\h[0-9A-Fa-f]{2}")
# These prefixes are controls in the historical corpus.  Crucially, only the
# prefix is consumed: `\when` becomes the immutable token `\w` + visible `hen`.
SINGLE_COMMANDS = {"c", "w", "I", "a", "y", "F", "G"}


@dataclass(frozen=True)
class Control:
    value: str
    start: int
    end: int
    kind: str  # immutable | layout


def decode_script(data: bytes) -> tuple[str, str]:
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return data.decode("cp1252"), "cp1252"


def script_files(root: Path):
    return sorted((root / "scripts").rglob("*.rbc"))


def iter_strings(root: Path):
    for path in script_files(root):
        text, encoding = decode_script(path.read_bytes())
        label = ""
        for number, line in enumerate(text.splitlines(), 1):
            org = ORG_RE.match(line)
            if org:
                label = org.group(1)
            match = TEXT_RE.match(line)
            if match:
                source = match.group("text")
                identity = f"{path.relative_to(root)}:{label}:{source}".encode()
                yield {"id": hashlib.sha1(identity).hexdigest()[:12],
                       "file": path.relative_to(root).as_posix(), "line": number,
                       "label": label, "encoding": encoding, "source": source}


def controls(text: str) -> list[Control]:
    """Lex XSE controls without ever swallowing adjacent player-visible text."""
    result: list[Control] = []
    i = 0
    while i < len(text):
        bracket = BRACKET_TECHNICAL.match(text, i)
        if bracket:
            result.append(Control(bracket.group(), i, bracket.end(), "immutable"))
            i = bracket.end(); continue
        if text.startswith(("\\n", "\\l", "\\p"), i):
            result.append(Control(text[i:i + 2], i, i + 2, "layout")); i += 2; continue
        hex_command = HEX_COMMAND.match(text, i)
        if hex_command:
            result.append(Control(hex_command.group(), i, hex_command.end(), "immutable"))
            i = hex_command.end(); continue
        if text.startswith("\\\\", i):
            result.append(Control("\\\\", i, i + 2, "immutable")); i += 2; continue
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] in SINGLE_COMMANDS:
            result.append(Control(text[i:i + 2], i, i + 2, "immutable")); i += 2; continue
        # Unknown brackets/backslashes are technical until classified.  Capture
        # one atomic token, never the following word.
        if text[i] == "[":
            end = text.find("]", i + 1)
            if end != -1:
                result.append(Control(text[i:end + 1], i, end + 1, "immutable")); i = end + 1; continue
        if text[i] == "\\":
            result.append(Control(text[i:i + 2], i, min(i + 2, len(text)), "immutable")); i += 2; continue
        i += 1
    return result


def immutable_tokens(text: str) -> list[str]:
    return [item.value for item in controls(text) if item.kind == "immutable"]


def visible_text(text: str, *, keep_layout: bool = True) -> str:
    """Remove technical controls by spans while retaining every visible byte."""
    out=[]; cursor=0
    for token in controls(text):
        out.append(text[cursor:token.start])
        if keep_layout and token.kind == "layout": out.append(token.value)
        cursor=token.end
    out.append(text[cursor:])
    return "".join(out)


def display_lines(text: str) -> list[tuple[int, int, str]]:
    """Return (page, row, text) and reject invalid two-row FireRed flow."""
    clean=visible_text(text, keep_layout=True); page=row=0; lines=[]; current=[]
    for part in re.split(r"(\\[nlp])", clean):
        if part not in LAYOUT_NAMES: current.append(part); continue
        lines.append((page, row, "".join(current))); current=[]
        if part == "\\p": page += 1; row = 0
        elif part == "\\n": row += 1
        else:  # \l scrolls only after the lower row has been reached
            if row < 1: raise ValueError("\\l avant la deuxième ligne")
            row = 1
        if row > 1: raise ValueError("plus de deux lignes sans défilement/page")
    lines.append((page, row, "".join(current)))
    return lines
