import logging
import sys

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')


class RAM:
    def __init__(self):
        self.memory = bytearray([0] * 65536)
        logging.info(f"Initialized Memory: {self.memory[:100]}")

    def load(self, data, offset, start=0, end=0xFFFF):
        for i in range(max(0, start), min(len(data), end)):
            self.memory[int(i + offset)] = data[i]
            # logging.info(f"address: {int(i + offset)} - {data[i]}")

        logging.info(f"Loaded Memory: {self.memory[start:start+1000]}")

    def read_byte(self, address):
        value = self.memory[address]
        logging.info(f"Read byte: {value}")
        value = int.to_bytes(value, 1, 'little')

        logging.info(f"Read byte return val: {value}")
        return value

    def set_byte(self, address, value):
        self.memory[address] = value
        logging.debug(f"Set byte: {address} \n\twith value: {value}")
