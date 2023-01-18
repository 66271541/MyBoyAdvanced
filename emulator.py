from phase2.motherboard import Motherboard


class MyBoyAdvanced:
    def __init__(self, game_rom, boot_rom):
        self.game_rom = game_rom
        self.boot_rom = game_rom
        self._motherboard = self.motherboard()

    def cartridge(self):
        pass

    def motherboard(self):
        return Motherboard(self.game_rom)

    def cpu(self):
        pass

    def display(self):
        pass
