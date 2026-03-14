import sys
import termios
import tty
import select
import shutil
import re




# ============================================================
# terminal and color functions
# ============================================================
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
FG_RESET = "\033[0m"

class Terminal:
	def __init__(self) -> None:
		self.fd =   sys.stdin.fileno()
		self.attr = termios.tcgetattr(self.fd)
	
	def __enter__(self) -> "Terminal":
		tty.setcbreak(self.fd)
		print("\033[?25l", end="")  # hide cursor
		print("\033[2J", end="")    # clear once
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
	
	return out + FG_RESET


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
	if ANSI_RE.search(result) and not result.endswith(FG_RESET):
		result += FG_RESET
		
	return result



# ============================================================
# frame buffer
# ============================================================
class FrameBuffer:
	def __init__(self):
		self.front = {}
		self.back = {}
	
	
	def draw(self, x, y, text):
		self.back[(x, y)] = text
	
	
	def swap(self):
		for pos, text in self.back.items():
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

	
	def get_grid_pos(self, grid_dimensions: list) -> tuple[int, int, int, int]:
		x, w = grid_dimensions[0][self.x]
		for i in range(1, self.w):
			w += grid_dimensions[0][self.x + i][1]
		y, h = grid_dimensions[1][self.y]
		for i in range(1, self.h):
			h += grid_dimensions[1][self.y + i][1]
		return x, y, w, h



class TBox(Render_Object):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str = "",
			color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF), line_limit: int = 500
	) -> None:
		super(TBox, self).__init__(x, y, w, h)
		self.title = title
		self.color = rgb_fg(*color)
		self.current_dimensions = None
		
		self.update_text = False
		self.line_limit = line_limit
		self.text = []
		
		
	def add_text(self, text: str) -> None:
		self.text.insert(0, text)
		self.text = self.text[:self.line_limit]
		self.update_text = True
	
	
	def update_border(self) -> None:
		x, y, w, h = self.current_dimensions
		if w < 4 or h < 3: return
		
		FB.draw(x, y, 			f"{self.color}╭─┐{self.title[: w - 4]}┌{'─' * (w - 5 - len(self.title[: w - 4]))}╮{FG_RESET}")
		FB.draw(x, y + h - 1, 	f"{self.color}╰{'─' * (w - 2)}╯{FG_RESET}")
		
		# Side borders
		for i in range(1, h - 1):
			FB.draw(x, y + i, 			f"{self.color}│{FG_RESET}")
			FB.draw(x + w - 1, y + i, 	f"{self.color}│{FG_RESET}")
	
	
	def render(self, grid_dimensions: list, force_update: bool = False) -> None:
		x, y, w, h = self.get_grid_pos(grid_dimensions)
		if self.current_dimensions != (x, y, w, h) or force_update:
			self.current_dimensions = (x, y, w, h)
			self.update_border()
			self.update_text = True
			print(flush=True)
		
		if self.update_text:
			self.update_text = False
			lines = len(self.text)
			for i, l in enumerate(range(y + 1, h)):
				if i < lines:
					t = self.text[i]
					FB.draw(x+1, l, f"{t[:w-3]}{(' ' * (len(t)-(w-3))) if len(t) < w-3 else ''}")
				else: FB.draw(x+1, l, "" * (w-3))
				


class TUI(object):
	def __init__(self, grid: tuple[int, int], modules: dict = None) -> None:
		self.running = False
		
		self.children = {}
		self.objects = []	# unordered version of children (render objects)
		
		self.keybindings = {}
		
		self.current_size = None
		self.grid_dimensions = None
		
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
		if key == "q": self.running = False
		if key in self.keybindings:
			self.keybindings[key]()
	
	def add_keybind(self, key: str, func: callable) -> None:
		self.keybindings.update({key: func})
	
	
	def get_child(self, obj_type: str, title: str):
		return self.children[obj_type][title]
		
	
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
		force_update = False
		if self.current_size != (width, height):
			print("\033[2J", end="", flush=True)
			self.update_grid([width, height])
			self.current_size = (width, height)
			force_update = True
			
		for obj in self.objects:
			obj.render(self.grid_dimensions, force_update)
		
	
	def run(self):
		self.running = True
		with Terminal() as term:
			while self.running:
				key = term.get_key()
				if key: self.handle_key(key)
				self.render()
				FB.swap()
				
	