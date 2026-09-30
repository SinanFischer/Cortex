# Cuts the session-resume recording into the cortex-intro-v3 GIF format:
# 960x848 = 960x776 zoomed crop + 72px caption bar, 15 fps.
import subprocess, pathlib

SRC = r"C:\Users\sinan\Videos\2026-09-27 16-27-51.mp4"
OUT = r"C:\Users\sinan\Downloads\Marktplatz Seite Cortex\cortex-claude-sessions.gif"
FONT = "C\\:/Windows/Fonts/segoeui.ttf"
W, H, BAR = 960, 776, 72
ACCENT = "0xD97757"  # Claude orange, used for click ring and highlight boxes

# Cameras as (w, h, x, y) in source pixels; all share the 960:776 aspect.
CARD = (1040, 841, 1500, 260)   # todo card with its session list
WIDE = (1260, 1019, 1280, 250)  # card + terminal panel below: shows the terminal being created
CHAT = (1050, 849, 400, 50)     # resumed Claude chat incl. its editor tab title

# Boxes in output pixels (x, y, w, h), valid for the WIDE camera.
TAB_BOX = (600, 352, 172, 46)   # the new terminal tab
CMD_BOX = (0, 410, 456, 32)     # the "claude --resume <id>" line

# (start, end, camera, caption, click_at_src or None, [(box, from_src)])
SEGS = [
    (0.5, 3.9, CARD, "Every Claude session lives on its todo", None, []),
    (3.9, 5.2, WIDE, "One click on the todo ...", 5.15, []),
    (5.2, 6.35, WIDE, "...  opens a new terminal and resumes the session", None,
     [(TAB_BOX, 5.55), (CMD_BOX, 6.2)]),
    (9.2, 10.6, CHAT, "The whole conversation is back", None, []),
    (21.4, 24.0, CARD, "Context and cost of every session", None, []),
    (27.6, 29.4, WIDE, "Any past session  ›  one click", 29.35, []),
    (29.4, 30.55, WIDE, "...  its own terminal, resumed", None,
     [(TAB_BOX, 29.75), (CMD_BOX, 30.3)]),
    (33.0, 34.6, CHAT, "Back in flow. Nothing lost.", None, []),
]

# Click positions in output pixels for segments with a click.
CLICK_POS = {5.15: (790, 122), 29.35: (267, 427)}

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
