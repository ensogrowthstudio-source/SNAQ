#!/usr/bin/env python3
"""Ajutor pentru exploded.png: arata randurile ocupate (straturi) in % din inaltime.
Straturile care se ating (ex. branza peste carne) apar unite: le imparti de mana in products.json.
  python3 ux/tools/bands.py assets/gen/double-bacon/exploded.png"""
import sys
from PIL import Image
import numpy as np
im = Image.open(sys.argv[1]).convert("RGB")
a = np.asarray(im.resize((im.width // 4, im.height // 4))).max(axis=2)
rows = (a > 55).sum(axis=1) > a.shape[1] * 0.01
runs, s = [], None
for y, v in enumerate(rows):
    if v and s is None: s = y
    if not v and s is not None: runs.append([s, y]); s = None
if s is not None: runs.append([s, len(rows)])
m = []
for r in runs:
    if m and r[0] - m[-1][1] < a.shape[0] * 0.006: m[-1][1] = r[1]
    else: m.append(r)
H = a.shape[0]
cols = np.where((a > 55).any(axis=0))[0]
print(f"{len(m)} straturi detectate; continut pe latime {cols.min()/a.shape[1]:.2f}-{cols.max()/a.shape[1]:.2f}; aspect imagine {im.width/im.height:.3f}")
for i, (x, y) in enumerate(m):
    print(f"  {i}: {x/H*100:5.1f} - {y/H*100:5.1f}")
bounds = [0] + [round((m[i][1] + m[i + 1][0]) / 2 / H * 100, 2) for i in range(len(m) - 1)] + [100]
print("granite (punct de pornire pentru band):", bounds)
