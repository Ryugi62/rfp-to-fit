"""녹화본 + edge-tts 내레이션 → deliver/demo/RFP-to-Fit_demo.mp4
대기 구간(버튼 클릭 → 결과)은 약 6초로 배속하고 화면 하단에 「실제 N초 · k배속」을 표기한다."""
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
D = Path("deliver/demo")
VOICE = "ko-KR-InJoonNeural"
FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
ev = json.loads((D / "events.json").read_text()) if (D / "events.json").exists() else {}

LINES = [  # (기준 장면, 장면 시작 후 초, 문장)
    ("landing", 0.3, "RFP-to-Fit은 심사 결과를 맞히는 AI가 아니라, 공고가 요구하는데 내 초안에 근거가 없는 곳을 제출 전에 원문으로 짚어 주는 에이전트입니다."),
    ("inputs", 0.2, "공고 링크를 붙여넣으면, 공지에 붙은 첨부 중 공고문을 스스로 골라 한글 파일까지 열고, 요건과 심사표를 쪽 번호와 원문 인용으로 뽑습니다."),
    ("click", 0.3, "초안을 넣으면 실제 심사 경험에서 나온 관점 여섯 개가 서로 모른 채 근거를 찾습니다. 충족이라고 하려면 초안 원문을 그대로 인용해야 하고, 원문에 없는 인용은 코드가 걸러 다시 묻습니다."),
    ("result", 0.3, "모든 관점이 근거를 못 찾은 곳은 고칠 곳, 관점이 갈린 곳은 판정하지 않고 연구자에게 넘깁니다."),
    ("cards", 0.3, "원문 보기를 누르면 공고 쪽과 초안 위치가 강조되고, 맞음과 틀림을 누르면 사람이 확인한 정밀도가 화면에 쌓입니다."),
    ("before_after", 0.3, "이 대회 심사표로 저희 기획서를 먼저 검사해, 관점별로 걸리는 점을 발표 전에 받았습니다."),
    ("trust", 0.3, "신뢰는 맞히는 것이 아니라 확인할 수 있는 것으로 정의했습니다. 처음 보는 공고 두 건과 제거 실험의 숫자, 코드와 정답표는 모두 공개 저장소에 있습니다."),
]


def dur(path: Path) -> float:
    r = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


async def tts(i: int, text: str) -> Path:
    import edge_tts
    p = D / f"n{i}.mp3"
    await edge_tts.Communicate(text, VOICE, rate="+8%").save(str(p))
    return p


def make_tts():
    clips = [asyncio.run(tts(i, s)) for i, (_, _, s) in enumerate(LINES)]
    (D / "narr.json").write_text(json.dumps({k: round(dur(c), 2) for (k, _, _), c in zip(LINES, clips)}, indent=1))
    print((D / "narr.json").read_text())


def main():
    narr = json.loads((D / "narr.json").read_text())
    a_end = ev["click"] + 1.5
    wait = ev["done"] - a_end
    speed = max(1.0, wait / max(4.0, narr["click"] + 0.6 - 1.5))
    real = ev["done"] - ev["click"]

    def out_t(t):
        if t <= a_end:
            return t
        if t <= ev["done"]:
            return a_end + (t - a_end) / speed
        return a_end + wait / speed + (t - ev["done"])

    clips = [D / f"n{i}.mp3" for i in range(len(LINES))]
    starts, cur = [], 0.0
    for (k, off, _), c in zip(LINES, clips):
        st = max(out_t(ev[k]) + off, cur + 0.25)
        starts.append(st)
        cur = st + dur(c)
    video_len = out_t(ev["end"])
    pad = max(0.0, cur + 0.8 - video_len)

    raw = str(D / "raw.webm")
    label = f"실제 {real:.0f}초 · {speed:.0f}배속" if speed >= 1.5 else f"실제 대기 {real:.0f}초(편집 없음)"
    vf = (f"[0:v]trim=0:{a_end},setpts=PTS-STARTPTS[a];"
          f"[0:v]trim={a_end}:{ev['done']},setpts=(PTS-STARTPTS)/{speed},"
          f"drawtext=fontfile={FONT}:text='{label}':fontsize=30:fontcolor=white:box=1:boxcolor=0x191F28CC:boxborderw=14:"
          f"x=(w-text_w)/2:y=h-80[w];"
          f"[0:v]trim={ev['done']}:{ev['end']},setpts=PTS-STARTPTS[c];"
          f"[a][w][c]concat=n=3:v=1:a=0,tpad=stop_mode=clone:stop_duration={pad:.2f},fps=30,format=yuv420p[v]")
    inputs = ["-i", raw]
    amix = []
    for i, (c, st) in enumerate(zip(clips, starts)):
        inputs += ["-i", str(c)]
        ms = int(st * 1000)
        amix.append(f"[{i + 1}:a]adelay={ms}|{ms}[n{i}]")
    af = ";".join(amix) + ";" + "".join(f"[n{i}]" for i in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0[aud]"
    out = D / "RFP-to-Fit_demo.mp4"
    cmd = [FF, "-y", *inputs, "-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[aud]",
           "-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); sys.exit(1)
    print(out, f"{dur(out):.1f}s", "speed", round(speed, 1), "starts", [round(s, 1) for s in starts])


if __name__ == "__main__":
    make_tts() if sys.argv[1:] == ["tts"] else main()
