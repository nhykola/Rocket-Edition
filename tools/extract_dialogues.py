#!/usr/bin/env python3
"""Create/update a translation catalogue without touching source scripts."""
from __future__ import annotations

import argparse, csv
from pathlib import Path
from localization_common import iter_strings

FIELDS = ["id", "file", "line", "label", "encoding", "source", "fr", "status", "notes"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    output = args.output or args.root / "translation" / "dialogues_fr.csv"
    previous = {}
    if output.exists():
        with output.open(encoding="utf-8", newline="") as handle:
            old_rows = list(csv.DictReader(handle))
            if len({row["id"] for row in old_rows}) != len(old_rows):
                raise SystemExit("catalogue existant invalide: identifiants dupliqués")
            previous = {row["id"]: row for row in old_rows}
    rows = []
    for item in iter_strings(args.root):
        old = previous.get(item["id"], {})
        item.update(fr=old.get("fr", ""), status=old.get("status", "à_traduire"), notes=old.get("notes", ""))
        rows.append(item)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, FIELDS); writer.writeheader(); writer.writerows(rows)
    print(f"{len(rows)} chaînes extraites vers {output}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
