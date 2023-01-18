import logging
import sys

from phase2.ram import RAM
# from phase3.gpu import GPU

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')


class Motherboard:
    def __init__(self, boot_data, game_rom=None, testing: bool = True):
        self.ram = RAM()
        self.ram.load(boot_data, 0)
        self.ram.load(game_rom, 0x0000, start=0x0100, end=0x4000)

        if testing:
            self.run_test_items()

    def get_byte(self, address):
        return self.ram.read_byte(address)

    def set_byte(self, address, value):
        return self.ram.set_byte(address, value)

    def run_test_items(self):
        print(self.ram.read_byte(0))
        print(self.ram.read_byte(5))
        print(self.ram.read_byte(10))
        print(self.ram.read_byte(20))
        print(self.ram.read_byte(40))
