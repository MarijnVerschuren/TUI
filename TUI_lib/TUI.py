import sys
import termios
import tty
import select
import shutil
import re
import time


# ============================================================
# terminal and color functions
# ============================================================
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

COL_RESET = "\033[0m"

# NAMED_COLORS = {
#     "black": (0,0,0),
#     "red": (128,0,0),
#     "green": (0,128,0),
#     "yellow": (128,128,0),
#     "blue": (0,0,128),
#     "magenta": (128,0,128),
#     "cyan": (0,128,128),
#     "white": (192,192,192),
#
#     "bright_black": (128,128,128),
#     "bright_red": (255,0,0),
#     "bright_green": (0,255,0),
#     "bright_yellow": (255,255,0),
#     "bright_blue": (0,0,255),
#     "bright_magenta": (255,0,255),
#     "bright_cyan": (0,255,255),
#     "bright_white": (255,255,255),
#     "navy_blue": (0,0,95),
#     "dark_blue": (0,0,135),
#     "blue3": (0,0,215),
#     "blue1": (0,0,255),
#     "dodger_blue3": (0,95,215),
#     "dodger_blue2": (0,95,255),
#     "dodger_blue1": (0,135,255),
#     "deep_sky_blue4": (0,95,175),
#     "deep_sky_blue3": (0,135,215),
#     "deep_sky_blue2": (0,175,215),
#     "deep_sky_blue1": (0,175,255),
#     "sky_blue2": (135,175,255),
#     "sky_blue1": (135,215,255),
#     "light_sky_blue3": (135,175,215),
#     "dark_green": (0,95,0),
#     "green4": (0,135,0),
#     "spring_green4": (0,135,95),
#     "spring_green3": (0,175,95),
#     "chartreuse2": (135,215,0),
#     "chartreuse1": (135,255,0),
#     "light_green": (135,255,135),
#     "pale_green3": (135,215,135),
#     "dark_sea_green": (135,175,135),
#     "dark_cyan": (0,175,135),
#     "light_sea_green": (0,175,175),
#     "aquamarine1": (135,255,215),
#     "dark_slate_gray1": (135,255,255),
#     "dark_slate_gray3": (135,215,215),
#     "red1": (255,0,0),
#     "deep_pink4": (175,0,95),
#     "deep_pink2": (255,0,95),
#     "deep_pink1": (255,0,175),
#     "hot_pink": (255,95,215),
#     "indian_red1": (255,95,135),
#     "pale_violet_red1": (255,135,175),
#     "light_coral": (255,135,135),
#     "purple": (175,0,255),
#     "dark_violet": (175,0,215),
#     "magenta1": (255,0,255),
#     "magenta2": (255,0,215),
#     "medium_violet_red": (175,0,135),
#     "medium_orchid1": (255,95,255),
#     "medium_orchid3": (175,95,175),
#     "orchid1": (255,135,255),
#     "orchid2": (255,135,215),
#     "plum1": (255,175,255),
#     "orange_red1": (255,95,0),
#     "dark_orange": (255,135,0),
#     "orange1": (255,175,0),
#     "gold1": (255,215,0),
#     "yellow1": (255,255,0),
#     "light_goldenrod1": (255,255,95),
#     "light_goldenrod2": (255,215,135),
#     "khaki1": (255,255,135),
#     "wheat1": (255,255,175),
#     "navajo_white1": (255,215,175),
#     "sandy_brown": (255,175,95),
#     "light_salmon1": (255,175,135),
#     "salmon1": (255,135,95),
#     "light_pink1": (255,175,175),
#     "pink1": (255,175,215),
#     "misty_rose1": (255,215,215),
#     "thistle1": (255,215,255),
#     "grey0": (0,0,0),
#     "grey3": (8,8,8),
#     "grey7": (18,18,18),
#     "grey11": (28,28,28),
#     "grey15": (38,38,38),
#     "grey19": (48,48,48),
#     "grey23": (58,58,58),
#     "grey27": (68,68,68),
#     "grey30": (78,78,78),
#     "grey35": (88,88,88),
#     "grey39": (98,98,98),
#     "grey42": (108,108,108),
#     "grey46": (118,118,118),
#     "grey50": (128,128,128),
#     "grey54": (138,138,138),
#     "grey58": (148,148,148),
#     "grey62": (158,158,158),
#     "grey66": (168,168,168),
#     "grey70": (178,178,178),
#     "grey74": (188,188,188),
#     "grey78": (198,198,198),
#     "grey82": (208,208,208),
#     "grey85": (218,218,218),
#     "grey89": (228,228,228),
#     "grey93": (238,238,238)
# }
#
# STYLE_CODES = {
# 	"bold": "\033[1m",
# 	"dim": "\033[2m",
# 	"italic": "\033[3m",
# 	"underline": "\033[4m",
# 	"blink": "\033[5m",
# 	"reverse": "\033[7m",
# 	"strike": "\033[9m",
# }


class Terminal:
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
		print("\033[H", end="")
	
	def get_key(self) -> bytes or str or None:
		if select.select([sys.stdin], [], [], 0)[0]:
			return sys.stdin.read(1)
		return None



def rgb_fg(r: int, g: int, b: int) -> str:
	return f"\033[38;2;{r};{g};{b}m"


def rgb_bg(r, g, b):
	return f"\033[48;2;{r};{g};{b}m"


def gradient_text(text, start_rgb, end_rgb):
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
	skip = 0; out = []
	for i, ch in enumerate(text):
		if ch == '\t':
			s = 3 - ((i+skip) % 4) # tab char is already counted
			skip += s; out.extend([' '] * (s + 1))
		else: out.append(ch)
	return ''.join(out)
	

# if tabs are left in the following functions will not work!
def visible_len(text: str) -> int:
	return len(ANSI_RE.sub("", text))


def ansi_safe_truncate(text: str, width: int):
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



# ============================================================
# frame buffer
# ============================================================
class FrameBuffer:
	def __init__(self):
		self.front = {}
		self.back = {}
	
	@property
	def layers(self) -> int:
		if not self.back: return 0
		return max(self.back.keys()) + 1
	
	def draw(self, x: int, y: int, text: str, layer: int = 0) -> None:
		if layer not in self.back: self.back[layer] = {}
		self.back[layer][(x, y)] = text
	
	
	def swap(self):
		for i in range(self.layers):
			if i not in self.back: continue
			for pos, text in self.back[i].items():
				if self.front.get(pos) != text:
					x, y = pos
					sys.stdout.write(f"\033[{y};{x}H{text}")
		
		sys.stdout.flush()
		self.front = self.back
		self.back = {}
	
	
	def clear(self):
		self.front = {}
		self.back = {}
		sys.stdout.write("\033[2J")
		sys.stdout.flush()


FB = FrameBuffer()



# ============================================================
# UI objects
# ============================================================
class Render_Object(object):
	def __init__(self, x: int, y: int, w: int, h: int) -> None:
		self.x = x; self.y = y
		self.w = w; self.h = h

	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 0) -> bool: return False	# returns True if changes occurred
	def get_grid_pos(self, grid_dimensions: list) -> tuple[int, int, int, int]:
		x, w = grid_dimensions[0][self.x]
		for i in range(1, self.w):
			w += grid_dimensions[0][self.x + i][1]
		y, h = grid_dimensions[1][self.y]
		for i in range(1, self.h):
			h += grid_dimensions[1][self.y + i][1]
		return x, y, w, h



class Box(Render_Object):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str = "",
			color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
			augments: list = None
	) -> None:
		super(Box, self).__init__(x, y, w, h)
		self.title = title
		self.color = rgb_fg(*color)
		self.augments = augments
		self.current_dimensions = None
	
	def draw_border(self, layer: int = 0) -> None:
		x, y, w, h = self.current_dimensions
		if w < 4 or h < 3: return
		
		FB.draw(x, y, 					f"{self.color}╭─┐{self.title[: w - 4]}┌{'─' * (w - 5 - len(self.title[: w - 4]))}╮{COL_RESET}", layer)
		FB.draw(x, y + h - 1, 			f"{self.color}╰{'─' * (w - 2)}╯{COL_RESET}", layer)
		
		# Side borders
		for i in range(1, h - 1):
			FB.draw(x, y + i, 			f"{self.color}│{COL_RESET}", layer)
			FB.draw(x + w - 1, y + i,	f"{self.color}│{COL_RESET}", layer)
		
		# augmentations
		if not self.augments: return
		for dx, dy, ch in self.augments:
			FB.draw(x + dx, y + dy,		f"{self.color}{ch}{COL_RESET}", layer)
			
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 0) -> bool:
		x, y, w, h = self.get_grid_pos(grid_dimensions)
		update = self.current_dimensions != (x, y, w, h) or force_update
		if update:
			self.current_dimensions = (x, y, w, h)
			self.draw_border(layer)
			print(flush=True)
		return update
		



class TBox(Box):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str,
			color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
			augments: list = None, line_limit: int = 500
	) -> None:
		super(TBox, self).__init__(x, y, w, h, title, color, augments)
		
		self.update_text = False
		self.line_limit = line_limit
		self.text = []
		
	def __getitem__(self, index: int) -> str:
		try: return self.text[index]
		except IndexError: return ""
	
	def pop(self) -> str:
		text = self.text.pop(0)
		self.update_text = True
		return text
		
	def add(self, text: str) -> None:
		self.text.insert(0, text)
		self.text = self.text[:self.line_limit]
		self.update_text = True
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 0) -> bool:
		if super(TBox, self).render(grid_dimensions, force_update, layer):
			self.update_text = True  # if statement to prevent short-circuiting errors
		x, y, w, h = self.current_dimensions
		if self.update_text:
			self.update_text = False
			lines = len(self.text)
			for i, l in enumerate(range(y + 1, h)):
				if i < lines:
					t = format_tabs(self.text[i])
					tlen = visible_len(t)
					t = ansi_safe_truncate(t, w-3)
					FB.draw(x+1, l, f"{t}{(' ' * (max((w-3)-tlen, 0)))}", layer)
				else: FB.draw(x+1, l, " " * (w-3), layer)
		return self.update_text
	


class Prompt(Box):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str,
			message: str, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
			augments: list = None
	) -> None:
		super(Prompt, self).__init__(x, y, w, h, title, color, augments)
		self.message = message
	
	
	def handle_key(self, key: str):
		pass
	
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 1) -> None:
		if super(Prompt, self).render(grid_dimensions, force_update, layer):
			update = True  # if statement to prevent short-circuiting errors
		pass
		
		
		


class TUI(object):
	def __init__(self, grid: tuple[int, int], modules: dict = None) -> None:
		self.running = False
		
		self.children = {}	# contains objects created by modules
		self.objects = []	# all render objects (children + prompts etc..)
		self.active_prompt = None # TODO: multi prompt??????
		
		self.keybindings = {}
		
		self.current_size = None
		self.grid_dimensions = None
		self.force_update = False
		
		self.grid = grid
		if modules: self.load_modules(modules)
		
		
	def load_modules(self, modules: dict):
		if "tbox" in modules:
			self.children.update({"tbox": {}})
			for tbox in modules["tbox"]:
				obj = TBox(**tbox)
				self.objects.append(obj)
				self.children["tbox"].update(
					{tbox["title"]: obj}
				)
		# TODO: other objects?
		# TODO: swappable objects??
	
	
	def handle_key(self, key: str) -> None:
		up = key.isupper(); key = key.lower()
		if self.active_prompt:
			self.active_prompt.handle_key(key)
			if key == "\n": self.unprompt(self.active_prompt)
		if key == "q": self.running = False
		if key in self.keybindings:
			self.keybindings[key]()
	
	def add_keybind(self, key: str, func: callable) -> None:
		self.keybindings.update({key: func})
	
	
	def get_child(self, obj_type: str, title: str):
		return self.children[obj_type][title]
	
	def force_refresh(self):
		print("\033[2J", end="", flush=True)
		self.force_update = True
	
	def prompt(self, x: int, y: int, w: int, h: int, title: str) -> Prompt:
		prompt = Prompt(x, y, w, h, title, "test")
		self.objects.append(prompt)
		self.active_prompt = prompt
		return prompt
	
	
	def unprompt(self, prompt: Prompt) -> None:
		if prompt != self.active_prompt: raise UserWarning("prompt was not active!")
		self.active_prompt = None
		self.objects.remove(prompt)
		self.force_refresh()
		
	
	def update_grid(self, size: list) -> None:
		self.grid_dimensions = [[], []]
		pos = [1, 1]
		for i in range(2):
			for j in range(self.grid[i]):
				w = size[i] // (self.grid[i] - j)
				self.grid_dimensions[i].append((pos[i], w))
				size[i] -= w; pos[i] += w
		
		
	def render(self):
		width, height = shutil.get_terminal_size()
		
		# update grid
		if self.current_size != (width, height):
			self.force_refresh()
			self.update_grid([width, height])
			self.current_size = (width, height)
		
		# TODO: prompt is overwritten in some situations_
		for obj in self.objects:
			obj.render(self.grid_dimensions, self.force_update)
			
		if self.force_update: self.force_update = False
		
	
	def run(self):
		self.running = True
		with Terminal() as term:
			while self.running:
				key = term.get_key()
				if key: self.handle_key(key)
				self.render()
				FB.swap()
				time.sleep(0.01)
				
