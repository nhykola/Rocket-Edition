#!/usr/bin/env python3
"""Conservative static QA for the French CSV catalogue (no ROM required)."""
from __future__ import annotations

import argparse, collections, csv, json, re
from pathlib import Path
from localization_common import iter_strings, tokens, visible_segments

# Approximation until the exact Rocket Edition font and glyph widths are extracted.
WIDTH = collections.defaultdict(lambda: 6, {" ": 4, "i": 2, "l": 3, "I": 3, "t": 4, "f": 4, ".": 2, ",": 2, "!": 2, "'": 3, "W": 8, "M": 8})
ENGLISH = re.compile(r"\b(the|you|your|this|that|with|have|are|not|from|what|Rocket|Pok[eé]mon)\b", re.I)
SAFE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?'-:;()/\"+&%#=*<>_éèêëàâäùûüôöîïçÉÈÊËÀÂÄÙÛÜÔÖÎÏÇœŒæÆ…")


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("catalogue", nargs="?", type=Path, default=Path("translation/dialogues_fr.csv")); ap.add_argument("--report", type=Path, default=Path("translation/qa_report.md")); args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = {r["id"]: r for r in iter_strings(root)}
    issues=[]; translated=[]; pairs=collections.defaultdict(set)
    with args.catalogue.open(encoding="utf-8", newline="") as h:
        rows=list(csv.DictReader(h))
    for row in rows:
        fr=row.get("fr", "").strip()
        if not fr: continue
        translated.append(row); src=source.get(row["id"])
        if not src: issues.append(("ERREUR", row["id"], "identifiant source introuvable")); continue
        if collections.Counter(tokens(src["source"])) != collections.Counter(tokens(fr)):
            issues.append(("ERREUR", row["id"], "commandes/placeholders différents de la source"))
        naked=re.sub(r"\[[^]]+\]|\\[^\s]+", "", fr)
        bad=sorted({c for c in naked if c not in SAFE})
        if bad: issues.append(("ERREUR", row["id"], f"caractères non autorisés (support ROM à confirmer): {bad!r}"))
        if ENGLISH.search(naked): issues.append(("AVERTISSEMENT", row["id"], "anglais résiduel probable"))
        for segment in visible_segments(fr):
            pixels=sum(WIDTH[c] for c in segment)
            if pixels > 198: issues.append(("AVERTISSEMENT", row["id"], f"ligne estimée à {pixels}px (>198px)"))
        pairs[src["source"]].add(fr)
    for original, variants in pairs.items():
        if len(variants)>1: issues.append(("AVERTISSEMENT", "doublon", f"source identique traduite de {len(variants)} façons: {original[:60]}"))
    # Lightweight XSE source sanity, useful after future catalogue application.
    for row in source.values():
        if not row["label"]: issues.append(("ERREUR", row["id"], "texte sans #org précédent"))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    lines=["# Rapport QA", "", f"- Catalogue : **{len(rows)}** chaînes", f"- Traduites : **{len(translated)}**", f"- Problèmes : **{len(issues)}**", "", "## Résultats", ""]
    lines += [f"- **{level}** `{ident}` — {message}" for level,ident,message in issues] or ["Aucun problème détecté."]
    args.report.write_text("\n".join(lines)+"\n", encoding="utf-8")
    progress={"total":len(rows),"translated":len(translated),"reviewed":sum(r.get("status")=="validé" for r in rows),"percent":round(100*len(translated)/len(rows),2) if rows else 0}
    (args.report.parent/"progress.json").write_text(json.dumps(progress,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    pending=[f"{r['id']}\t{r['file']}:{r['line']}\t{r['label']}" for r in rows if not r.get("fr", "").strip()]
    (args.report.parent/"untranslated_report.txt").write_text(
        f"Chaînes non traduites: {len(pending)} / {len(rows)}\n"+"\n".join(pending)+"\n", encoding="utf-8")
    print(f"{len(issues)} problème(s); rapport: {args.report}")
    return 1 if any(i[0]=="ERREUR" for i in issues) else 0

if __name__ == "__main__": raise SystemExit(main())
