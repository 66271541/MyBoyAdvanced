import logging
import struct
import sys
from array import array

from metadata.metadata_reader import CARTRIDGE_HEADER, CartridgeMetadata, read_cartridge_metadata

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')


class Cartridge:
    def __init__(self, game_rom):
        self.cart_mem = self.load_cartridge(game_rom)

        # Get cartridge info
        metadata = read_cartridge_metadata(game_rom.read_bytes())

        # logging.info('Read metadata v1')
        # carttype = self.cart_mem[0][0x0147]
        # logging.info(f"Cart type: {carttype}")

        logging.info('Read metadata v2')
        logging.info(f"ROM metadata: {metadata}")
        self.title = metadata.title
        self.cgb = metadata.cgb
        self.sgb = metadata.sgb
        self.type = metadata.cartridge_type
        self.rom = metadata.rom_size
        self.ram = metadata.ram_size
        self.header_checksum = metadata.header_checksum
        self.global_checksum = metadata.global_checksum

    def load_cartridge(self, filename):
        with open(filename, "rb") as file:
            # B read it in as Bytes
            data = array("B", file.read())

        logging.info(f"ROM Data: {data}")

        # Check if ROM is empty
        if len(data) == 0:
            logging.error("ROM file is empty!")
            exit(0)

        # TODO - what is the bank size
        # Why do we need this?
        banksize = 16 * 1024
        if len(data) % banksize != 0:
            logging.error("Unexpected ROM file length")
            raise Exception("Bad ROM file size")

        v = memoryview(data)
        mem_view = [v[i:i + banksize] for i in range(0, len(data), banksize)]
        logging.info(f"Memory View: {mem_view}")
        return mem_view, data
