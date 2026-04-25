from .base import *



__all__ = [
	"Render_Object",
	"Grid_Object",
	"Relative_Object",
	"Augment",
	"FB"
]


# ============================================================
# frame buffer object
# ============================================================
FB = Frame_Buffer()



# ============================================================
# UI objects
# ============================================================
class Render_Object(object):
	"""Renderable object"""
	def __init__(self) -> None:					pass
	def render(self, *args, **kwargs) -> bool:	return False
	
	@staticmethod
	def draw(x: int, y: int, l: int, txt: str) -> None:
		FB.draw(x, y, txt, l)
	


class Grid_Object(Render_Object):
	"""Renderable object that is aligned to a dynamic grid"""
	def __init__(self, x: int, y: int, w: int, h: int) -> None:
		super(Grid_Object, self).__init__()
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



class Relative_Object(Render_Object):
	"""Renderable object that has a relative position"""
	def __init__(self, x: int, y: int) -> None:
		super(Relative_Object, self).__init__()
		self.x = x; self.y = y
		
	def render(self, x_offset: int, y_offset: int, layer: int = 0) -> bool: return False
	


class Augment(Relative_Object):
	"""Renderable object that has a relative position from a grid object"""
	def __init__(self, parent: Grid_Object, x: int, y: int) -> None:
		super(Augment, self).__init__(x, y)
		self.parent = parent
		
	def render(self, x_offset: int, y_offset: int, layer: int = 0) -> bool: return False
	def handle_key(self, key: str) -> any: pass