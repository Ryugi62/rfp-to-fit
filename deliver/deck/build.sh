#!/usr/bin/env bash
# 덱 재빌드 — 숫자는 data/ JSON에서 빌드 시점에 다시 읽는다.
#   bash deliver/deck/build.sh            (LIVE_URL=https://... bash deliver/deck/build.sh 로 주소 교체)
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/node/bin:$PATH"
SOFFICE="${SOFFICE_BIN:-$HOME/Applications/LibreOffice.app/Contents/MacOS/soffice}"
NAME="RFP-to-Fit_루미아"
PY="uv run --no-project --with pypdfium2 --with pillow --with qrcode python"
cd "$D"
[ -d node_modules/pptxgenjs ] || npm install --silent
$PY prepare.py > /dev/null || exit 1   # WARN·STOP 줄은 stderr로 보인다
node deck.js "$D/$NAME.pptx"
rm -f "$D/$NAME.pdf"
"$SOFFICE" --headless --convert-to pdf --outdir "$D" "$D/$NAME.pptx" > /dev/null 2>&1
rm -rf "$D/png" && mkdir -p "$D/png"
$PY -c "
import pypdfium2 as p
d=p.PdfDocument('$D/$NAME.pdf')
for i,pg in enumerate(d): pg.render(scale=2).to_pil().save(f'$D/png/slide-{i+1:02d}.png')
print('pages', len(d))"
uv run --no-project --python 3.12 --with lxml --with defusedxml python ~/.claude/skills/pptx/scripts/office/validate.py "$D/$NAME.pptx" | tail -3
# 자리표시·잔재 검사
$PY -c "
import zipfile,re,sys
z=zipfile.ZipFile('$D/$NAME.pptx'); txt=' '.join(z.read(n).decode('utf8','ignore') for n in z.namelist() if n.startswith('ppt/slides/slide'))
bad=[w for w in ['측정 중','undefined','NaN','null','TODO','{'+'}'] if w in re.sub('<[^>]+>','',txt)]
print('자리표시:', bad or '없음')"
