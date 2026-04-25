import time

from TUI_lib import *

from time import sleep
from threading import Thread

from random import randint

from TUI_lib import *


def rand_color():
	return randint(0, 0xFF), randint(0, 0xFF), randint(0, 0xFF)


class Regs(object):
	def __init__(self) -> None:
		self.regs = {
			"R0": 0x40000000,
			"R1": 0x40000200,
			"PC": 0x80000400
		}
	
	def __hash__(self) -> int: return hash(tuple(hash((r, d)) for r, d in self.regs.items()))
	def __str__(self) -> str:
		out = []
		for reg, dat in self.regs.items():
			out.append(f"{reg}: {rgb_fg(0x30, 0x60, 0xA0)}{hex(dat)}")
		return "\n".join(out)


halted = False
def UI_test():
	global halted
	color = (0xD9, 0xA3, 0x4C)
	config = {
		"grid": [6, 4],
		"modules": {
			"tbox": [
				{"x": 0, "y": 0, "w": 2, "h": 4, "title": "code",		"color": color, "augments": {
					"text": [{"x": 0, "y": 1, "text": "❯", "color": color}]
				}},
				{"x": 2, "y": 0, "w": 1, "h": 2, "title": "call_stack",	"color": color, "augments": {
					"text": [{"x": 0, "y": 1, "text": "❯", "color": color}]
				}},
				{"x": 2, "y": 2, "w": 4, "h": 2, "title": "hardware",	"color": color},
			],
			"obox": [
				{"x": 3, "y": 0, "w": 1, "h": 2, "title": "registers",	"color": color},
				{"x": 4, "y": 0, "w": 2, "h": 2, "title": "memory",		"color": color, "augments": {
					"text": [{"x": 0, "y": 1, "text": "❯", "color": color}],
					"search": [{"x": 12, "y": 0, "title": "address", "key": "a", "color": color}]
				}}
			]
		}
	}
	
	tui = TUI(**config)
	code = tui.get_child("code")
	stack = tui.get_child("call_stack")
	regs = tui.get_child("registers")
	
	registers = Regs()
	regs.set_obj(registers)
	

	def test_keybind():
		global halted
		halted = not halted
		
	def prompt_keybind():
		prompt = TPrompt(1, 1, 1, 2, "Error", "A memory error occurred at instruction [1245]", "Tried to read from 0x0004021\nins: udhdhfhgy\n regs: .....", (0xFF, 0, 0))
		tui.prompt(prompt)
		
	def choice():
		prompt = CPrompt(1, 1, 1, 2, "Error", "Continue", ["Yes", "No"], (0xA0, 0xA0, 0))
		tui.prompt(prompt)
		while not (out := prompt.eval()):
			time.sleep(0.01)
		return out
		
	tui.add_keybind(" ", test_keybind)
	tui.add_keybind("p", prompt_keybind)
	
	t = Thread(target=tui.run)
	t.start()
	
	i = 0
	while t.is_alive():
		code.add(
			f"{rgb_fg(30, 120, 80)}[{i:04}] 0x0800{i:04x}  LDR R0, [R1] hshshshshshshshhshshshshshshfgisgsurifguisfguiss{COL_RESET}"
		)
		sleep(0.05)
		
		if not (i % 100):
			registers.regs["R2"] = randint(0, 0xFFFFFFFF)
			#stack.add(f"{rgb_fg(0xFF, 0, 0)}{choice()}{COL_RESET}")
		
		while halted:
			sleep(0.05)
			
		i += 1





if __name__ == "__main__":
	#text = "he\tllo world"
	#print(text, len(text), visible_len(text))
	#txt = f"{rgb_fg(15, 30, 45)}{rgb_fg(60, 75, 90)}{text}{COL_RESET}"
	#print(txt, len(txt), visible_len(txt))
	
	
	
	UI_test()
