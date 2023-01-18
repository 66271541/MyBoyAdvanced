from pathlib import Path
from pprint import pprint

import understanding.opcodes as u_opcodes
from opcodes.opcode_reader import load_opcodes, Decoder
from phase1.reading_boot_rom import phase_1_boot_rom
from phase1.reading_game_rom import phase_1_game_rom
from phase2.cpu import CPU
from phase2.motherboard import Motherboard
from phase3.display import Interface
from phase4.inputs import *

u_opcodes.results()

print('\n==== PHASE 1: Reading Boot-ROM ====')
boot_data = phase_1_boot_rom()

print('\n==== PHASE 1: Reading Game-ROM ====')
game_data = phase_1_game_rom()

print('\n==== PHASE 2: Create Base components ====')
mb = Motherboard(boot_data, game_data)
cpu = CPU(mb)

print('\n==== PHASE 4: Inputs ====')
print(f"A: {A()}")
print(f"B: {B()}")
print(f"Start: {start()}")
print(f"Select: {select()}")
print(f"Left: {left()}")
print(f"Right: {right()}")
print(f"Up: {up()}")
print(f"Down: {down()}")

start_input_listener()

print('\n==== PHASE 3: Displaying to video ====')
gpu = Interface(cpu, mb)








# print(" === LETS TRY STUFF ===")
# emulator.MyBoyAdvanced(game, None)

