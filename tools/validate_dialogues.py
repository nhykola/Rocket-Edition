#!/usr/bin/env python3
"""Conservative static QA for the French CSV catalogue (no ROM required)."""
from __future__ import annotations
import argparse, collections, csv, json, re
from pathlib import Path
from localization_common import Control, display_line_parts, immutable_tokens, iter_strings, visible_text
from validate_terminology import load_canonical, validate_prose

WIDTH = collections.defaultdict(lambda: 6, {" ":4,"i":2,"l":3,"I":3,"t":4,"f":4,".":2,",":2,"!":2,"'":3,"W":8,"M":8})
ENGLISH = re.compile(r"\b(the|you|your|this|that|with|have|are|not|from|what)\b", re.I)
SAFE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?'-:;()/\"+&%#=*<>_éèêëàâäùûüôöîïçÉÈÊËÀÂÄÙÛÜÔÖÎÏÇœŒæÆ…óÀÁ")
ALLOWED_STATUSES = {"à_traduire", "traduit", "relu", "validé"}
PLAYER_NAME_LENGTH = 7
WIDEST_GLYPH_PX = 8
DEFAULT_BUFFER_MAX_PX = 96

def placeholder_widths(notes: str, buffer_max_px: int):
    widths={"[player]":PLAYER_NAME_LENGTH*WIDEST_GLYPH_PX,
            "[buffer1]":buffer_max_px,"[buffer2]":buffer_max_px,"[buffer3]":buffer_max_px}
    for name,value in re.findall(r"\b(buffer[123])_max_px=(\d+)\b",notes or ""):
        widths[f"[{name}]"]=int(value)
    return widths

def measured_lines(text: str, notes: str="", buffer_max_px: int=DEFAULT_BUFFER_MAX_PX):
    widths=placeholder_widths(notes,buffer_max_px); result=[]
    for page,row,parts in display_line_parts(text):
        pixels=0; unknown=[]
        for part in parts:
            if isinstance(part,Control):
                key=part.value.lower(); pixels+=widths[key]
                if key.startswith("[buffer") and f"{key[1:-1]}_max_px=" not in (notes or ""): unknown.append(key)
            else: pixels+=sum(WIDTH[c] for c in part)
        result.append((page,row,pixels,unknown))
    return result

def validate(catalogue: Path, root: Path, *, buffer_max_px: int=DEFAULT_BUFFER_MAX_PX):
    expected_rows=list(iter_strings(root)); expected={r["id"]:r for r in expected_rows}
    issues=[]
    with catalogue.open(encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    counts=collections.Counter(r.get("id","") for r in rows)
    for ident,count in counts.items():
        if count>1: issues.append(("ERREUR",ident,f"ID présent {count} fois"))
    actual=set(counts); wanted=set(expected)
    for ident in sorted(wanted-actual): issues.append(("ERREUR",ident,"ID source absent du catalogue"))
    for ident in sorted(actual-wanted): issues.append(("ERREUR",ident,"ID étranger au catalogue"))
    canonical=load_canonical(root/"translation/canonical/canonical_fr_gen3.csv")
    translated=[]; reviewed=[]; validated=[]; pairs=collections.defaultdict(set)
    for row in rows:
        src=expected.get(row.get("id")); fr=row.get("fr","").strip(); status=row.get("status","")
        if status not in ALLOWED_STATUSES: issues.append(("ERREUR",row.get("id",""),f"statut inconnu: `{status}`"))
        if not fr and status in {"traduit","relu","validé"}: issues.append(("ERREUR",row.get("id",""),f"statut `{status}` interdit avec une traduction vide"))
        if fr and status == "à_traduire": issues.append(("ERREUR",row.get("id",""),"texte français présent mais statut `à_traduire`"))
        if not src: continue
        for field in ("file","label","encoding","source"):
            if row.get(field) != str(src[field]): issues.append(("ERREUR",row["id"],f"champ source `{field}` modifié"))
        if not fr: continue
        if status in {"traduit","relu","validé"}: translated.append(row)
        if status in {"relu","validé"}: reviewed.append(row)
        if status == "validé": validated.append(row)
        if immutable_tokens(src["source"]) != immutable_tokens(fr):
            issues.append(("ERREUR",row["id"],"contrôles immuables absents, altérés ou réordonnés"))
        naked=visible_text(fr,keep_layout=False)
        bad=sorted({c for c in naked if c not in SAFE})
        if bad: issues.append(("ERREUR",row["id"],f"caractères non autorisés: {bad!r}"))
        if ENGLISH.search(naked): issues.append(("AVERTISSEMENT",row["id"],"anglais résiduel probable"))
        for level,ident,message in validate_prose(naked,canonical):
            issues.append(("ERREUR" if level=="ERROR" else "REVIEW_REQUIRED",row["id"],f"{ident}: {message}"))
        try: lines=measured_lines(fr,row.get("notes",""),buffer_max_px)
        except ValueError as exc: issues.append(("ERREUR",row["id"],f"structure de boîte invalide: {exc}")); lines=[]
        for page,rownum,pixels,unknown_buffers in lines:
            if pixels>198: issues.append(("ERREUR",row["id"],f"page {page+1}, ligne {rownum+1}: {pixels}px (>198px)"))
            elif unknown_buffers and pixels>170: issues.append(("REVIEW_REQUIRED",row["id"],f"largeur {pixels}px avec buffer contextuel non annoté: {', '.join(unknown_buffers)}"))
        pairs[src["source"]].add(fr)
    for original,variants in pairs.items():
        if len(variants)>1: issues.append(("AVERTISSEMENT","doublon",f"source identique traduite de {len(variants)} façons: {original[:60]}"))
    for row in expected_rows:
        if not row["label"]: issues.append(("ERREUR",row["id"],"texte sans #org précédent"))
    blocking_ids={ident for level,ident,_ in issues if level in {"ERREUR","REVIEW_REQUIRED"}}
    translated=[row for row in translated if row["id"] not in blocking_ids]
    reviewed=[row for row in reviewed if row["id"] not in blocking_ids]
    validated=[row for row in validated if row["id"] not in blocking_ids]
    return rows,translated,reviewed,validated,issues

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("catalogue",nargs="?",type=Path,default=Path("translation/dialogues_fr.csv")); ap.add_argument("--report",type=Path,default=Path("translation/qa_report.md")); ap.add_argument("--buffer-max-px",type=int,default=DEFAULT_BUFFER_MAX_PX); a=ap.parse_args(); root=Path(__file__).resolve().parents[1]
    rows,translated,reviewed,validated,issues=validate(a.catalogue,root,buffer_max_px=a.buffer_max_px); a.report.parent.mkdir(parents=True,exist_ok=True)
    lines=["# Rapport QA","",f"- Catalogue : **{len(rows)}** chaînes",f"- Traduites : **{len(translated)}**",f"- Problèmes : **{len(issues)}**","","## Résultats",""]+[f"- **{x}** `{i}` — {m}" for x,i,m in issues]
    if not issues: lines.append("Aucun problème détecté.")
    a.report.write_text("\n".join(lines)+"\n",encoding="utf-8")
    progress={"total":len(rows),"translated":len(translated),"reviewed":len(reviewed),"validated":len(validated),"percent":round(100*len(translated)/len(rows),2) if rows else 0}
    (a.report.parent/"progress.json").write_text(json.dumps(progress,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    pending=[f"{r['id']}\t{r['file']}:{r['line']}\t{r['label']}" for r in rows if not r.get("fr","").strip()]
    (a.report.parent/"untranslated_report.txt").write_text(f"Chaînes non traduites: {len(pending)} / {len(rows)}\n"+"\n".join(pending)+"\n",encoding="utf-8")
    print(f"{len(issues)} problème(s); {len(rows)} chaînes; rapport: {a.report}")
    return 1 if any(x in {"ERREUR","REVIEW_REQUIRED"} for x,_,_ in issues) else 0
if __name__=="__main__": raise SystemExit(main())
