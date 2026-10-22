#!/bin/bash
# build -> validate -> PowerPoint PNG export -> contact sheets
set -e
S=/tmp/claude-1000/-home-cappu-code-QC2026-27/8753e823-d4bc-48b5-9136-203a9f17fa94/scratchpad
SK=/home/cappu/.claude/skills/synced/18a0f9f9-4327-4d6e-a959-f2351bdc4a2b_dfd95597-fde4-4fef-ae2b-7f9fc81a1024/pptx
cd "$S/deck"
OUT=${1:-RSA_Shor_lecture.pptx}
"$S/venv/bin/python" build_deck.py "$OUT"
~/anaconda3/envs/IQMQ/bin/python "$SK/scripts/office/validate.py" "$OUT" --original template.pptx 2>&1 | grep -v libtinfo | tail -4
rm -rf out_png; mkdir -p out_png
UP=$(wslpath -w "$PWD/$OUT"); UO=$(wslpath -w "$PWD/out_png")
powershell.exe -NoProfile -Command "try { \$app = New-Object -ComObject PowerPoint.Application; \$p = \$app.Presentations.Open('$UP', \$true, \$false, \$false); \$n = \$p.Slides.Count; \$p.Export('$UO', 'PNG', 1280, 720); \$p.Close(); \$app.Quit(); \"exported \$n\" } catch { \"ERR: \$_\" }" 2>&1 | tail -1
~/anaconda3/envs/IQMQ/bin/python - <<'PY' 2>&1 | grep -v libtinfo
from PIL import Image, ImageDraw
import glob, re
files = sorted(glob.glob("out_png/*.PNG"), key=lambda f: int(re.search(r"(\d+)\.PNG", f).group(1)))
W, H, cols, per = 1280, 720, 2, 6
for k0 in range(0, len(files), per):
    chunk = files[k0:k0+per]; rows = (len(chunk)+cols-1)//cols
    img = Image.new("RGB", (cols*W, rows*(H+30)), "white"); d = ImageDraw.Draw(img)
    for k, f in enumerate(chunk):
        x, y = (k % cols)*W, (k//cols)*(H+30)
        img.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y+30)); d.text((x+8, y+8), f"slide {k0+k+1}", fill="red")
    img.save(f"qa-{k0//per+1}.jpg", quality=85)
print("sheets:", len(range(0, len(files), per)), "slides:", len(files))
PY
