#!/usr/bin/env python3
"""Validate canonical Gen III terms by internal ID and cautiously in prose."""
from __future__ import annotations
import argparse, csv, re
from pathlib import Path

FIELDS={"category","internal_id","english_key","english_display","french_canonical","rom_display_fr","source","verification_status","notes"}

def load_canonical(path: Path):
    with path.open(encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    if not FIELDS.issubset(rows[0] if rows else {}): raise ValueError("colonnes canoniques absentes")
    result={}
    for row in rows:
        ident=row["internal_id"]
        if not ident or ident in result: raise ValueError(f"identifiant vide/dupliqué: {ident}")
        if row["verification_status"] not in {"verified","review_required"}: raise ValueError(f"statut invalide: {ident}")
        result[ident]=row
    return result

def validate_assignments(rows, canonical):
    """Tables ROM and explicit annotations are always checked strictly by ID."""
    issues=[]
    for row in rows:
        ident=row.get("internal_id",""); value=row.get("french","")
        term=canonical.get(ident)
        if not term: issues.append(("REVIEW_REQUIRED",ident,"identifiant canonique inconnu"))
        elif term["verification_status"] != "verified": issues.append(("REVIEW_REQUIRED",ident,"terme non vérifié"))
        elif value != term["french_canonical"]: issues.append(("ERROR",ident,f"attendu « {term['french_canonical']} », reçu « {value} »"))
    return issues

def validate_prose(text: str, canonical):
    """Flag English terms; ambiguous one-word move names require human context."""
    issues=[]; occupied=[]
    # Longest first prevents `Thunder` from shadowing the unambiguous
    # `Thunder Wave` at the same location.
    for term in sorted(canonical.values(),key=lambda row:len(row["english_display"]),reverse=True):
        english=term["english_display"]
        matches=list(re.finditer(r"(?<![\w-])"+re.escape(english)+r"(?![\w-])",text,re.I))
        fresh=[match for match in matches if not any(match.start()<end and match.end()>start for start,end in occupied)]
        if fresh:
            severity="ERROR" if term["category"]=="species" or " " in english else "REVIEW_REQUIRED"
            issues.append((severity,term["internal_id"],f"terme anglais détecté; canonique: {term['french_canonical']}"))
            occupied.extend((match.start(),match.end()) for match in fresh)
    return issues

def main():
    root=Path(__file__).resolve().parents[1]
    ap=argparse.ArgumentParser(); ap.add_argument("--canonical",type=Path,default=root/"translation/canonical/canonical_fr_gen3.csv"); ap.add_argument("--catalogue",type=Path,default=root/"translation/dialogues_fr.csv",help="catalogue contrôlé par défaut"); ap.add_argument("--assignments",type=Path); ap.add_argument("--text"); a=ap.parse_args()
    canonical=load_canonical(a.canonical); issues=[]
    if a.assignments:
        with a.assignments.open(encoding="utf-8",newline="") as h: issues+=validate_assignments(list(csv.DictReader(h)),canonical)
    if a.text is not None: issues+=validate_prose(a.text,canonical)
    scanned=0
    if a.catalogue:
        with a.catalogue.open(encoding="utf-8",newline="") as h:
            for row in csv.DictReader(h):
                fr=row.get("fr","").strip()
                if fr:
                    scanned+=1
                    issues += validate_prose(fr,canonical)
    for level,ident,message in issues: print(f"{level} {ident}: {message}")
    print(f"{len(canonical)} termes canoniques chargés; {scanned} traduction(s) contrôlée(s); {len(issues)} problème(s)")
    return 1 if issues else 0
if __name__=="__main__": raise SystemExit(main())
