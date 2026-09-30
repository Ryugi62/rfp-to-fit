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
ev = json.loads((D / "events.json").read_text())

LINES = [  # (기준 장면, 장면 시작 후 초, 문장)
    ("landing", 0.3, "RFP-to-Fit은 국가 R&D 공고의 실제 심사표로, 가상 평가위원 다섯 명이 제안서 초안을 먼저 채점하는 에이전트입니다."),
    ("inputs", 0.2, "넣은 공고는 이 대회 공고입니다. 요건 서른네 개와 본선 심사표 다섯 개를, 쪽 번호와 원문 인용을 붙여 스스로 찾아냈습니다. 초안은 저희 예선 기획서이고, 서버에 저장하지 않습니다."),
    ("click", 0.3, "평가위원 다섯 명이 서로의 답을 모른 채 채점합니다. 구글 제미나이 셋, 국산 업스테이지 솔라 둘입니다. 충족이라고 하려면 초안 원문을 그대로 인용해야 하고, 코드가 대조해서 가짜 인용은 다시 묻습니다."),
    ("result", 0.3, "다섯 명 모두가 깎는 곳은 반드시 고칠 곳, 의견이 갈리는 곳은 연구자가 판단할 곳으로 나뉩니다."),
    ("cards", 0.3, "보완 지정은 문장을 대신 쓰지 않고, 어떤 근거를 어느 절에 넣을지만 알려 줍니다. 평가위원별 판정과 인용도 모두 펼쳐 볼 수 있습니다."),
    ("before_after", 0.3, "이 지적을 받아 저희 기획서에 서비스 흐름도와 화면 구성, 구현 결과를 직접 보강했고, 같은 질문으로 다시 채점했습니다."),
    ("trust", 0.3, "공고 파싱 정확도는 사람이 쪽마다 만든 정답표 대비 요건 재현율 95%와 91%입니다. 코드와 정답표는 모두 공개 저장소에 있습니다."),
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


def main():
    a_end = ev["click"] + 1.5
    wait = ev["done"] - a_end
    speed = max(1.0, wait / 6.0)
    real = ev["done"] - ev["click"]

    def out_t(t):
        if t <= a_end:
            return t
        if t <= ev["done"]:
            return a_end + (t - a_end) / speed
        return a_end + wait / speed + (t - ev["done"])

    clips = [asyncio.run(tts(i, s)) for i, (_, _, s) in enumerate(LINES)]
    starts, cur = [], 0.0
    for (k, off, _), c in zip(LINES, clips):
        st = max(out_t(ev[k]) + off, cur + 0.25)
        starts.append(st)
        cur = st + dur(c)
    video_len = out_t(ev["end"])
    pad = max(0.0, cur + 0.8 - video_len)

    raw = str(D / "raw.webm")
    label = f"실제 {real:.0f}초 · {speed:.0f}배속"
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
    main()
