import shutil
import time


from .base import *
from .objects import *



class Box(Grid_Object):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str = "",
			color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF)
	) -> None:
		super(Box, self).__init__(x, y, w, h)
		self.title = title
		self.color = rgb_fg(*color)
		self.current_dimensions = None
		self.augments = []
	
	
	def add_augment(self, aug: Augment) -> None:
		self.augments.append(aug)
		
	
	def draw_border(self, layer: int = 0) -> None:
		x, y, w, h = self.current_dimensions
		if w < 4 or h < 3: return
		
		self.draw(x, y, layer, 					f"{self.color}╭─┐{self.title[: w - 4]}┌{'─' * (w - 5 - len(self.title[: w - 4]))}╮{COL_RESET}")
		self.draw(x, y + h - 1, layer, 			f"{self.color}╰{'─' * (w - 2)}╯{COL_RESET}")
		
		# Side borders
		for i in range(1, h - 1):
			self.draw(x, y + i, layer, 			f"{self.color}│{COL_RESET}")
			self.draw(x + w - 1, y + i, layer,	f"{self.color}│{COL_RESET}")
		
		for aug in self.augments:
			aug.render(x, y, layer + 1)
		
			
	
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
			line_limit: int = 500
	) -> None:
		super(TBox, self).__init__(x, y, w, h, title, color)
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
				self.draw(x+1, y+l, layer, ansi_safe_truncate_and_pad(self.text[i], " ", w-2))
			else: self.draw(x+1, y+l, layer, " " * (w-2))
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
			line_limit: int = 500, search_box_key: str = None
	) -> None:
		super(OBox, self).__init__(x, y, w, h, title, color)
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
		
		
	def search(self, search: str) -> None:
		if hasattr(self.object, "search"):
			self.object.search(search)
		print(f"OBOX_{self.title}.search({search})")
	
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
				self.draw(x+1, y+l, layer, ansi_safe_truncate_and_pad(f"{text[i]}", " ", w-2))
			else: self.draw(x+1, y+l, layer, " " * (w-2))
		return True
	


class Prompt(Box):
	def __init__(
			self, x: int, y: int, w: int, h: int, title: str,
			message: str, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF)
	) -> None:
		super(Prompt, self).__init__(x, y, w, h, title, color)
		self.message = message
		self.ended = False
		
	def eval(self) -> bool: return self.ended
	def end(self) -> None: self.ended = True
	def handle_key(self, key: str) -> None: pass
	
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 1) -> bool:
		if not super(Prompt, self).render(grid_dimensions, force_update, layer): return False
		x, y, w, h = self.current_dimensions
		self.draw(x+1, y+1, layer,		ansi_safe_truncate_and_pad(self.message, " ", w-2, "C"))
		self.draw(x, y+2, layer+1,		f"{self.color}├{'─' * (w-2)}┤{COL_RESET}")
		self.draw(x+1, y+h-2, layer+1,	f"{' ' * (w-22)}{self.color}press enter to exit{COL_RESET}")
		return True
	
	

class TPrompt(Prompt):
	def __init__(
		self, x: int, y: int, w: int, h: int, title: str,
		message: str, text: str, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF)
	 ) -> None:
		super(TPrompt, self).__init__(x, y, w, h, title, message, color)
		self.text = text.splitlines()
	
	
	def render(self, grid_dimensions: list, force_update: bool = False, layer: int = 1) -> bool:
		if not super(TPrompt, self).render(grid_dimensions, force_update, layer): return False
		x, y, w, h = self.current_dimensions
		lines = len(self.text)
		for i, l in enumerate(range(3, h-1)):
			if i < lines:
				self.draw(x+1, y+l, layer, ansi_safe_truncate_and_pad(self.text[i], " ", w-2))
			else: self.draw(x+1, y+l, layer, " " * (w-2))
		return True



class CPrompt(Prompt):
	def __init__(
		self, x: int, y: int, w: int, h: int, title: str,
		message: str, choices: list, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF)
	 ) -> None:
		super(CPrompt, self).__init__(x, y, w, h, title, message, color)
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
				self.draw(x+1, y+l, layer, ansi_safe_truncate_and_pad(f"-{'>' if i == self.selected else ' '}[{i}]: {self.choices[i]}", " ", w-2))
			else: self.draw(x+1, y+l, layer, " " * (w-2))
		return True

	
	
# TODO: create augments
class Text_Augment(Augment):
	def __init__(self, parent: Box, x: int, y: int, text: str, color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF)) -> None:
		super(Text_Augment, self).__init__(parent, x, y)
		self.text = text
		self.color = rgb_fg(*color)
		
	def render(self, x_offset: int, y_offset: int, layer: int = 0) -> bool:
		self.draw(x_offset + self.x, y_offset + self.y, layer, f"{self.color}{self.text}{COL_RESET}")
		return True


class Search_Augment(Augment):
	def __init__(
		self, parent: Box, x: int, y: int, title: str, key: str,
		color: tuple[int, int, int] = (0xFF, 0xFF, 0xFF)
	) -> None:
		super(Search_Augment, self).__init__(parent, x, y)
		self.title = title
		self.key = key
		self.color = rgb_fg(*color)
		if self.key in self.title:
			self.title_text = self.title.replace(
				self.key, f"{BOLD + UNDERLINE}{self.key}{BOLD_OFF + UNDERLINE_OFF}"
			)
		else: self.title_text = f"{BOLD}{self.key}{BOLD_OFF}: {self.title}"
		self.active = False
		self.search = ""
		
	def render(self, x_offset: int, y_offset: int, layer: int = 0) -> bool:
		if self.active:
			text = f"{self.color}┐{self.search}┌{COL_RESET}"
		else:
			text = f"{self.color}┐{self.title_text}┌{COL_RESET}"
		self.draw(x_offset + self.x, y_offset + self.y, layer, text)
		return True

	def submit(self):
		if hasattr(self.parent, "search"):
			self.parent.search(self.search)
		self.search = ""
		self.active = False
		

	def handle_key(self, key: str) -> "Search_Augment" or None:
		if self.active:
			if key == "enter": self.submit()
			elif len(key) == 1:
				self.search += key
		elif key == self.key:
			self.active = True
		return self if self.active else None




class Keybind_Handler(object):
	def __init__(self, tui: "TUI"):
		self.tui = tui
		self.keybindings = {}			# global keybinds
		self.search_boxes = []
		self.active_search_box = None
	
	def add(self, key: dict[str: callable]):
		self.keybindings.update(key)
	
	def handle_key(self, key: str or None) -> None:
		if not key: return
		key = key.lower()
		if self.tui.has_prompt and key == "enter":
			self.tui.unprompt(self.tui.active_prompt)
		if key == "q": self.tui.running = False
		if self.active_search_box:
			self.active_search_box = self.active_search_box.handle_key(key)
			self.tui.force_update = True
		elif key in self.keybindings:
			self.active_search_box = self.keybindings[key](key)
		if self.active_search_box: self.tui.force_update = True




class TUI(object):
	def __init__(self, grid: tuple[int, int], modules: dict = None) -> None:
		self.running = False
		
		self.objects = []		# all render objects (children + prompts etc..)
		self.prompts = []
		self.augments = []
		
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
			obj_t = {"tbox": TBox, "obox": OBox}[obj_type]
			for kwargs in objs:
				augments = kwargs.get("augments", None)
				if "augments" in kwargs: del kwargs["augments"]
				print(kwargs)
				obj = obj_t(**kwargs)
				if augments is not None:
					for aug_type, augs in augments.items():
						aug_t = {"text": Text_Augment, "search": Search_Augment}[aug_type]
						for aug_kwargs in augs:
							aug = aug_t(parent=obj, **aug_kwargs)
							obj.add_augment(aug)
							self.augments.append(aug)
							if aug_type == "search":
								self.add_keybind(aug.key, aug.handle_key)
				self.objects.append(obj)
		# TODO: swappable objects??

	
	def add_keybind(self, key: str, func: callable) -> None:
		self.key_handler.add({key: func})
	
	def get_child(self, title: str) -> any:
		for obj in self.objects:
			if obj.title == title:
				return obj
		return None
	
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
		# TODO: grid dimensions should be checked by obj itself?
		for obj in self.objects:
			obj.render(self.grid_dimensions, self.force_update)
			
		if self.force_update: self.force_update = False
		
	
	def run(self):
		self.running = True
		with Terminal() as term:
			while self.running:
				self.key_handler.handle_key(term.get_key())
				self.render()
				FB.swap()		# TODO: improve how this is referenced
				time.sleep(0.01)
		for log in self._log:
			print(log)
				
				
# TODO: log, render obj, augment obj (ref in parent obj and ref to parent obj, use hasattr to interact)

