from pathlib import Path

from phase2.ram import RAM
from utils import hex_to_int


def phase_1_boot_rom():
    print('Option 1')
    with open("bios.rom", mode="rb") as f:
        boot_data = f.read()

    print(f"Raw reading: {boot_data}")
    print(f"Raw reading: {boot_data[0]}")

    print('Option 2')
    boot_data = Path('bios.rom')
    print(f"Read bytes method: {boot_data.read_bytes()}")

    return boot_data.read_bytes()
