#!/usr/bin/env python3
"""Generate a BPS patch from two local ROMs; neither ROM is copied into the repo."""
from __future__ import annotations
import argparse, binascii, struct
from pathlib import Path

def number(value: int) -> bytes:
    out=bytearray()
    while True:
        byte=value & 0x7f; value >>= 7
        if value: out.append(byte | 0x80); value -= 1
        else: out.append(byte); return bytes(out)

def create_bps(source: bytes, target: bytes) -> bytes:
    patch=bytearray(b"BPS1")+number(len(source))+number(len(target))+number(0)
    pos=0
    while pos < len(target):
        same=pos < len(source) and source[pos]==target[pos]
        end=pos+1
        while end < len(target) and (end < len(source) and source[end]==target[end])==same: end+=1
        patch += number(((end-pos-1)<<2) | (0 if same else 1))
        if not same: patch += target[pos:end]
        pos=end
    patch += struct.pack("<I", binascii.crc32(source)&0xffffffff)
    patch += struct.pack("<I", binascii.crc32(target)&0xffffffff)
    patch += struct.pack("<I", binascii.crc32(patch)&0xffffffff)
    return bytes(patch)

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--source-rom",required=True,type=Path); ap.add_argument("--target-rom",required=True,type=Path); ap.add_argument("--output",required=True,type=Path); a=ap.parse_args()
    if a.output.suffix.lower() != ".bps": ap.error("la sortie doit porter l'extension .bps")
    if a.output.resolve() in {a.source_rom.resolve(),a.target_rom.resolve()}: ap.error("la sortie ne peut pas écraser une ROM")
    data=create_bps(a.source_rom.read_bytes(),a.target_rom.read_bytes()); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(data)
    print(f"Patch BPS écrit: {a.output} ({len(data)} octets)")
if __name__ == "__main__": main()
