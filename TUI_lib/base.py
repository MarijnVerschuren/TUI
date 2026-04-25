import sys
import termios
import tty
import select
import re

from typing import Literal


__all__ = [
	"BOLD",
	"BOLD_OFF",
	"UNDERLINE",
	"UNDERLINE_OFF",
	"COL_RESET",
	"Terminal",
	"Frame_Buffer",
	"rgb_fg",
	"rgb_bg",
	"gradient_text",
	"format_tabs",
	"visible_len",
	"ansi_safe_truncate",
	"ansi_safe_truncate_and_pad"
]


# ============================================================
# terminal
# ============================================================
class Terminal(object):
	def __init__(self) -> None:
		self.fd =   sys.stdin.fileno()
		self.attr = termios.tcgetattr(self.fd)
	
	def __enter__(self) -> "Terminal":
		tty.setcbreak(self.fd)
		print("\033[?25l", end="")  # hide cursor
		print("\033[2J", end="")	# clear once
		return self
	
	def __exit__(self, *args) -> None:
		termios.tcsetattr(self.fd, termios.TCSADRAIN, self.attr)
		print("\033[0m\033[?25h")   # reset + show cursor
		print("\033[H", end="\033[2J")
	
	def get_key(self) -> bytes or str or None:
		if not select.select([sys.stdin], [], [], 0)[0]:
			return None
		ch = sys.stdin.read(1)
		if ch == "\n": return "enter"
		if ch != "\x1b": return ch
		arrow = sys.stdin.read(2)[1]
		return {"A": "up", "B": "down", "C": "right", "D": "left"}[arrow]
	


# ============================================================
# frame buffer
# ============================================================
class Frame_Buffer:
	def __init__(self) -> None:
		self.front = {}
		self.back = {}
	
	@property
	def layers(self) -> int:
		if not self.back: return 0
		return max(self.back.keys()) + 1
	
	def draw(self, x: int, y: int, text: str, layer: int = 0) -> None:
		if layer not in self.back: self.back[layer] = {}
		self.back[layer][(x, y)] = text
	
	
	def swap(self) -> None:
		for i in range(self.layers):
			if i not in self.back: continue
			for pos, text in self.back[i].items():
				if self.front.get(pos) != text:
					x, y = pos
					sys.stdout.write(f"\033[{y};{x}H{text}")
		
		sys.stdout.flush()
		self.front = self.back
		self.back = {}
	
	
	def clear(self) -> None:
		self.front = {}
		self.back = {}
		sys.stdout.write("\033[2J")
		sys.stdout.flush()



# ============================================================
# color functions
# ============================================================
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
COL_RESET =	"\033[0m"
BOLD =		"\033[1m"
BOLD_OFF =	"\033[22m"
UNDERLINE = "\033[4m"
UNDERLINE_OFF = "\033[24m"

def rgb_fg(r: int, g: int, b: int) -> str:
	return f"\033[38;2;{r};{g};{b}m"


def rgb_bg(r, g, b) -> str:
	return f"\033[48;2;{r};{g};{b}m"


def gradient_text(text, start_rgb, end_rgb) -> str:
	sr, sg, sb = start_rgb
	er, eg, eb = end_rgb
	length = max(len(text) - 1, 1)
	out = ""
	
	for i, ch in enumerate(text):
		t = i / length
		r = int(sr + (er - sr) * t)
		g = int(sg + (eg - sg) * t)
		b = int(sb + (eb - sb) * t)
		out += f"\033[38;2;{r};{g};{b}m{ch}"
	return out + COL_RESET



def format_tabs(text: str) -> str:
	if "\t" not in text: return text
	skip = 0; out = []
	for i, ch in enumerate(text):
		if ch == '\t':
			s = 3 - ((i+skip) % 4) # tab char is already counted
			skip += s; out.extend([' '] * (s + 1))
		else: out.append(ch)
	return ''.join(out)
	


def visible_len(text: str) -> int:
	return len(ANSI_RE.sub("", text))


def ansi_safe_truncate(text: str, width: int) -> str:
	out = []; visible = 0; i = 0
	
	while i < len(text) and visible < width:
		if text[i] == "\033" and (m := ANSI_RE.match(text, i)):
			seq = m.group(0)
			out.append(seq)
			i += len(seq)
			continue
			
		out.append(text[i])
		visible += 1
		i += 1
		
	result = "".join(out)
	if ANSI_RE.search(result) and not result.endswith(COL_RESET):
		result += COL_RESET
		
	return result


def ansi_safe_truncate_and_pad(text: str, pad_ch: str, width: int, pad_method: Literal["R", "L", "C"] = "R") -> str:
	t = format_tabs(text)
	tlen = visible_len(t)
	t = ansi_safe_truncate(t, width)
	if pad_method == "R":
		return f"{t}{(pad_ch * (max(width-tlen, 0)))}"
	if pad_method == "L":
		return f"{(pad_ch * (max(width-tlen, 0)))}{t}"
	pad_c = max(width-tlen, 0)
	return f"{(pad_ch * (pad_c // 2))}{t}{(pad_ch * (pad_c // 2))}"