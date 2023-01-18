import copy
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Literal, List


def load_items(obj: List):
    opcodes = []

    for key in obj:
        opcodes.append(Instruction(key, obj[key]))

    return opcodes


def load_opcodes(file):
    file = open(file)
    file = json.load(file)

    prefixed = load_items(file['cbprefixed'])
    unprefixed = load_items(file['unprefixed'])

    return (prefixed, unprefixed)


@dataclass
class Decoder:
    data: bytes
    address: int
    prefixed_instructions: dict
    instructions: dict

    @classmethod
    def create(cls, opcode_file: Path, data: bytes, address: int = 0):
        # Loads the opcodes from the opcode file
        prefixed, unprefixed = load_opcodes(opcode_file)
        return cls(
            prefixed_instructions=prefixed,
            instructions=unprefixed,
            data=data,
            address=address,
        )

    def read(self, address: int, count: int = 1):
        """
        Reads `count` bytes starting from `address`.
        """
        if 0 <= address + count <= len(self.data):
            v = self.data[address: address + count]
            return int.from_bytes(v, sys.byteorder)
        else:
            raise IndexError(f'{address=}+{count=} is out of range')

    def decode(self, address: int):
        """
        Decodes the instruction at `address`.
        """
        opcode = self.read(address)
        address += 1
        # 0xCB is a special prefix instruction. Read from
        # prefixed_instructions instead and increment address.
        if opcode == 0xCB:
            opcode = self.read(address)
            address += 1
            instruction = self.prefixed_instructions[opcode]
        else:
            instruction = self.instructions[opcode]
        new_operands = []
        for operand in instruction.operands:
            if operand.bytes is not None:
                value = self.read(address, operand.bytes)
                address += operand.bytes
                new_operands.append(operand.copy(value))
            else:
                # No bytes; that means it's not a memory address
                new_operands.append(operand)
        decoded_instruction = instruction.copy(operands=new_operands)
        return address, decoded_instruction


def disassemble(decoder: Decoder, address: int, count: int):
    for _ in range(count):
        try:
            new_address, instruction = decoder.decode(address)
            pp = instruction.print()
            print(f'{address:>04X} {pp}')
            address = new_address
        except IndexError as e:
            print('ERROR - {e!s}')
            break


class Instruction:
    def __init__(self, opcode_name, item, comment=None):
        operands = []

        for op in item['operands']:
            bytes = op.get('bytes', None)
            value = op.get('value', None)
            adjust = op.get('adjust', None)

            operands.append(Operand(
                immediate=op.get('immediate'),
                name=opcode_name,
                bytes=bytes,
                value=value,
                adjust=adjust
            ))

        self.opcode: int = opcode_name
        self.immediate: bool = item['immediate']
        self.operands: list[Operand] = operands
        self.cycles: list[int] = item['cycles']
        self.bytes: int = item['bytes']
        self.mnemonic: str = item['mnemonic']
        self.comment: str = comment

    def print(self):
        ops = ', '.join(op.print() for op in self.operands)
        s = f"{self.mnemonic:<8} {ops}"
        if self.comment:
            s = s + f" ; {self.comment:<10}"
        return s

    def copy(self, operands):
        new_item = copy.deepcopy(self)
        new_item.operands = operands
        return new_item


@dataclass
class Operand:
    immediate: bool
    name: str
    bytes: int
    value: int | None
    adjust: Literal["+", "-"] | None

    def print(self):
        if self.adjust is None:
            adjust = ""
        else:
            adjust = self.adjust
        if self.value is not None:
            if self.bytes is not None:
                val = hex(self.value)
            else:
                val = self.value
            v = val
        else:
            v = self.name
        v = v + adjust
        if self.immediate:
            return v
        return f'({v})'

    def copy(self, value):
        new_item = copy.deepcopy(self)
        new_item.value = value
        return new_item
