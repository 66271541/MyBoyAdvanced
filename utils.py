import logging
import sys

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')


def hex_to_int(x):
    byte = int(x, 16)
    logging.info(f"hex to int: {byte}")
    return byte



def shift_left(val):
    return val << 8

def shift_right(val):
    return val >> 8

