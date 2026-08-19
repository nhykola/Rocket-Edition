#!/usr/bin/env python3
"""Conservative static QA for the French CSV catalogue (no ROM required)."""
from __future__ import annotations
import argparse, collections, csv, json, re
from pathlib import Path
from localization_common import display_lines, immutable_tokens, iter_strings, visible_text

WIDTH = collections.defaultdict(lambda: 6, {" ":4,"i":2,"l":3,"I":3,"t":4,"f":4,".":2,",":2,"!":2,"'":3,"W":8,"M":8})
ENGLISH = re.compile(r"\b(the|you|your|this|that|with|have|are|not|from|what)\b", re.I)
SAFE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?'-:;()/\"+&%#=*<>_éèêëàâäùûüôöîïçÉÈÊËÀÂÄÙÛÜÔÖÎÏÇœŒæÆ…óÀÁ")

def validate(catalogue: Path, root: Path):
    expected_rows=list(iter_strings(root)); expected={r["id"]:r for r in expected_rows}
    issues=[]
    with catalogue.open(encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    counts=collections.Counter(r.get("id","") for r in rows)
    for ident,count in counts.items():
        if count>1: issues.append(("ERREUR",ident,f"ID présent {count} fois"))
    actual=set(counts); wanted=set(expected)
    for ident in sorted(wanted-actual): issues.append(("ERREUR",ident,"ID source absent du catalogue"))
    for ident in sorted(actual-wanted): issues.append(("ERREUR",ident,"ID étranger au catalogue"))
    translated=[]; pairs=collections.defaultdict(set)
    for row in rows:
        src=expected.get(row.get("id")); fr=row.get("fr","").strip()
        if not src: continue
        for field in ("file","label","encoding","source"):
            if row.get(field) != str(src[field]): issues.append(("ERREUR",row["id"],f"champ source `{field}` modifié"))
        if not fr: continue
        translated.append(row)
        if immutable_tokens(src["source"]) != immutable_tokens(fr):
            issues.append(("ERREUR",row["id"],"contrôles immuables absents, altérés ou réordonnés"))
        naked=visible_text(fr,keep_layout=False)
        bad=sorted({c for c in naked if c not in SAFE})
        if bad: issues.append(("ERREUR",row["id"],f"caractères non autorisés: {bad!r}"))
        if ENGLISH.search(naked): issues.append(("AVERTISSEMENT",row["id"],"anglais résiduel probable"))
        try: lines=display_lines(fr)
        except ValueError as exc: issues.append(("ERREUR",row["id"],f"structure de boîte invalide: {exc}")); lines=[]
        for page,rownum,line in lines:
            pixels=sum(WIDTH[c] for c in line)
            if pixels>198: issues.append(("ERREUR",row["id"],f"page {page+1}, ligne {rownum+1}: {pixels}px (>198px)"))
        pairs[src["source"]].add(fr)
    for original,variants in pairs.items():
        if len(variants)>1: issues.append(("AVERTISSEMENT","doublon",f"source identique traduite de {len(variants)} façons: {original[:60]}"))
    for row in expected_rows:
        if not row["label"]: issues.append(("ERREUR",row["id"],"texte sans #org précédent"))
    return rows,translated,issues

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("catalogue",nargs="?",type=Path,default=Path("translation/dialogues_fr.csv")); ap.add_argument("--report",type=Path,default=Path("translation/qa_report.md")); a=ap.parse_args(); root=Path(__file__).resolve().parents[1]
    rows,translated,issues=validate(a.catalogue,root); a.report.parent.mkdir(parents=True,exist_ok=True)
    lines=["# Rapport QA","",f"- Catalogue : **{len(rows)}** chaînes",f"- Traduites : **{len(translated)}**",f"- Problèmes : **{len(issues)}**","","## Résultats",""]+[f"- **{x}** `{i}` — {m}" for x,i,m in issues]
    if not issues: lines.append("Aucun problème détecté.")
    a.report.write_text("\n".join(lines)+"\n",encoding="utf-8")
    progress={"total":len(rows),"translated":len(translated),"reviewed":sum(r.get("status")=="validé" for r in rows),"percent":round(100*len(translated)/len(rows),2) if rows else 0}
    (a.report.parent/"progress.json").write_text(json.dumps(progress,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    pending=[f"{r['id']}\t{r['file']}:{r['line']}\t{r['label']}" for r in rows if not r.get("fr","").strip()]
    (a.report.parent/"untranslated_report.txt").write_text(f"Chaînes non traduites: {len(pending)} / {len(rows)}\n"+"\n".join(pending)+"\n",encoding="utf-8")
    print(f"{len(issues)} problème(s); {len(rows)} chaînes; rapport: {a.report}")
    return 1 if any(x=="ERREUR" for x,_,_ in issues) else 0
if __name__=="__main__": raise SystemExit(main())
