import dis
from understanding.opcodes import *


# Sample method
def add(a, b):
    return a + b

def results():
    print('=== understanding opcodes ===')
    print('Disassemabled code')
    print(dis.dis(add))

    print('\n')

    print('Byte code - this is not a 100% mirror of source due to python')
    print(add.__code__.co_code)

    print('\n')

    print('check bytes from hex AB CD')
    data = bytes.fromhex('AB CD')
    print(data)

    print('Use little/big endian')
    little = int.from_bytes(data, 'little')
    big = int.from_bytes(data, 'big')
    print((little, big))
    print('- As hex')
    print((hex(little), hex(big)))