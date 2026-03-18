from TUI_lib import *

from time import sleep
from threading import Thread


halted = False
def UI_test():
	color = (0xD9, 0xA3, 0x4C)
	config = {
		"grid": [3, 4],
		"modules": {
			"tbox": [
				{"x": 0, "y": 0, "w": 1, "h": 4, "title": "code",		"color": color},
				{"x": 1, "y": 0, "w": 1, "h": 2, "title": "call_stack",	"color": color},
				{"x": 2, "y": 0, "w": 1, "h": 2, "title": "registers",	"color": color},
				{"x": 1, "y": 2, "w": 2, "h": 2, "title": "hardware",	"color": color},
			]
		}
	}
	
	tui = TUI(**config)
	code = tui.get_child("tbox", "code")

	def test_keybind():
		global halted
		halted = not halted
		
	def prompt_keybind():
		tui.prompt(1,1,1,2, "test")
	
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
		
		while halted:
			sleep(0.05)
			
		i += 1





if __name__ == "__main__":
	#text = "he\tllo world"
	#print(text, len(text), visible_len(text))
	#txt = f"{rgb_fg(15, 30, 45)}{rgb_fg(60, 75, 90)}{text}{COL_RESET}"
	#print(txt, len(txt), visible_len(txt))
	
	
	
	UI_test()
