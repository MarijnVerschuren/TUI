import shutil
import time


from .base import *



# ============================================================
# frame buffer object
# ============================================================
FB = Frame_Buffer()



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


class Augment(object):
	def __init__(self, parent: object, rel_x: int, rel_y: int) -> None:
		self.parent = parent
		self.x = rel_x; self.y = rel_y
		
	def render(self) -> bool: return False



class Box(Render_Object):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str = "",
			color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
			augments: list = None
	) -> None:
		super(Box, self).__init__(x, y, w, h)
		self.title = title
		self.color = rgb_fg(*color)
		self.current_dimensions = None
		self.augments = augments or []
		
	
	def draw_border(self, layer: int = 0) -> None:
		x, y, w, h = self.current_dimensions
		if w < 4 or h < 3: return
		
		FB.draw(x, y, 					f"{self.color}╭─┐{self.title[: w - 4]}┌{'─' * (w - 5 - len(self.title[: w - 4]))}╮{COL_RESET}", layer)
		FB.draw(x, y + h - 1, 			f"{self.color}╰{'─' * (w - 2)}╯{COL_RESET}", layer)
		
		# Side borders
		for i in range(1, h - 1):
			FB.draw(x, y + i, 			f"{self.color}│{COL_RESET}", layer)
			FB.draw(x + w - 1, y + i,	f"{self.color}│{COL_RESET}", layer)
		
		for x, y, aug in self.augments:
			FB.draw(x, y, f"{self.color}{aug}{COL_RESET}", layer + 1)
		
			
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 0) -> bool:
		x, y, w, h = self.get_grid_pos(grid_dimensions)
		update = self.current_dimensions != (x, y, w, h) or force_update
		if update:
			self.current_dimensions = (x, y, w, h)
			self.draw_border(layer)
			print(flush=True)
		return update
		



class TBox(Box):
	""" Text Box
	TUI box that displays text
	TODO: add append order
	"""
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str,
			color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
			augments: list = None, line_limit: int = 500
	) -> None:
		super(TBox, self).__init__(x, y, w, h, title, color, augments)
		self.update = False
		self.line_limit = line_limit
		self.text = []
		
	def __getitem__(self, index: int) -> str:
		try: return self.text[index]
		except IndexError: return ""
	
	def pop(self) -> str:
		text = self.text.pop(0)
		self.update = True
		return text
		
	def add(self, text: str) -> None:
		self.text.insert(0, text)
		self.text = self.text[:self.line_limit]
		self.update = True
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 0) -> bool:
		if super(TBox, self).render(grid_dimensions, force_update, layer):
			self.update = True  # if statement to prevent short-circuiting errors
		if not self.update: return False
		x, y, w, h = self.current_dimensions
		self.update = False
		lines = len(self.text)
		for i, l in enumerate(range(1, h-1)):
			if i < lines:
				FB.draw(x+1, y+l, ansi_safe_truncate_and_pad(self.text[i], " ", w-2), layer)
			else: FB.draw(x+1, y+l, " " * (w-2), layer)
		return True


class OBox(Box):
	""" Object Box
	TUI box that displays an object.
	object requirements:
		- __str__ method
		- __hash__ method (hashing printed data)
	"""
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str,
			obj: any = None, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
			augments: list = None, line_limit: int = 500, search_box_key: str = None
	) -> None:
		super(OBox, self).__init__(x, y, w, h, title, color, augments)
		self.update = False
		self.line_limit = line_limit
		self.object = self.hash = None
		self.search_box_key = search_box_key	# key used to activate search box
		self.search_box_active = False
		self.search_box_query = ""
		if obj is not None: self.set_obj(obj)
	
	
	def set_obj(self, obj: any) -> None:
		if not hasattr(obj, "__str__"): raise TypeError(f"{type(obj)} has no __str__ method")
		if not hasattr(obj, "__hash__"): raise TypeError(f"{type(obj)} has no __hash__ method")
		self.object = obj
		self.hash = hash(obj)
		
	
	def handle_key(self, key: str) -> None:
		pass
	

	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 0) -> bool:
		if super(OBox, self).render(grid_dimensions, force_update, layer):
			self.update = True  # if statement to prevent short-circuiting errors
		if hash(self.object) != self.hash: self.update = True
		if not self.update: return False
		x, y, w, h = self.current_dimensions
		self.hash = hash(self.object)
		self.update = False
		text =	str(self.object).split("\n")
		lines =	len(text)
		for i, l in enumerate(range(1, h-1)):
			if i < lines:
				FB.draw(x+1, y+l, ansi_safe_truncate_and_pad(f"{text[i]}", " ", w-2), layer)
			else: FB.draw(x+1, y+l, " " * (w-2), layer)
		return True
	


class Prompt(Box):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str,
			message: str, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
			augments: list = None
	) -> None:
		super(Prompt, self).__init__(x, y, w, h, title, color, augments)
		self.message = message
		self.ended = False
		
	def eval(self) -> bool: return self.ended
	def end(self) -> None: self.ended = True
	def handle_key(self, key: str) -> None: pass
	
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 1) -> bool:
		if not super(Prompt, self).render(grid_dimensions, force_update, layer): return False
		x, y, w, h = self.current_dimensions
		FB.draw(x+1, y+1, ansi_safe_truncate_and_pad(self.message, " ", w-2, "C"), layer)
		FB.draw(x, y+2, f"{self.color}├{'─' * (w-2)}┤{COL_RESET}", layer+1)
		FB.draw(x+1, y+h-2, f"{' ' * (w-22)}{self.color}press enter to exit{COL_RESET}", layer+1)
		return True
	
	

class TPrompt(Prompt):
	def __init__(
		self, x: int, y: int, w: int, h: int, title: str,
		message: str, text: str, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
		augments: list = None
	 ) -> None:
		super(TPrompt, self).__init__(x, y, w, h, title, message, color, augments)
		self.text = text.splitlines()
	
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 1) -> bool:
		if not super(TPrompt, self).render(grid_dimensions, force_update, layer): return False
		x, y, w, h = self.current_dimensions
		lines = len(self.text)
		for i, l in enumerate(range(3, h-1)):
			if i < lines:
				FB.draw(x+1, y+l, ansi_safe_truncate_and_pad(self.text[i], " ", w-2), layer)
			else: FB.draw(x+1, y+l, " " * (w-2), layer)
		return True



class CPrompt(Prompt):
	def __init__(
		self, x: int, y: int, w: int, h: int, title: str,
		message: str, choices: list, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
		augments: list = None
	 ) -> None:
		super(CPrompt, self).__init__(x, y, w, h, title, message, color, augments)
		self.choices = choices
		self.choice_count = len(choices)
		self.update = False
		self.selected = 0
	
	
	def eval(self) -> None or any: return self.choices[self.selected] if self.ended else None
	
	def handle_key(self, key: str) -> None:
		if key == "up":		self.selected = max(0, self.selected - 1);						self.update = True
		if key == "down":	self.selected = min(self.selected + 1, self.choice_count - 1);	self.update = True
		
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 1) -> bool:
		if super(CPrompt, self).render(grid_dimensions, force_update, layer):
			self.update = True
		if not self.update: return False
		self.update = False
		x, y, w, h = self.current_dimensions
		for i, l in enumerate(range(3, h-2)):
			if i < self.choice_count:
				FB.draw(x+1, y+l, ansi_safe_truncate_and_pad(f"-{'>' if i == self.selected else ' '}[{i}]: {self.choices[i]}", " ", w-2), layer)
			else: FB.draw(x+1, y+l, " " * (w-2), layer)
		return True

	

class SearchBox(Augment):
	def __init__(self, parent: object, x: int, y: int) -> None:
		super(SearchBox, self).__init__(parent, x, y)
		self.active = False
		
	#def render(self) -> bool: return False


class Keybind_Handler(object):
	def __init__(self, tui: "TUI"):
		self.tui = tui
		self.keybindings = {}			# global keybinds
		self.search_boxes = []
		self.active_search_box = None	# TODO
	
	def add(self, key: dict[str: callable]):
		self.keybindings.update(key)
	
	def handle_key(self, key: str) -> None:
		key = key.lower()
		if self.tui.has_prompt and key == "enter":
			self.tui.unprompt(self.tui.active_prompt)
		if key == "q": self.tui.running = False
		if key in self.keybindings:
			self.keybindings[key]()




class TUI(object):
	def __init__(self, grid: tuple[int, int], modules: dict = None) -> None:
		self.running = False
		
		self.children = {}		# contains objects created by modules
		self.objects = []		# all render objects (children + prompts etc..)
		self.prompts = []
		# TODO: add searchbox module that can be attached to objects (overtop?)
		# TODO: keybinds should be managed from this class (link with title) sep class!
		# TODO: improve key handling system?
		self._log = []
		
		self.key_handler = Keybind_Handler(self)
		
		self.current_size = None
		self.grid_dimensions = None
		self.force_update = False
		
		self.grid = grid
		if modules: self.load_modules(modules)
	
	def log(self, message: str) -> None: self._log.append(message)
	
	def load_modules(self, modules: dict) -> None:
		for obj_type, objs in modules.items():
			self.children.update({obj_type: {}})
			if obj_type == "search":
				for kwargs in objs:
					parent = self.get_obj(kwargs["parent"])
					# TODO
				continue
			obj_t = {"tbox": TBox, "obox": OBox}[obj_type]
			for kwargs in objs:
				obj = obj_t(**kwargs)
				self.objects.append(obj)
				self.children[obj_type].update({kwargs["title"]: obj})
		# TODO: swappable objects??

	
	def add_keybind(self, key: str, func: callable) -> None:
		self.key_handler.add({key: func})
	
	
	def get_obj(self, title: str) -> any:
		for obj in self.objects:
			if obj.title != title:
				return obj
		return None
	
	# TODO: is the child set needed????
	def get_child(self, obj_type: str, title: str) -> any:
		return self.children[obj_type][title]
	
	def force_refresh(self):
		print("\033[2J", end="", flush=True)
		self.force_update = True
	
	@property
	def active_prompt(self) -> Prompt: return self.prompts[-1]
	@property
	def has_prompt(self) -> bool: return len(self.prompts) > 0
	
	def prompt(self, prompt: Prompt) -> None:
		self.objects.append(prompt)
		self.prompts.append(prompt)
	
	
	def unprompt(self, prompt: Prompt) -> None:
		if prompt not in self.prompts: raise UserWarning("prompt was not active!")
		self.prompts.remove(prompt)
		self.objects.remove(prompt)
		prompt.end()
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
				if key: self.key_handler.handle_key(key)
				self.render()
				FB.swap()
				time.sleep(0.01)
		for log in self._log:
			print(log)
				
				
# TODO: log, render obj, augment obj (ref in parent obj and ref to parent obj, use hasattr to interact)

