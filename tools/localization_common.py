#!/usr/bin/env python3
"""Shared, ROM-free helpers for the Rocket Edition localization tools."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

TEXT_RE = re.compile(r"^(?P<indent>\s*)= (?P<text>.*)$")
ORG_RE = re.compile(r"^\s*#org\s+(\S+)", re.IGNORECASE)
TOKEN_RE = re.compile(r"\[[^\]\r\n]+\]|\\(?:[npl]|[chw][^\\\s]{0,5}|.)")
STRUCTURAL_RE = re.compile(r"\\[npl]|\[\.\]|\[(?:player|buffer[123]|\$|ME)\]|\\[chw][^\\\s]{0,5}", re.I)


def decode_script(data: bytes) -> tuple[str, str]:
    """Decode the two encodings actually present in the historical source tree."""
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
                key = hashlib.sha1(f"{path.relative_to(root)}:{label}:{source}".encode()).hexdigest()[:12]
                yield {
                    "id": key, "file": path.relative_to(root).as_posix(), "line": number,
                    "label": label, "encoding": encoding, "source": source,
                }


def tokens(text: str) -> list[str]:
    return STRUCTURAL_RE.findall(text)


def visible_segments(text: str) -> list[str]:
    """Split an XSE string on its explicit line/page controls."""
    return re.split(r"\\[npl]", TOKEN_RE.sub(lambda m: "" if m.group().startswith("[") else m.group(), text))
