# Cuts the auto-prompt recording (new todo -> Claude with prefilled prompt -> /clear) into the
# 960x848 = 960x776 zoomed crop + 72px caption bar, 15 fps.
import subprocess, pathlib

SRC = r"C:\Users\sinan\Videos\2026-09-27 16-46-53.mp4"
OUT = r"C:\Users\sinan\Downloads\Marktplatz Seite Cortex\cortex-auto-prompt.gif"
FONT = "C\\:/Windows/Fonts/segoeui.ttf"
W, H, BAR = 960, 776, 72
ACCENT = "0xD97757"  # Claude orange, used for click ring and highlight boxes

# Cameras as (w, h, x, y) in source pixels; all share the 960:776 aspect.
CARD = (1050, 849, 1490, 250)    # todo card + right half of the terminal panel below it
PROMPT = (1200, 970, 400, 540)   # Claude banner + prefilled input line (bottom panel)
CLEAR = (1050, 849, 400, 630)    # input area of the terminal once it sits in the editor

# Boxes in output pixels (x, y, w, h).
TAB_BOX = (530, 430, 196, 40)    # new terminal tab named after the todo (CARD camera)
PROMPT_BOX = (0, 658, 960, 50)   # prefilled Cortex prompt (PROMPT camera)
CLEAR_BOX = (0, 598, 960, 126)   # prompt re-injected after /clear (CLEAR camera)

# (start, end, camera, caption, click_at_src or None, [(box, from_src)])
SEGS = [
    (1.0, 3.9, CARD, "New todo  ›  start Claude with one click", 3.85, []),
    (3.9, 5.0, CARD, "...  a terminal opens, named after the todo", None, [(TAB_BOX, 4.1)]),
    (7.4, 8.5, PROMPT, "Claude starts ...", None, []),
    (8.5, 11.5, PROMPT, "...  with the Cortex prompt already in  ›  just add your request", None,
     [(PROMPT_BOX, 8.5)]),
    (57.9, 59.6, CLEAR, "Later: /clear for a fresh session", None, []),
    (60.6, 64.5, CLEAR, "The todo context is loaded again  ›  keep going", None,
     [(CLEAR_BOX, 61.0)]),
]

# Click positions in output pixels for segments with a click.
CLICK_POS = {3.85: (835, 144)}

RING = 160  # ripple canvas size
ring_src = (
    f"color=c=black@0:s={RING}x{RING}:r=15:d=0.6,format=rgba,"
    # expanding ring that fades out + a short solid dot at the click point
    f"geq=r=217:g=119:b=87:a='min(255,255*(1-T/0.6)*max(0,1-abs(hypot(X-80,Y-80)-(12+T*105))/8)"
    f"+200*max(0,1-T/0.25)*lt(hypot(X-80,Y-80),16))'"
)

parts, labels = [], []
for i, (a, b, (cw, ch, cx, cy), txt, click, boxes) in enumerate(SEGS):
    txt = txt.replace("'", "\u2019").replace(":", "\\:")
    f = (f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,crop={cw}:{ch}:{cx}:{cy},"
         f"scale={W}:{H}:flags=lanczos,setsar=1")
    for (bx, by, bw, bh), t0 in boxes:
        f += (f",drawbox=x={bx}:y={by}:w={bw}:h={bh}:color={ACCENT}:t=3"
              f":enable='gte(t,{t0 - a:.2f})'")
    f += f",pad={W}:{H + BAR}:0:0:0x171818"
    f += (f",drawtext=fontfile='{FONT}':text='{txt}':fontsize=28:fontcolor=0xE6E6E6"
          f":x=(w-tw)/2:y={H}+({BAR}-th)/2,fps=15")
    if click is None:
        parts.append(f + f"[v{i}]")
    else:
        px, py = CLICK_POS[click]
        parts.append(f + f"[b{i}]")
        parts.append(f"{ring_src},setpts=PTS-STARTPTS+{click - a:.2f}/TB[r{i}]")
        parts.append(f"[b{i}][r{i}]overlay=x={px - RING // 2}:y={py - RING // 2}:eof_action=pass[v{i}]")
    labels.append(f"[v{i}]")

parts.append("".join(labels) + f"concat=n={len(SEGS)}:v=1:a=0,split[a][b]")
parts.append("[a]palettegen=max_colors=256:stats_mode=diff[p]")
parts.append("[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle")

filt = pathlib.Path(__file__).with_name("filter.txt")
filt.write_text(";\n".join(parts), encoding="utf-8")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-/filter_complex", str(filt),
                "-loop", "0", OUT], check=True)
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
                      "-of", "compact", OUT], capture_output=True, text=True).stdout)
