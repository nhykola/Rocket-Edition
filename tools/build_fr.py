#!/usr/bin/env python3
"""Safe localization build entry point (currently a documented preflight)."""
import argparse, hashlib
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--rom",required=True,type=Path,help="Rocket Edition anglaise locale"); ap.add_argument("--catalogue",type=Path,default=Path("translation/dialogues_fr.csv")); a=ap.parse_args()
    if not a.rom.is_file(): ap.error("ROM locale introuvable")
    head=a.rom.read_bytes()[:192]
    if len(head)<192 or head[0xB2] != 0x96: ap.error("en-tête GBA invalide")
    digest=hashlib.sha256(a.rom.read_bytes()).hexdigest()
    print(f"ROM locale valide (SHA-256 {digest}); catalogue: {a.catalogue}")
    print("ARRÊT SÛR: l'injecteur et la table de caractères ne sont pas encore qualifiés. Voir LOCALIZATION_PLAN.md.")
    return 2
if __name__ == "__main__": raise SystemExit(main())
