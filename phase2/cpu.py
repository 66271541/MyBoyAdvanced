import json
import logging
import sys
import inspect
from typing import Dict

from phase2.motherboard import Motherboard
from utils import shift_left, shift_right

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')

MIN_BYTE = 0x0000  # 0
MAX_BYTE = 0x00FF  # 255


class CPU:
    def __init__(self, motherboard: Motherboard, tick_rate=4194304):
        self.A = 0
        self.F = 0
        self.B = 0
        self.C = 0
        self.D = 0
        self.E = 0
        self.H = 0
        self.L = 0
        self.SP = 0
        self.PC = 0

        self.reg_fns = {
            'A': self.reg_a,
            'F': self.reg_f,
            'B': self.reg_b,
            'C': self.reg_c,
            'D': self.reg_d,
            'E': self.reg_e,
            'H': self.reg_h,
            'L': self.reg_l,
            'AF': self.reg_af,
            'BC': self.reg_bc,
            'DE': self.reg_de,
            'HL': self.reg_hl
        }

        self.motherboard = motherboard
        self.tick_rate = tick_rate

        self.opcodes = self.load_opcodes()
        self.register_values()

    def register_values(self):
        return [self.reg_af, self.reg_bc, self.reg_de, self.reg_hl, self.PC, self.SP]

    def print_register_values(self):
        print(f"A: {self.A}")
        print(f"F: {self.F}")
        print(f"BC: {self.reg_bc}")
        print(f"DE: {self.reg_de}")
        print(f"HL: {self.reg_hl}")
        print(f"PC: {self.PC}")
        print(f"SP: {self.SP}")

    def set_memory_address(self, address, value):
        self.motherboard.set_byte(address, value)

    def fetch_memory_address(self, address):
        return self.motherboard.get_byte(address)

    def execute(self) -> int:
        """

        :return: cycles
        """
        logging.info(f"Get PC instruction: {self.PC}")
        instruction = self.fetch_memory_address(self.PC)
        logging.info(f"decoded instruction: {instruction}")

        try:
            instruction = f"{instruction}".replace('\'', '').replace('b\\', '0')
            print(instruction)
            instruction = f"{instruction[:2]}{instruction[2].upper()}{instruction[3].upper()}"
            logging.info(f"current Instruction: {instruction}")

            #  This tell us which instruction table to get stuff from
            try:
                if instruction == '0xCB':
                    opcode = self.opcodes['prefixed'][instruction]
                else:
                    # opcode 0x00 is special in that it has no operands. Perhaps there is a better way to handle this
                    if instruction == '0x00':
                        self.PC += 1
                        self.PC &= 0xFFFF
                        return 4
                    opcode = self.opcodes['unprefixed'][instruction]
            except KeyError as e:
                print(f"Opcode not found: {instruction}")
                raise e

            logging.info(f"Opcode: {opcode}")
            return self.execute_opcode(instruction, opcode)
        except Exception as ex:
            logging.info(f"Weird byte: {instruction}")
            # raise ex
            self.PC += 1

    def execute_opcode(self, instruction, opcode) -> int:
        # Immediate: if true get from PC + 1, else from register

        logging.debug(f"Executing opcode mnemonic: {opcode['mnemonic']}")

        func_name = f"{opcode['mnemonic']}_{instruction[:-2]}"
        fn = self.__getattribute__(func_name)

        # # 1st byte is current byte
        # # every other byte is read
        _bytes = opcode['bytes']

        arg = 0
        if _bytes == 3:
            a = self.fetch_memory_address(self.PC + 2)
            b = self.fetch_memory_address(self.PC + 1)
            arg = (a << 8) + b
        elif _bytes == 2:
            arg = self.fetch_memory_address(self.PC + 1)

        if len(inspect.getfullargspec(func_name).args) > 0:
            cycles = fn()
        else:
            cycles = fn(arg)

        self.PC &= 0xFFFF

        # I didn't return this on all items
        return cycles or opcode['cycles'][0]

    def load_opcodes(self):
        with open('opcodes/Opcodes.json') as json_file:
            data = json.load(json_file)

        return data

    # === Register items ===
    @property
    def reg_a(self):
        return f"{self.A}"

    @reg_a.setter
    def reg_a(self, val):
        self.A = val

    @property
    def reg_b(self):
        return f"{self.B}"

    @reg_b.setter
    def reg_b(self, val):
        self.B = val

    @property
    def reg_c(self):
        return f"{self.C}"

    @reg_c.setter
    def reg_c(self, val):
        self.C = val

    @property
    def reg_d(self):
        return f"{self.D}"

    @reg_d.setter
    def reg_d(self, val):
        self.D = val

    @property
    def reg_e(self):
        return f"{self.E}"

    @reg_e.setter
    def reg_e(self, val):
        self.E = val

    @property
    def reg_f(self):
        return f"{self.F}"

    @reg_f.setter
    def reg_f(self, val):
        self.F = val

    @property
    def reg_h(self):
        return f"{self.H}"

    @reg_h.setter
    def reg_h(self, val):
        self.H = val

    @property
    def reg_l(self):
        return f"{self.L}"

    @reg_l.setter
    def reg_l(self, val):
        self.L = val

    @property
    def reg_af(self):
        return f"{self.A}{self.F}"

    @property
    def reg_bc(self):
        return f"{self.B}{self.C}"

    @reg_bc.setter
    def reg_bc(self, val):
        self.B = shift_right(val)
        self.C = val & MAX_BYTE

    @property
    def reg_de(self):
        return f"{self.D}{self.E}"

    @reg_de.setter
    def reg_de(self, val):
        self.B = shift_right(val)
        self.C = val & MAX_BYTE

    @property
    def reg_hl(self):
        return f"{self.H}{self.L}"

    # === Flags ===
    @property
    def z_flag(self):
        return (self.F & 0b10000000) >> 7

    @z_flag.setter
    def z_flag(self, value):
        if value == '-':
            return
        if value:
            self.F |= 1 << 7
        else:
            self.F &= 0b01111111

    @property
    def n_flag(self):
        return (self.F & 0b01000000) >> 6

    @n_flag.setter
    def n_flag(self, value):
        if value == '-':
            return
        if value:
            self.F |= 1 << 6
        else:
            self.F &= 0b10111111

    @property
    def h_flag(self):
        return (self.F & 0b00100000) >> 5

    @h_flag.setter
    def h_flag(self, value):
        if value == '-':
            return
        if value:
            self.F |= 1 << 5
        else:
            self.F &= 0b11011111

    @property
    def c_flag(self):
        return (self.F & 0b00010000) >> 4

    @c_flag.setter
    def c_flag(self, value):
        if value == '-':
            return
        if value:
            self.F |= 1 << 4
        else:
            self.F &= 0b11101111

    # ==== OPCODE FUNCTIONS ====
    def NOP_00(self):  # 00 NOP
        self.PC += 1
        return 4

    def LD_01(self, value):  # 01 LD BC,d16
        self.reg_bc(value)
        self.PC += 3

    def LD_02(self):  # 02 LD (BC),A
        self.set_memory_address(((self.B << 8) + self.C), self.A)
        self.PC += 1

    def INC_03(self):  # 03 INC BC
        temp = ((self.B << 8) + self.C) + 1
        # No flag operations
        temp &= 0xFFFF
        self.reg_bc(temp)
        self.PC += 1

    def INC_04(self):  # 04 INC B
        temp = self.B + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.B & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF

        self.B = temp
        self.PC += 1

    def DEC_05(self):  # 05 DEC B
        temp = self.B - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.B & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 1

    def LD_06(self, value):  # 06 LD B,d8
        self.B = value
        self.PC += 2

    def RLCA_07(self):  # 07 RLCA
        temp = (self.A << 1) + (self.A >> 7)
        flag = 0b00000000
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1

    def LD_08(self, value):  # 08 LD (a16),SP
        self.set_memory_address(value, self.SP & 0xFF)
        self.set_memory_address(value + 1, self.SP >> 8)
        self.PC += 3

    def ADD_09(self):  # 09 ADD HL,BC
        temp = self.HL + ((self.B << 8) + self.C)
        flag = 0b00000000
        flag += (((self.HL & 0xFFF) + (((self.B << 8) + self.C) & 0xFFF)) > 0xFFF) << self.h_flag
        flag += (temp > 0xFFFF) << self.c_flag
        self.F &= 0b10000000
        self.F |= flag
        temp &= 0xFFFF
        self.HL = temp
        self.PC += 1

    def LD_0A(self):  # 0A LD A,(BC)
        self.A = self.set_memory_address(((self.B << 8) + self.C))
        self.PC += 1

    def DEC_0B(self):  # 0B DEC BC
        temp = ((self.B << 8) + self.C) - 1
        # No flag operations
        temp &= 0xFFFF
        self.reg_bc(temp)
        self.PC += 1

    def INC_0C(self):  # 0C INC C
        temp = self.C + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.C & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 1

    def DEC_0D(self):  # 0D DEC C
        temp = self.C - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.C & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 1

    def LD_0E(self, value):  # 0E LD C,d8
        self.C = value
        self.PC += 2

    def RRCA_0F(self):  # 0F RRCA
        temp = (self.A >> 1) + ((self.A & 1) << 7) + ((self.A & 1) << 8)
        flag = 0b00000000
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1

    # def STOP_10(self, value):  # 10 STOP 0
    #     if self.mb.cgb:
    #         self.mb.switch_speed()
    #         self.set_memory_address(0xFF04, 0)
    #     self.PC += 2
    #     self.PC &= 0xFFFF
    #     return 4

    def LD_11(self, value):  # 11 LD DE,d16
        self.set_de(value)
        self.PC += 3

    def LD_12(self):  # 12 LD (DE),A
        self.set_memory_address(((self.D << 8) + self.E), self.A)
        self.PC += 1

    def INC_13(self):  # 13 INC DE
        temp = ((self.D << 8) + self.E) + 1
        # No flag operations
        temp &= 0xFFFF
        self.reg_de(temp)
        self.PC += 1

    def INC_14(self):  # 14 INC D
        temp = self.D + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.D & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 1

    def DEC_15(self):  # 15 DEC D
        temp = self.D - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.D & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 1

    def LD_16(self, value):  # 16 LD D,d8
        self.D = value
        self.PC += 2

    def RLA_17(self):  # 17 RLA
        temp = (self.A << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1

    def JR_18(self, value):  # 18 JR r8
        self.PC += 2 + ((value ^ 0x80) - 0x80)

    def ADD_19(self):  # 19 ADD HL,DE
        temp = self.HL + ((self.D << 8) + self.E)
        flag = 0b00000000
        flag += (((self.HL & 0xFFF) + (((self.D << 8) + self.E) & 0xFFF)) > 0xFFF) << self.h_flag
        flag += (temp > 0xFFFF) << self.c_flag
        self.F &= 0b10000000
        self.F |= flag
        temp &= 0xFFFF
        self.HL = temp
        self.PC += 1

    def LD_1A(self):  # 1A LD A,(DE)
        self.A = self.set_memory_address(((self.D << 8) + self.E))
        self.PC += 1

    def DEC_1B(self):  # 1B DEC DE
        temp = ((self.D << 8) + self.E) - 1
        # No flag operations
        temp &= 0xFFFF
        self.reg_de(temp)
        self.PC += 1

    def INC_1C(self):  # 1C INC E
        temp = self.E + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.E & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 1

    def DEC_1D(self):  # 1D DEC E
        temp = self.E - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.E & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 1

    def LD_1E(self, value):  # 1E LD E,d8
        self.E = value
        self.PC += 2

    def RRA_1F(self):  # 1F RRA
        temp = (self.A >> 1) + (self.c_flag != 0 << 7) + ((self.A & 1) << 8)
        flag = 0b00000000
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1

    def JR_20(self, value):  # 20 JR NZ,r8
        self.PC += 2
        if self.F & (1 << self.z_flag) == 0:
            self.PC += ((value ^ 0x80) - 0x80)
            self.PC &= 0xFFFF
            return 12
        else:
            self.PC &= 0xFFFF
            return 8

    def LD_21(self, value):  # 21 LD HL,d16
        self.HL = value
        self.PC += 3

    def LD_22(self):  # 22 LD (HL+),A
        self.set_memory_address(self.HL, self.A)
        self.HL += 1
        self.HL &= 0xFFFF
        self.PC += 1

    def INC_23(self):  # 23 INC HL
        temp = self.HL + 1
        # No flag operations
        temp &= 0xFFFF
        self.HL = temp
        self.PC += 1

    def INC_24(self):  # 24 INC H
        temp = (self.HL >> 8) + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += ((((self.HL >> 8) & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 1

    def DEC_25(self):  # 25 DEC H
        temp = (self.HL >> 8) - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += ((((self.HL >> 8) & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 1

    def LD_26(self, value):  # 26 LD H,d8
        self.HL = (self.HL & 0x00FF) | (value << 8)
        self.PC += 2

    def DAA_27(self):  # 27 DAA
        temp = self.A
        corr = 0
        corr |= 0x06 if self.h_flag != 0 else 0x00
        corr |= 0x60 if self.c_flag != 0else 0x00
        if self.n_flag != 0:
            temp -= corr
        else:
            corr |= 0x06 if (temp & 0x0F) > 0x09 else 0x00
            corr |= 0x60 if temp > 0x99 else 0x00
            temp += corr
        flag = 0
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (corr & 0x60 != 0) << self.c_flag
        self.F &= 0b01000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1

    def JR_28(self, value):  # 28 JR Z,r8
        self.PC += 2
        if self.z_flag != 0:
            self.PC += ((value ^ 0x80) - 0x80)
            return 12
        else:
            return 8

    def ADD_29(self):  # 29 ADD HL,HL
        temp = self.HL + self.HL
        flag = 0b00000000
        flag += (((self.HL & 0xFFF) + (self.HL & 0xFFF)) > 0xFFF) << self.h_flag
        flag += (temp > 0xFFFF) << self.c_flag
        self.F &= 0b10000000
        self.F |= flag
        temp &= 0xFFFF
        self.HL = temp
        self.PC += 1

    def LD_2A(self):  # 2A LD A,(HL+)
        self.A = self.set_memory_address(self.HL)
        self.HL += 1
        self.HL &= 0xFFFF
        self.PC += 1

    def DEC_2B(self):  # 2B DEC HL
        temp = self.HL - 1
        # No flag operations
        temp &= 0xFFFF
        self.HL = temp
        self.PC += 1

    def INC_2C(self):  # 2C INC L
        temp = (self.HL & 0xFF) + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += ((((self.HL & 0xFF) & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 1

    def DEC_2D(self):  # 2D DEC L
        temp = (self.HL & 0xFF) - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += ((((self.HL & 0xFF) & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 1

    def LD_2E(self, value):  # 2E LD L,d8
        self.HL = (self.HL & 0xFF00) | (value & 0xFF)
        self.PC += 2

    def CPL_2F(self):  # 2F CPL
        self.A = (~self.A) & 0xFF
        flag = 0b01100000
        self.F &= 0b10010000
        self.F |= flag
        self.PC += 1

    def JR_30(self, value):  # 30 JR NC,r8
        self.PC += 2
        if self.c_flag == 0:
            self.PC += ((value ^ 0x80) - 0x80)
            return 12
        else:
            return 8

    def LD_31(self, value):  # 31 LD SP,d16
        self.SP = value
        self.PC += 3

    def LD_32(self):  # 32 LD (HL-),A
        self.set_memory_address(self.HL, self.A)
        self.HL -= 1
        self.HL &= 0xFFFF
        self.PC += 1

    def INC_33(self):  # 33 INC SP
        temp = self.SP + 1
        # No flag operations
        temp &= 0xFFFF
        self.SP = temp
        self.PC += 1

    def INC_34(self):  # 34 INC (HL)
        temp = self.fetch_memory_address(self.HL) + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.fetch_memory_address(self.HL) & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 1
        return 12

    def DEC_35(self):  # 35 DEC (HL)
        temp = self.fetch_memory_address(self.HL) - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.fetch_memory_address(self.HL) & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 1
        return 12

    def LD_36(self, value):  # 36 LD (HL),d8
        self.set_memory_address(self.HL, value)
        self.PC += 2
        return 12

    def SCF_37(self):  # 37 SCF
        flag = 0b00010000
        self.F &= 0b10000000
        self.F |= flag
        self.PC += 1
        return 4

    def JR_38(self, value):  # 38 JR C,r8
        self.PC += 2
        if self.c_flag != 0:
            self.PC += ((value ^ 0x80) - 0x80)
            self.PC &= 0xFFFF
            return 12
        else:
            self.PC &= 0xFFFF
            return 8

    def ADD_39(self):  # 39 ADD HL,SP
        temp = self.HL + self.SP
        flag = 0b00000000
        flag += (((self.HL & 0xFFF) + (self.SP & 0xFFF)) > 0xFFF) << self.h_flag
        flag += (temp > 0xFFFF) << self.c_flag
        self.F &= 0b10000000
        self.F |= flag
        temp &= 0xFFFF
        self.HL = temp
        self.PC += 1
        return 8

    def LD_3A(self):  # 3A LD A,(HL-)
        self.A = self.fetch_memory_address(self.HL)
        self.HL -= 1
        self.HL &= 0xFFFF
        self.PC += 1
        return 8

    def DEC_3B(self):  # 3B DEC SP
        temp = self.SP - 1
        # No flag operations
        temp &= 0xFFFF
        self.SP = temp
        self.PC += 1
        return 8

    def INC_3C(self):  # 3C INC A
        temp = self.A + 1
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (1 & 0xF)) > 0xF) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def DEC_3D(self):  # 3D DEC A
        temp = self.A - 1
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (1 & 0xF)) < 0) << self.h_flag
        self.F &= 0b00010000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def LD_3E(self, value):  # 3E LD A,d8
        self.A = value
        self.PC += 2
        return 8

    def CCF_3F(self):  # 3F CCF
        flag = (self.F & 0b00010000) ^ 0b00010000
        self.F &= 0b10000000
        self.F |= flag
        self.PC += 1
        return 4

    def LD_40(self):  # 40 LD B,B
        self.B = self.B
        self.PC += 1
        return 4

    def LD_41(self):  # 41 LD B,C
        self.B = self.C
        self.PC += 1
        return 4

    def LD_42(self):  # 42 LD B,D
        self.B = self.D
        self.PC += 1
        return 4

    def LD_43(self):  # 43 LD B,E
        self.B = self.E
        self.PC += 1
        return 4

    def LD_44(self):  # 44 LD B,H
        self.B = (self.HL >> 8)
        self.PC += 1
        return 4

    def LD_45(self):  # 45 LD B,L
        self.B = (self.HL & 0xFF)
        self.PC += 1
        return 4

    def LD_46(self):  # 46 LD B,(HL)
        self.B = self.fetch_memory_address(self.HL)
        self.PC += 1
        return 8

    def LD_47(self):  # 47 LD B,A
        self.B = self.A
        self.PC += 1
        return 4

    def LD_48(self):  # 48 LD C,B
        self.C = self.B
        self.PC += 1
        return 4

    def LD_49(self):  # 49 LD C,C
        self.C = self.C
        self.PC += 1
        return 4

    def LD_4A(self):  # 4A LD C,D
        self.C = self.D
        self.PC += 1
        return 4

    def LD_4B(self):  # 4B LD C,E
        self.C = self.E
        self.PC += 1
        return 4

    def LD_4C(self):  # 4C LD C,H
        self.C = (self.HL >> 8)
        self.PC += 1
        return 4

    def LD_4D(self):  # 4D LD C,L
        self.C = (self.HL & 0xFF)
        self.PC += 1
        return 4

    def LD_4E(self):  # 4E LD C,(HL)
        self.C = self.fetch_memory_address(self.HL)
        self.PC += 1
        return 8

    def LD_4F(self):  # 4F LD C,A
        self.C = self.A
        self.PC += 1
        return 4

    def LD_50(self):  # 50 LD D,B
        self.D = self.B
        self.PC += 1
        return 4

    def LD_51(self):  # 51 LD D,C
        self.D = self.C
        self.PC += 1
        return 4

    def LD_52(self):  # 52 LD D,D
        self.D = self.D
        self.PC += 1
        return 4

    def LD_53(self):  # 53 LD D,E
        self.D = self.E
        self.PC += 1
        return 4

    def LD_54(self):  # 54 LD D,H
        self.D = (self.HL >> 8)
        self.PC += 1
        return 4

    def LD_55(self):  # 55 LD D,L
        self.D = (self.HL & 0xFF)
        self.PC += 1
        return 4

    def LD_56(self):  # 56 LD D,(HL)
        self.D = self.fetch_memory_address(self.HL)
        self.PC += 1
        return 8

    def LD_57(self):  # 57 LD D,A
        self.D = self.A
        self.PC += 1
        return 4

    def LD_58(self):  # 58 LD E,B
        self.E = self.B
        self.PC += 1
        return 4

    def LD_59(self):  # 59 LD E,C
        self.E = self.C
        self.PC += 1
        return 4

    def LD_5A(self):  # 5A LD E,D
        self.E = self.D
        self.PC += 1
        return 4

    def LD_5B(self):  # 5B LD E,E
        self.E = self.E
        self.PC += 1
        return 4

    def LD_5C(self):  # 5C LD E,H
        self.E = (self.HL >> 8)
        self.PC += 1
        return 4

    def LD_5D(self):  # 5D LD E,L
        self.E = (self.HL & 0xFF)
        self.PC += 1
        return 4

    def LD_5E(self):  # 5E LD E,(HL)
        self.E = self.fetch_memory_address(self.HL)
        self.PC += 1
        return 8

    def LD_5F(self):  # 5F LD E,A
        self.E = self.A
        self.PC += 1
        return 4

    def LD_60(self):  # 60 LD H,B
        self.HL = (self.HL & 0x00FF) | (self.B << 8)
        self.PC += 1
        return 4

    def LD_61(self):  # 61 LD H,C
        self.HL = (self.HL & 0x00FF) | (self.C << 8)
        self.PC += 1
        return 4

    def LD_62(self):  # 62 LD H,D
        self.HL = (self.HL & 0x00FF) | (self.D << 8)
        self.PC += 1
        return 4

    def LD_63(self):  # 63 LD H,E
        self.HL = (self.HL & 0x00FF) | (self.E << 8)
        self.PC += 1
        return 4

    def LD_64(self):  # 64 LD H,H
        self.HL = (self.HL & 0x00FF) | ((self.HL >> 8) << 8)
        self.PC += 1
        return 4

    def LD_65(self):  # 65 LD H,L
        self.HL = (self.HL & 0x00FF) | ((self.HL & 0xFF) << 8)
        self.PC += 1
        return 4

    def LD_66(self):  # 66 LD H,(HL)
        self.HL = (self.HL & 0x00FF) | (self.fetch_memory_address(self.HL) << 8)
        self.PC += 1
        return 8

    def LD_67(self):  # 67 LD H,A
        self.HL = (self.HL & 0x00FF) | (self.A << 8)
        self.PC += 1
        return 4

    def LD_68(self):  # 68 LD L,B
        self.HL = (self.HL & 0xFF00) | (self.B & 0xFF)
        self.PC += 1
        return 4

    def LD_69(self):  # 69 LD L,C
        self.HL = (self.HL & 0xFF00) | (self.C & 0xFF)
        self.PC += 1
        return 4

    def LD_6A(self):  # 6A LD L,D
        self.HL = (self.HL & 0xFF00) | (self.D & 0xFF)
        self.PC += 1
        return 4

    def LD_6B(self):  # 6B LD L,E
        self.HL = (self.HL & 0xFF00) | (self.E & 0xFF)
        self.PC += 1
        return 4

    def LD_6C(self):  # 6C LD L,H
        self.HL = (self.HL & 0xFF00) | ((self.HL >> 8) & 0xFF)
        self.PC += 1
        return 4

    def LD_6D(self):  # 6D LD L,L
        self.HL = (self.HL & 0xFF00) | ((self.HL & 0xFF) & 0xFF)
        self.PC += 1
        return 4

    def LD_6E(self):  # 6E LD L,(HL)
        self.HL = (self.HL & 0xFF00) | (self.fetch_memory_address(self.HL) & 0xFF)
        self.PC += 1
        return 8

    def LD_6F(self):  # 6F LD L,A
        self.HL = (self.HL & 0xFF00) | (self.A & 0xFF)
        self.PC += 1
        return 4

    def LD_70(self):  # 70 LD (HL),B
        self.set_memory_address(self.HL, self.B)
        self.PC += 1
        return 8

    def LD_71(self):  # 71 LD (HL),C
        self.set_memory_address(self.HL, self.C)
        self.PC += 1
        return 8

    def LD_72(self):  # 72 LD (HL),D
        self.set_memory_address(self.HL, self.D)
        self.PC += 1
        return 8

    def LD_73(self):  # 73 LD (HL),E
        self.set_memory_address(self.HL, self.E)
        self.PC += 1
        return 8

    def LD_74(self):  # 74 LD (HL),H
        self.set_memory_address(self.HL, (self.HL >> 8))
        self.PC += 1
        return 8

    def LD_75(self):  # 75 LD (HL),L
        self.set_memory_address(self.HL, (self.HL & 0xFF))
        self.PC += 1
        return 8

    def HALT_76(self):  # 76 HALT
        self.halted = True
        return 4

    def LD_77(self):  # 77 LD (HL),A
        self.set_memory_address(self.HL, self.A)
        self.PC += 1
        return 8

    def LD_78(self):  # 78 LD A,B
        self.A = self.B
        self.PC += 1
        return 4

    def LD_79(self):  # 79 LD A,C
        self.A = self.C
        self.PC += 1
        return 4

    def LD_7A(self):  # 7A LD A,D
        self.A = self.D
        self.PC += 1
        return 4

    def LD_7B(self):  # 7B LD A,E
        self.A = self.E
        self.PC += 1
        return 4

    def LD_7C(self):  # 7C LD A,H
        self.A = (self.HL >> 8)
        self.PC += 1
        return 4

    def LD_7D(self):  # 7D LD A,L
        self.A = (self.HL & 0xFF)
        self.PC += 1
        return 4

    def LD_7E(self):  # 7E LD A,(HL)
        self.A = self.fetch_memory_address(self.HL)
        self.PC += 1
        return 8

    def LD_7F(self):  # 7F LD A,A
        self.A = self.A
        self.PC += 1
        return 4

    def ADD_80(self):  # 80 ADD A,B
        temp = self.A + self.B
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.B & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADD_81(self):  # 81 ADD A,C
        temp = self.A + self.C
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.C & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADD_82(self):  # 82 ADD A,D
        temp = self.A + self.D
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.D & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADD_83(self):  # 83 ADD A,E
        temp = self.A + self.E
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.E & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADD_84(self):  # 84 ADD A,H
        temp = self.A + (self.HL >> 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + ((self.HL >> 8) & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADD_85(self):  # 85 ADD A,L
        temp = self.A + (self.HL & 0xFF)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + ((self.HL & 0xFF) & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADD_86(self):  # 86 ADD A,(HL)
        temp = self.A + self.fetch_memory_address(self.HL)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.fetch_memory_address(self.HL) & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 8

    def ADD_87(self):  # 87 ADD A,A
        temp = self.A + self.A
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.A & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADC_88(self):  # 88 ADC A,B
        temp = self.A + self.B + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.B & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADC_89(self):  # 89 ADC A,C
        temp = self.A + self.C + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.C & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADC_8A(self):  # 8A ADC A,D
        temp = self.A + self.D + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.D & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADC_8B(self):  # 8B ADC A,E
        temp = self.A + self.E + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.E & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADC_8C(self):  # 8C ADC A,H
        temp = self.A + (self.HL >> 8) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + ((self.HL >> 8) & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADC_8D(self):  # 8D ADC A,L
        temp = self.A + (self.HL & 0xFF) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + ((self.HL & 0xFF) & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def ADC_8E(self):  # 8E ADC A,(HL)
        temp = self.A + self.fetch_memory_address(self.HL) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.fetch_memory_address(self.HL) & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 8

    def ADC_8F(self):  # 8F ADC A,A
        temp = self.A + self.A + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (self.A & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SUB_90(self):  # 90 SUB B
        temp = self.A - self.B
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.B & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SUB_91(self):  # 91 SUB C
        temp = self.A - self.C
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.C & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SUB_92(self):  # 92 SUB D
        temp = self.A - self.D
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.D & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SUB_93(self):  # 93 SUB E
        temp = self.A - self.E
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.E & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SUB_94(self):  # 94 SUB H
        temp = self.A - (self.HL >> 8)
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - ((self.HL >> 8) & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SUB_95(self):  # 95 SUB L
        temp = self.A - (self.HL & 0xFF)
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - ((self.HL & 0xFF) & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SUB_96(self):  # 96 SUB (HL)
        temp = self.A - self.fetch_memory_address(self.HL)
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.fetch_memory_address(self.HL) & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 8

    def SUB_97(self):  # 97 SUB A
        temp = self.A - self.A
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.A & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SBC_98(self):  # 98 SBC A,B
        temp = self.A - self.B - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.B & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SBC_99(self):  # 99 SBC A,C
        temp = self.A - self.C - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.C & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SBC_9A(self):  # 9A SBC A,D
        temp = self.A - self.D - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.D & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SBC_9B(self):  # 9B SBC A,E
        temp = self.A - self.E - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.E & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SBC_9C(self):  # 9C SBC A,H
        temp = self.A - (self.HL >> 8) - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - ((self.HL >> 8) & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SBC_9D(self):  # 9D SBC A,L
        temp = self.A - (self.HL & 0xFF) - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - ((self.HL & 0xFF) & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def SBC_9E(self):  # 9E SBC A,(HL)
        temp = self.A - self.fetch_memory_address(self.HL) - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.fetch_memory_address(self.HL) & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 8

    def SBC_9F(self):  # 9F SBC A,A
        temp = self.A - self.A - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.A & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def AND_A0(self):  # A0 AND B
        temp = self.A & self.B
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def AND_A1(self):  # A1 AND C
        temp = self.A & self.C
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def AND_A2(self):  # A2 AND D
        temp = self.A & self.D
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def AND_A3(self):  # A3 AND E
        temp = self.A & self.E
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def AND_A4(self):  # A4 AND H
        temp = self.A & (self.HL >> 8)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def AND_A5(self):  # A5 AND L
        temp = self.A & (self.HL & 0xFF)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def AND_A6(self):  # A6 AND (HL)
        temp = self.A & self.fetch_memory_address(self.HL)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 8

    def AND_A7(self):  # A7 AND A
        temp = self.A & self.A
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def XOR_A8(self):  # A8 XOR B
        temp = self.A ^ self.B
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def XOR_A9(self):  # A9 XOR C
        temp = self.A ^ self.C
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def XOR_AA(self):  # AA XOR D
        temp = self.A ^ self.D
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def XOR_AB(self):  # AB XOR E
        temp = self.A ^ self.E
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def XOR_AC(self):  # AC XOR H
        temp = self.A ^ (self.HL >> 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def XOR_AD(self):  # AD XOR L
        temp = self.A ^ (self.HL & 0xFF)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def XOR_AE(self):  # AE XOR (HL)
        temp = self.A ^ self.fetch_memory_address(self.HL)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 8

    def XOR_AF(self):  # AF XOR A
        temp = self.A ^ self.A
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def OR_B0(self):  # B0 OR B
        temp = self.A | self.B
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def OR_B1(self):  # B1 OR C
        temp = self.A | self.C
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def OR_B2(self):  # B2 OR D
        temp = self.A | self.D
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def OR_B3(self):  # B3 OR E
        temp = self.A | self.E
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def OR_B4(self):  # B4 OR H
        temp = self.A | (self.HL >> 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def OR_B5(self):  # B5 OR L
        temp = self.A | (self.HL & 0xFF)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def OR_B6(self):  # B6 OR (HL)
        temp = self.A | self.fetch_memory_address(self.HL)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 8

    def OR_B7(self):  # B7 OR A
        temp = self.A | self.A
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 1
        return 4

    def CP_B8(self):  # B8 CP B
        temp = self.A - self.B
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.B & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 4

    def CP_B9(self):  # B9 CP C
        temp = self.A - self.C
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.C & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 4

    def CP_BA(self):  # BA CP D
        temp = self.A - self.D
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.D & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 4

    def CP_BB(self):  # BB CP E
        temp = self.A - self.E
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.E & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 4

    def CP_BC(self):  # BC CP H
        temp = self.A - (self.HL >> 8)
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - ((self.HL >> 8) & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 4

    def CP_BD(self):  # BD CP L
        temp = self.A - (self.HL & 0xFF)
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - ((self.HL & 0xFF) & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 4

    def CP_BE(self):  # BE CP (HL)
        temp = self.A - self.fetch_memory_address(self.HL)
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.fetch_memory_address(self.HL) & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 8

    def CP_BF(self):  # BF CP A
        temp = self.A - self.A
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (self.A & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 1
        return 4

    def RET_C0(self):  # C0 RET NZ
        if self.f_nz():
            self.PC = self.fetch_memory_address((self.SP + 1) & 0xFFFF) << 8  # High
            self.PC |= self.fetch_memory_address(self.SP)  # Low
            self.SP += 2
            self.SP &= 0xFFFF
            return 20
        else:
            self.PC += 1
            self.PC &= 0xFFFF
            return 8

    def POP_C1(self):  # C1 POP BC
        self.B = self.fetch_memory_address((self.SP + 1) & 0xFFFF)  # High
        self.C = self.fetch_memory_address(self.SP)  # Low
        self.SP += 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 12

    def JP_C2(self, value):  # C2 JP NZ,a16
        if self.f_nz():
            self.PC = value
            return 16
        else:
            self.PC += 3
            self.PC &= 0xFFFF
            return 12

    def JP_C3(self, value):  # C3 JP a16
        self.PC = value
        return 16

    def CALL_C4(self, value):  # C4 CALL NZ,a16
        self.PC += 3
        if self.f_nz():
            self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
            self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
            self.SP -= 2
            self.SP &= 0xFFFF
            self.PC = value
            return 24
        else:
            return 12

    def PUSH_C5(self):  # C5 PUSH BC
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.B)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.C)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 16

    def ADD_C6(self, value):  # C6 ADD A,d8
        temp = self.A + value
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (value & 0xF)) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RST_C7(self):  # C7 RST 00H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 0
        return 16

    def RET_C8(self):  # C8 RET Z
        if self.f_z():
            self.PC = self.fetch_memory_address((self.SP + 1) & 0xFFFF) << 8  # High
            self.PC |= self.fetch_memory_address(self.SP)  # Low
            self.SP += 2
            self.SP &= 0xFFFF
            return 20
        else:
            self.PC += 1
            self.PC &= 0xFFFF
            return 8

    def RET_C9(self):  # C9 RET
        self.PC = self.fetch_memory_address((self.SP + 1) & 0xFFFF) << 8  # High
        self.PC |= self.fetch_memory_address(self.SP)  # Low
        self.SP += 2
        self.SP &= 0xFFFF
        return 16

    def JP_CA(self, value):  # CA JP Z,a16
        if self.f_z():
            self.PC = value
            return 16
        else:
            self.PC += 3
            self.PC &= 0xFFFF
            return 12

    def PREFIX_CB(self):  # CB PREFIX CB
        logging.critical('CB cannot be called!')
        self.PC += 1
        return 4

    def CALL_CC(self, value):  # CC CALL Z,a16
        self.PC += 3
        if self.f_z():
            self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
            self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
            self.SP -= 2
            self.SP &= 0xFFFF
            self.PC = value
            return 24
        else:
            return 12

    def CALL_CD(self, value):  # CD CALL a16
        self.PC += 3
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = value
        return 24

    def ADC_CE(self, value):  # CE ADC A,d8
        temp = self.A + value + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) + (value & 0xF) + self.c_flag != 0) > 0xF) << self.h_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RST_CF(self):  # CF RST 08H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 8
        return 16

    def RET_D0(self):  # D0 RET NC
        if self.c_flag == 0:
            self.PC = self.fetch_memory_address((self.SP + 1) & 0xFFFF) << 8  # High
            self.PC |= self.fetch_memory_address(self.SP)  # Low
            self.SP += 2
            self.SP &= 0xFFFF
            return 20
        else:
            self.PC += 1
            self.PC &= 0xFFFF
            return 8

    def POP_D1(self):  # D1 POP DE
        self.D = self.set_memory_address((self.SP + 1) & 0xFFFF)  # High
        self.E = self.fetch_memory_address(self.SP)  # Low
        self.SP += 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 12

    def JP_D2(self, value):  # D2 JP NC,a16
        if self.c_flag == 0:
            self.PC = value
            return 16
        else:
            self.PC += 3
            self.PC &= 0xFFFF
            return 12

    def CALL_D4(self, value):  # D4 CALL NC,a16
        self.PC += 3
        if self.c_flag == 0:
            self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
            self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
            self.SP -= 2
            self.SP &= 0xFFFF
            self.PC = value
            return 24
        else:
            return 12

    def PUSH_D5(self):  # D5 PUSH DE
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.D)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.E)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 16

    def SUB_D6(self, value):  # D6 SUB d8
        temp = self.A - value
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (value & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RST_D7(self):  # D7 RST 10H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 16
        return 16

    def RET_D8(self):  # D8 RET C
        if self.c_flag != 0:
            self.PC = self.fetch_memory_address((self.SP + 1) & 0xFFFF) << 8  # High
            self.PC |= self.fetch_memory_address(self.SP)  # Low
            self.SP += 2
            self.SP &= 0xFFFF
            return 20
        else:
            self.PC += 1
            self.PC &= 0xFFFF
            return 8

    def RETI_D9(self):  # D9 RETI
        self.interrupt_master_enable = True
        self.PC = self.fetch_memory_address((self.SP + 1) & 0xFFFF) << 8  # High
        self.PC |= self.fetch_memory_address(self.SP)  # Low
        self.SP += 2
        self.SP &= 0xFFFF
        return 16

    def JP_DA(self, value):  # DA JP C,a16
        if self.c_flag != 0:
            self.PC = value
            return 16
        else:
            self.PC += 3
            self.PC &= 0xFFFF
            return 12

    def CALL_DC(self, value):  # DC CALL C,a16
        self.PC += 3
        if self.c_flag != 0:
            self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
            self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
            self.SP -= 2
            self.SP &= 0xFFFF
            self.PC = value
            return 24
        else:
            return 12

    def SBC_DE(self, value):  # DE SBC A,d8
        temp = self.A - value - self.c_flag != 0
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (value & 0xF) - self.c_flag != 0) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RST_DF(self):  # DF RST 18H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 24
        return 16

    def LDH_E0(self, value):  # E0 LDH (a8),A
        self.set_memory_address(value + 0xFF00, self.A)
        self.PC += 2
        return 12

    def POP_E1(self):  # E1 POP HL
        self.HL = (self.fetch_memory_address((self.SP + 1) & 0xFFFF) << 8) + self.fetch_memory_address(self.SP)  # High
        self.SP += 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 12

    def LD_E2(self):  # E2 LD (C),A
        self.set_memory_address(0xFF00 + self.C, self.A)
        self.PC += 1
        return 8

    def PUSH_E5(self):  # E5 PUSH HL
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.HL >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.HL & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 16

    def AND_E6(self, value):  # E6 AND d8
        temp = self.A & value
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RST_E7(self):  # E7 RST 20H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 32
        return 16

    def ADD_E8(self, value):  # E8 ADD SP,r8
        temp = self.SP + ((value ^ 0x80) - 0x80)
        flag = 0b00000000
        flag += (((self.SP & 0xF) + (value & 0xF)) > 0xF) << self.h_flag
        flag += (((self.SP & 0xFF) + (value & 0xFF)) > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFFFF
        self.SP = temp
        self.PC += 2
        return 16

    def JP_E9(self):  # E9 JP (HL)
        self.PC = self.HL
        return 4

    def LD_EA(self, value):  # EA LD (a16),A
        self.set_memory_address(value, self.A)
        self.PC += 3
        return 16

    def XOR_EE(self, value):  # EE XOR d8
        temp = self.A ^ value
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RST_EF(self):  # EF RST 28H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 40
        return 16

    def LDH_F0(self, value):  # F0 LDH A,(a8)
        self.A = self.fetch_memory_address(value + 0xFF00)
        self.PC += 2
        return 12

    def POP_F1(self):  # F1 POP AF
        self.A = self.fetch_memory_address((self.SP + 1) & 0xFFFF)  # High
        self.F = self.fetch_memory_address(self.SP) & 0xF0 & 0xF0  # Low
        self.SP += 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 12

    def LD_F2(self):  # F2 LD A,(C)
        self.A = self.fetch_memory_address(0xFF00 + self.C)
        self.PC += 1
        return 8

    def DI_F3(self):  # F3 DI
        self.interrupt_master_enable = False
        self.PC += 1
        return 4

    def PUSH_F5(self):  # F5 PUSH AF
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.A)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.F & 0xF0)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC += 1
        return 16

    def OR_F6(self, value):  # F6 OR d8
        temp = self.A | value
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RST_F7(self):  # F7 RST 30H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 48
        return 16

    def LD_F8(self, value):  # F8 LD HL,SP+r8
        self.HL = self.SP + ((value ^ 0x80) - 0x80)
        temp = self.HL
        flag = 0b00000000
        flag += (((self.SP & 0xF) + (value & 0xF)) > 0xF) << self.h_flag
        flag += (((self.SP & 0xFF) + (value & 0xFF)) > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        self.HL &= 0xFFFF
        self.PC += 2
        return 12

    def LD_F9(self):  # F9 LD SP,HL
        self.SP = self.HL
        self.PC += 1
        return 8

    def LD_FA(self, value):  # FA LD A,(a16)
        self.A = self.fetch_memory_address(value)
        self.PC += 3
        return 16

    def EI_FB(self):  # FB EI
        self.interrupt_master_enable = True
        self.PC += 1
        return 4

    def CP_FE(self, value):  # FE CP d8
        temp = self.A - value
        flag = 0b01000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (((self.A & 0xF) - (value & 0xF)) < 0) << self.h_flag
        flag += (temp < 0) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.PC += 2
        return 8

    def RST_FF(self):  # FF RST 38H
        self.PC += 1
        self.set_memory_address((self.SP - 1) & 0xFFFF, self.PC >> 8)  # High
        self.set_memory_address((self.SP - 2) & 0xFFFF, self.PC & 0xFF)  # Low
        self.SP -= 2
        self.SP &= 0xFFFF
        self.PC = 56
        return 16

    def RLC_100(self):  # 100 RLC B
        temp = (self.B << 1) + (self.B >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def RLC_101(self):  # 101 RLC C
        temp = (self.C << 1) + (self.C >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def RLC_102(self):  # 102 RLC D
        temp = (self.D << 1) + (self.D >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def RLC_103(self):  # 103 RLC E
        temp = (self.E << 1) + (self.E >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def RLC_104(self):  # 104 RLC H
        temp = ((self.HL >> 8) << 1) + ((self.HL >> 8) >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RLC_105(self):  # 105 RLC L
        temp = ((self.HL & 0xFF) << 1) + ((self.HL & 0xFF) >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RLC_106(self):  # 106 RLC (HL)
        temp = (self.fetch_memory_address(self.HL) << 1) + (self.fetch_memory_address(self.HL) >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RLC_107(self):  # 107 RLC A
        temp = (self.A << 1) + (self.A >> 7)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RRC_108(self):  # 108 RRC B
        temp = (self.B >> 1) + ((self.B & 1) << 7) + ((self.B & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def RRC_109(self):  # 109 RRC C
        temp = (self.C >> 1) + ((self.C & 1) << 7) + ((self.C & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def RRC_10A(self):  # 10A RRC D
        temp = (self.D >> 1) + ((self.D & 1) << 7) + ((self.D & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def RRC_10B(self):  # 10B RRC E
        temp = (self.E >> 1) + ((self.E & 1) << 7) + ((self.E & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def RRC_10C(self):  # 10C RRC H
        temp = ((self.HL >> 8) >> 1) + (((self.HL >> 8) & 1) << 7) + (((self.HL >> 8) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RRC_10D(self):  # 10D RRC L
        temp = ((self.HL & 0xFF) >> 1) + (((self.HL & 0xFF) & 1) << 7) + (((self.HL & 0xFF) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RRC_10E(self):  # 10E RRC (HL)
        temp = (self.fetch_memory_address(self.HL) >> 1) + ((self.fetch_memory_address(self.HL) & 1) << 7) + ((self.fetch_memory_address(self.HL) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RRC_10F(self):  # 10F RRC A
        temp = (self.A >> 1) + ((self.A & 1) << 7) + ((self.A & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RL_110(self):  # 110 RL B
        temp = (self.B << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def RL_111(self):  # 111 RL C
        temp = (self.C << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def RL_112(self):  # 112 RL D
        temp = (self.D << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def RL_113(self):  # 113 RL E
        temp = (self.E << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def RL_114(self):  # 114 RL H
        temp = ((self.HL >> 8) << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RL_115(self):  # 115 RL L
        temp = ((self.HL & 0xFF) << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RL_116(self):  # 116 RL (HL)
        temp = (self.fetch_memory_address(self.HL) << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RL_117(self):  # 117 RL A
        temp = (self.A << 1) + self.c_flag != 0
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def RR_118(self):  # 118 RR B
        temp = (self.B >> 1) + (self.c_flag != 0 << 7) + ((self.B & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def RR_119(self):  # 119 RR C
        temp = (self.C >> 1) + (self.c_flag != 0 << 7) + ((self.C & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def RR_11A(self):  # 11A RR D
        temp = (self.D >> 1) + (self.c_flag != 0 << 7) + ((self.D & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def RR_11B(self):  # 11B RR E
        temp = (self.E >> 1) + (self.c_flag != 0 << 7) + ((self.E & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def RR_11C(self):  # 11C RR H
        temp = ((self.HL >> 8) >> 1) + (self.c_flag != 0 << 7) + (((self.HL >> 8) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RR_11D(self):  # 11D RR L
        temp = ((self.HL & 0xFF) >> 1) + (self.c_flag != 0 << 7) + (((self.HL & 0xFF) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RR_11E(self):  # 11E RR (HL)
        temp = (self.fetch_memory_address(self.HL) >> 1) + (self.c_flag != 0 << 7) + ((self.fetch_memory_address(self.HL) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RR_11F(self):  # 11F RR A
        temp = (self.A >> 1) + (self.c_flag != 0 << 7) + ((self.A & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def SLA_120(self):  # 120 SLA B
        temp = (self.B << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def SLA_121(self):  # 121 SLA C
        temp = (self.C << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def SLA_122(self):  # 122 SLA D
        temp = (self.D << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def SLA_123(self):  # 123 SLA E
        temp = (self.E << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def SLA_124(self):  # 124 SLA H
        temp = ((self.HL >> 8) << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SLA_125(self):  # 125 SLA L
        temp = ((self.HL & 0xFF) << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SLA_126(self):  # 126 SLA (HL)
        temp = (self.fetch_memory_address(self.HL) << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SLA_127(self):  # 127 SLA A
        temp = (self.A << 1)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def SRA_128(self):  # 128 SRA B
        temp = ((self.B >> 1) | (self.B & 0x80)) + ((self.B & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def SRA_129(self):  # 129 SRA C
        temp = ((self.C >> 1) | (self.C & 0x80)) + ((self.C & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def SRA_12A(self):  # 12A SRA D
        temp = ((self.D >> 1) | (self.D & 0x80)) + ((self.D & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def SRA_12B(self):  # 12B SRA E
        temp = ((self.E >> 1) | (self.E & 0x80)) + ((self.E & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def SRA_12C(self):  # 12C SRA H
        temp = (((self.HL >> 8) >> 1) | ((self.HL >> 8) & 0x80)) + (((self.HL >> 8) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SRA_12D(self):  # 12D SRA L
        temp = (((self.HL & 0xFF) >> 1) | ((self.HL & 0xFF) & 0x80)) + (((self.HL & 0xFF) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SRA_12E(self):  # 12E SRA (HL)
        temp = ((self.fetch_memory_address(self.HL) >> 1) | (self.fetch_memory_address(self.HL) & 0x80)) + ((self.fetch_memory_address(self.HL) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SRA_12F(self):  # 12F SRA A
        temp = ((self.A >> 1) | (self.A & 0x80)) + ((self.A & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def SWAP_130(self):  # 130 SWAP B
        temp = ((self.B & 0xF0) >> 4) | ((self.B & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def SWAP_131(self):  # 131 SWAP C
        temp = ((self.C & 0xF0) >> 4) | ((self.C & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def SWAP_132(self):  # 132 SWAP D
        temp = ((self.D & 0xF0) >> 4) | ((self.D & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def SWAP_133(self):  # 133 SWAP E
        temp = ((self.E & 0xF0) >> 4) | ((self.E & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def SWAP_134(self):  # 134 SWAP H
        temp = (((self.HL >> 8) & 0xF0) >> 4) | (((self.HL >> 8) & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SWAP_135(self):  # 135 SWAP L
        temp = (((self.HL & 0xFF) & 0xF0) >> 4) | (((self.HL & 0xFF) & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SWAP_136(self):  # 136 SWAP (HL)
        temp = ((self.fetch_memory_address(self.HL) & 0xF0) >> 4) | ((self.fetch_memory_address(self.HL) & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SWAP_137(self):  # 137 SWAP A
        temp = ((self.A & 0xF0) >> 4) | ((self.A & 0x0F) << 4)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def SRL_138(self):  # 138 SRL B
        temp = (self.B >> 1) + ((self.B & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.B = temp
        self.PC += 2
        return 8

    def SRL_139(self):  # 139 SRL C
        temp = (self.C >> 1) + ((self.C & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.C = temp
        self.PC += 2
        return 8

    def SRL_13A(self):  # 13A SRL D
        temp = (self.D >> 1) + ((self.D & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.D = temp
        self.PC += 2
        return 8

    def SRL_13B(self):  # 13B SRL E
        temp = (self.E >> 1) + ((self.E & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.E = temp
        self.PC += 2
        return 8

    def SRL_13C(self):  # 13C SRL H
        temp = ((self.HL >> 8) >> 1) + (((self.HL >> 8) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SRL_13D(self):  # 13D SRL L
        temp = ((self.HL & 0xFF) >> 1) + (((self.HL & 0xFF) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SRL_13E(self):  # 13E SRL (HL)
        temp = (self.fetch_memory_address(self.HL) >> 1) + ((self.fetch_memory_address(self.HL) & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SRL_13F(self):  # 13F SRL A
        temp = (self.A >> 1) + ((self.A & 1) << 8)
        flag = 0b00000000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        flag += (temp > 0xFF) << self.c_flag
        self.F &= 0b00000000
        self.F |= flag
        temp &= 0xFF
        self.A = temp
        self.PC += 2
        return 8

    def BIT_140(self):  # 140 BIT 0,B
        temp = self.B & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_141(self):  # 141 BIT 0,C
        temp = self.C & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_142(self):  # 142 BIT 0,D
        temp = self.D & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_143(self):  # 143 BIT 0,E
        temp = self.E & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_144(self):  # 144 BIT 0,H
        temp = (self.HL >> 8) & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_145(self):  # 145 BIT 0,L
        temp = (self.HL & 0xFF) & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_146(self):  # 146 BIT 0,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_147(self):  # 147 BIT 0,A
        temp = self.A & (1 << 0)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_148(self):  # 148 BIT 1,B
        temp = self.B & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_149(self):  # 149 BIT 1,C
        temp = self.C & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_14A(self):  # 14A BIT 1,D
        temp = self.D & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_14B(self):  # 14B BIT 1,E
        temp = self.E & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_14C(self):  # 14C BIT 1,H
        temp = (self.HL >> 8) & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_14D(self):  # 14D BIT 1,L
        temp = (self.HL & 0xFF) & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_14E(self):  # 14E BIT 1,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_14F(self):  # 14F BIT 1,A
        temp = self.A & (1 << 1)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_150(self):  # 150 BIT 2,B
        temp = self.B & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_151(self):  # 151 BIT 2,C
        temp = self.C & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_152(self):  # 152 BIT 2,D
        temp = self.D & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_153(self):  # 153 BIT 2,E
        temp = self.E & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_154(self):  # 154 BIT 2,H
        temp = (self.HL >> 8) & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_155(self):  # 155 BIT 2,L
        temp = (self.HL & 0xFF) & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_156(self):  # 156 BIT 2,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_157(self):  # 157 BIT 2,A
        temp = self.A & (1 << 2)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_158(self):  # 158 BIT 3,B
        temp = self.B & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_159(self):  # 159 BIT 3,C
        temp = self.C & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_15A(self):  # 15A BIT 3,D
        temp = self.D & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_15B(self):  # 15B BIT 3,E
        temp = self.E & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_15C(self):  # 15C BIT 3,H
        temp = (self.HL >> 8) & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_15D(self):  # 15D BIT 3,L
        temp = (self.HL & 0xFF) & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_15E(self):  # 15E BIT 3,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_15F(self):  # 15F BIT 3,A
        temp = self.A & (1 << 3)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_160(self):  # 160 BIT 4,B
        temp = self.B & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_161(self):  # 161 BIT 4,C
        temp = self.C & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_162(self):  # 162 BIT 4,D
        temp = self.D & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_163(self):  # 163 BIT 4,E
        temp = self.E & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_164(self):  # 164 BIT 4,H
        temp = (self.HL >> 8) & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_165(self):  # 165 BIT 4,L
        temp = (self.HL & 0xFF) & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_166(self):  # 166 BIT 4,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_167(self):  # 167 BIT 4,A
        temp = self.A & (1 << 4)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_168(self):  # 168 BIT 5,B
        temp = self.B & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_169(self):  # 169 BIT 5,C
        temp = self.C & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_16A(self):  # 16A BIT 5,D
        temp = self.D & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_16B(self):  # 16B BIT 5,E
        temp = self.E & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_16C(self):  # 16C BIT 5,H
        temp = (self.HL >> 8) & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_16D(self):  # 16D BIT 5,L
        temp = (self.HL & 0xFF) & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_16E(self):  # 16E BIT 5,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_16F(self):  # 16F BIT 5,A
        temp = self.A & (1 << 5)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_170(self):  # 170 BIT 6,B
        temp = self.B & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_171(self):  # 171 BIT 6,C
        temp = self.C & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_172(self):  # 172 BIT 6,D
        temp = self.D & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_173(self):  # 173 BIT 6,E
        temp = self.E & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_174(self):  # 174 BIT 6,H
        temp = (self.HL >> 8) & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_175(self):  # 175 BIT 6,L
        temp = (self.HL & 0xFF) & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_176(self):  # 176 BIT 6,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_177(self):  # 177 BIT 6,A
        temp = self.A & (1 << 6)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_178(self):  # 178 BIT 7,B
        temp = self.B & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_179(self):  # 179 BIT 7,C
        temp = self.C & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_17A(self):  # 17A BIT 7,D
        temp = self.D & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_17B(self):  # 17B BIT 7,E
        temp = self.E & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_17C(self):  # 17C BIT 7,H
        temp = (self.HL >> 8) & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_17D(self):  # 17D BIT 7,L
        temp = (self.HL & 0xFF) & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def BIT_17E(self):  # 17E BIT 7,(HL)
        temp = self.fetch_memory_address(self.HL) & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 16

    def BIT_17F(self):  # 17F BIT 7,A
        temp = self.A & (1 << 7)
        flag = 0b00100000
        flag += ((temp & 0xFF) == 0) << self.z_flag
        self.F &= 0b00010000
        self.F |= flag
        self.PC += 2
        return 8

    def RES_180(self):  # 180 RES 0,B
        temp = self.B & ~(1 << 0)
        self.B = temp
        self.PC += 2
        return 8

    def RES_181(self):  # 181 RES 0,C
        temp = self.C & ~(1 << 0)
        self.C = temp
        self.PC += 2
        return 8

    def RES_182(self):  # 182 RES 0,D
        temp = self.D & ~(1 << 0)
        self.D = temp
        self.PC += 2
        return 8

    def RES_183(self):  # 183 RES 0,E
        temp = self.E & ~(1 << 0)
        self.E = temp
        self.PC += 2
        return 8

    def RES_184(self):  # 184 RES 0,H
        temp = (self.HL >> 8) & ~(1 << 0)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_185(self):  # 185 RES 0,L
        temp = (self.HL & 0xFF) & ~(1 << 0)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_186(self):  # 186 RES 0,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 0)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_187(self):  # 187 RES 0,A
        temp = self.A & ~(1 << 0)
        self.A = temp
        self.PC += 2
        return 8

    def RES_188(self):  # 188 RES 1,B
        temp = self.B & ~(1 << 1)
        self.B = temp
        self.PC += 2
        return 8

    def RES_189(self):  # 189 RES 1,C
        temp = self.C & ~(1 << 1)
        self.C = temp
        self.PC += 2
        return 8

    def RES_18A(self):  # 18A RES 1,D
        temp = self.D & ~(1 << 1)
        self.D = temp
        self.PC += 2
        return 8

    def RES_18B(self):  # 18B RES 1,E
        temp = self.E & ~(1 << 1)
        self.E = temp
        self.PC += 2
        return 8

    def RES_18C(self):  # 18C RES 1,H
        temp = (self.HL >> 8) & ~(1 << 1)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_18D(self):  # 18D RES 1,L
        temp = (self.HL & 0xFF) & ~(1 << 1)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_18E(self):  # 18E RES 1,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 1)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_18F(self):  # 18F RES 1,A
        temp = self.A & ~(1 << 1)
        self.A = temp
        self.PC += 2
        return 8

    def RES_190(self):  # 190 RES 2,B
        temp = self.B & ~(1 << 2)
        self.B = temp
        self.PC += 2
        return 8

    def RES_191(self):  # 191 RES 2,C
        temp = self.C & ~(1 << 2)
        self.C = temp
        self.PC += 2
        return 8

    def RES_192(self):  # 192 RES 2,D
        temp = self.D & ~(1 << 2)
        self.D = temp
        self.PC += 2
        return 8

    def RES_193(self):  # 193 RES 2,E
        temp = self.E & ~(1 << 2)
        self.E = temp
        self.PC += 2
        return 8

    def RES_194(self):  # 194 RES 2,H
        temp = (self.HL >> 8) & ~(1 << 2)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_195(self):  # 195 RES 2,L
        temp = (self.HL & 0xFF) & ~(1 << 2)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_196(self):  # 196 RES 2,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 2)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_197(self):  # 197 RES 2,A
        temp = self.A & ~(1 << 2)
        self.A = temp
        self.PC += 2
        return 8

    def RES_198(self):  # 198 RES 3,B
        temp = self.B & ~(1 << 3)
        self.B = temp
        self.PC += 2
        return 8

    def RES_199(self):  # 199 RES 3,C
        temp = self.C & ~(1 << 3)
        self.C = temp
        self.PC += 2
        return 8

    def RES_19A(self):  # 19A RES 3,D
        temp = self.D & ~(1 << 3)
        self.D = temp
        self.PC += 2
        return 8

    def RES_19B(self):  # 19B RES 3,E
        temp = self.E & ~(1 << 3)
        self.E = temp
        self.PC += 2
        return 8

    def RES_19C(self):  # 19C RES 3,H
        temp = (self.HL >> 8) & ~(1 << 3)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_19D(self):  # 19D RES 3,L
        temp = (self.HL & 0xFF) & ~(1 << 3)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_19E(self):  # 19E RES 3,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 3)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_19F(self):  # 19F RES 3,A
        temp = self.A & ~(1 << 3)
        self.A = temp
        self.PC += 2
        return 8

    def RES_1A0(self):  # 1A0 RES 4,B
        temp = self.B & ~(1 << 4)
        self.B = temp
        self.PC += 2
        return 8

    def RES_1A1(self):  # 1A1 RES 4,C
        temp = self.C & ~(1 << 4)
        self.C = temp
        self.PC += 2
        return 8

    def RES_1A2(self):  # 1A2 RES 4,D
        temp = self.D & ~(1 << 4)
        self.D = temp
        self.PC += 2
        return 8

    def RES_1A3(self):  # 1A3 RES 4,E
        temp = self.E & ~(1 << 4)
        self.E = temp
        self.PC += 2
        return 8

    def RES_1A4(self):  # 1A4 RES 4,H
        temp = (self.HL >> 8) & ~(1 << 4)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_1A5(self):  # 1A5 RES 4,L
        temp = (self.HL & 0xFF) & ~(1 << 4)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_1A6(self):  # 1A6 RES 4,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 4)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_1A7(self):  # 1A7 RES 4,A
        temp = self.A & ~(1 << 4)
        self.A = temp
        self.PC += 2
        return 8

    def RES_1A8(self):  # 1A8 RES 5,B
        temp = self.B & ~(1 << 5)
        self.B = temp
        self.PC += 2
        return 8

    def RES_1A9(self):  # 1A9 RES 5,C
        temp = self.C & ~(1 << 5)
        self.C = temp
        self.PC += 2
        return 8

    def RES_1AA(self):  # 1AA RES 5,D
        temp = self.D & ~(1 << 5)
        self.D = temp
        self.PC += 2
        return 8

    def RES_1AB(self):  # 1AB RES 5,E
        temp = self.E & ~(1 << 5)
        self.E = temp
        self.PC += 2
        return 8

    def RES_1AC(self):  # 1AC RES 5,H
        temp = (self.HL >> 8) & ~(1 << 5)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_1AD(self):  # 1AD RES 5,L
        temp = (self.HL & 0xFF) & ~(1 << 5)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_1AE(self):  # 1AE RES 5,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 5)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_1AF(self):  # 1AF RES 5,A
        temp = self.A & ~(1 << 5)
        self.A = temp
        self.PC += 2
        return 8

    def RES_1B0(self):  # 1B0 RES 6,B
        temp = self.B & ~(1 << 6)
        self.B = temp
        self.PC += 2
        return 8

    def RES_1B1(self):  # 1B1 RES 6,C
        temp = self.C & ~(1 << 6)
        self.C = temp
        self.PC += 2
        return 8

    def RES_1B2(self):  # 1B2 RES 6,D
        temp = self.D & ~(1 << 6)
        self.D = temp
        self.PC += 2
        return 8

    def RES_1B3(self):  # 1B3 RES 6,E
        temp = self.E & ~(1 << 6)
        self.E = temp
        self.PC += 2
        return 8

    def RES_1B4(self):  # 1B4 RES 6,H
        temp = (self.HL >> 8) & ~(1 << 6)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_1B5(self):  # 1B5 RES 6,L
        temp = (self.HL & 0xFF) & ~(1 << 6)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_1B6(self):  # 1B6 RES 6,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 6)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_1B7(self):  # 1B7 RES 6,A
        temp = self.A & ~(1 << 6)
        self.A = temp
        self.PC += 2
        return 8

    def RES_1B8(self):  # 1B8 RES 7,B
        temp = self.B & ~(1 << 7)
        self.B = temp
        self.PC += 2
        return 8

    def RES_1B9(self):  # 1B9 RES 7,C
        temp = self.C & ~(1 << 7)
        self.C = temp
        self.PC += 2
        return 8

    def RES_1BA(self):  # 1BA RES 7,D
        temp = self.D & ~(1 << 7)
        self.D = temp
        self.PC += 2
        return 8

    def RES_1BB(self):  # 1BB RES 7,E
        temp = self.E & ~(1 << 7)
        self.E = temp
        self.PC += 2
        return 8

    def RES_1BC(self):  # 1BC RES 7,H
        temp = (self.HL >> 8) & ~(1 << 7)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def RES_1BD(self):  # 1BD RES 7,L
        temp = (self.HL & 0xFF) & ~(1 << 7)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def RES_1BE(self):  # 1BE RES 7,(HL)
        temp = self.fetch_memory_address(self.HL) & ~(1 << 7)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def RES_1BF(self):  # 1BF RES 7,A
        temp = self.A & ~(1 << 7)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1C0(self):  # 1C0 SET 0,B
        temp = self.B | (1 << 0)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1C1(self):  # 1C1 SET 0,C
        temp = self.C | (1 << 0)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1C2(self):  # 1C2 SET 0,D
        temp = self.D | (1 << 0)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1C3(self):  # 1C3 SET 0,E
        temp = self.E | (1 << 0)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1C4(self):  # 1C4 SET 0,H
        temp = (self.HL >> 8) | (1 << 0)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1C5(self):  # 1C5 SET 0,L
        temp = (self.HL & 0xFF) | (1 << 0)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1C6(self):  # 1C6 SET 0,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 0)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1C7(self):  # 1C7 SET 0,A
        temp = self.A | (1 << 0)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1C8(self):  # 1C8 SET 1,B
        temp = self.B | (1 << 1)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1C9(self):  # 1C9 SET 1,C
        temp = self.C | (1 << 1)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1CA(self):  # 1CA SET 1,D
        temp = self.D | (1 << 1)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1CB(self):  # 1CB SET 1,E
        temp = self.E | (1 << 1)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1CC(self):  # 1CC SET 1,H
        temp = (self.HL >> 8) | (1 << 1)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1CD(self):  # 1CD SET 1,L
        temp = (self.HL & 0xFF) | (1 << 1)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1CE(self):  # 1CE SET 1,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 1)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1CF(self):  # 1CF SET 1,A
        temp = self.A | (1 << 1)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1D0(self):  # 1D0 SET 2,B
        temp = self.B | (1 << 2)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1D1(self):  # 1D1 SET 2,C
        temp = self.C | (1 << 2)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1D2(self):  # 1D2 SET 2,D
        temp = self.D | (1 << 2)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1D3(self):  # 1D3 SET 2,E
        temp = self.E | (1 << 2)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1D4(self):  # 1D4 SET 2,H
        temp = (self.HL >> 8) | (1 << 2)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1D5(self):  # 1D5 SET 2,L
        temp = (self.HL & 0xFF) | (1 << 2)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1D6(self):  # 1D6 SET 2,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 2)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1D7(self):  # 1D7 SET 2,A
        temp = self.A | (1 << 2)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1D8(self):  # 1D8 SET 3,B
        temp = self.B | (1 << 3)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1D9(self):  # 1D9 SET 3,C
        temp = self.C | (1 << 3)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1DA(self):  # 1DA SET 3,D
        temp = self.D | (1 << 3)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1DB(self):  # 1DB SET 3,E
        temp = self.E | (1 << 3)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1DC(self):  # 1DC SET 3,H
        temp = (self.HL >> 8) | (1 << 3)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1DD(self):  # 1DD SET 3,L
        temp = (self.HL & 0xFF) | (1 << 3)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1DE(self):  # 1DE SET 3,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 3)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1DF(self):  # 1DF SET 3,A
        temp = self.A | (1 << 3)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1E0(self):  # 1E0 SET 4,B
        temp = self.B | (1 << 4)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1E1(self):  # 1E1 SET 4,C
        temp = self.C | (1 << 4)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1E2(self):  # 1E2 SET 4,D
        temp = self.D | (1 << 4)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1E3(self):  # 1E3 SET 4,E
        temp = self.E | (1 << 4)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1E4(self):  # 1E4 SET 4,H
        temp = (self.HL >> 8) | (1 << 4)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1E5(self):  # 1E5 SET 4,L
        temp = (self.HL & 0xFF) | (1 << 4)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1E6(self):  # 1E6 SET 4,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 4)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1E7(self):  # 1E7 SET 4,A
        temp = self.A | (1 << 4)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1E8(self):  # 1E8 SET 5,B
        temp = self.B | (1 << 5)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1E9(self):  # 1E9 SET 5,C
        temp = self.C | (1 << 5)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1EA(self):  # 1EA SET 5,D
        temp = self.D | (1 << 5)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1EB(self):  # 1EB SET 5,E
        temp = self.E | (1 << 5)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1EC(self):  # 1EC SET 5,H
        temp = (self.HL >> 8) | (1 << 5)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1ED(self):  # 1ED SET 5,L
        temp = (self.HL & 0xFF) | (1 << 5)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1EE(self):  # 1EE SET 5,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 5)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1EF(self):  # 1EF SET 5,A
        temp = self.A | (1 << 5)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1F0(self):  # 1F0 SET 6,B
        temp = self.B | (1 << 6)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1F1(self):  # 1F1 SET 6,C
        temp = self.C | (1 << 6)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1F2(self):  # 1F2 SET 6,D
        temp = self.D | (1 << 6)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1F3(self):  # 1F3 SET 6,E
        temp = self.E | (1 << 6)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1F4(self):  # 1F4 SET 6,H
        temp = (self.HL >> 8) | (1 << 6)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1F5(self):  # 1F5 SET 6,L
        temp = (self.HL & 0xFF) | (1 << 6)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1F6(self):  # 1F6 SET 6,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 6)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1F7(self):  # 1F7 SET 6,A
        temp = self.A | (1 << 6)
        self.A = temp
        self.PC += 2
        return 8

    def SET_1F8(self):  # 1F8 SET 7,B
        temp = self.B | (1 << 7)
        self.B = temp
        self.PC += 2
        return 8

    def SET_1F9(self):  # 1F9 SET 7,C
        temp = self.C | (1 << 7)
        self.C = temp
        self.PC += 2
        return 8

    def SET_1FA(self):  # 1FA SET 7,D
        temp = self.D | (1 << 7)
        self.D = temp
        self.PC += 2
        return 8

    def SET_1FB(self):  # 1FB SET 7,E
        temp = self.E | (1 << 7)
        self.E = temp
        self.PC += 2
        return 8

    def SET_1FC(self):  # 1FC SET 7,H
        temp = (self.HL >> 8) | (1 << 7)
        self.HL = (self.HL & 0x00FF) | (temp << 8)
        self.PC += 2
        return 8

    def SET_1FD(self):  # 1FD SET 7,L
        temp = (self.HL & 0xFF) | (1 << 7)
        self.HL = (self.HL & 0xFF00) | (temp & 0xFF)
        self.PC += 2
        return 8

    def SET_1FE(self):  # 1FE SET 7,(HL)
        temp = self.fetch_memory_address(self.HL) | (1 << 7)
        self.set_memory_address(self.HL, temp)
        self.PC += 2
        return 16

    def SET_1FF(self):  # 1FF SET 7,A
        temp = self.A | (1 << 7)
        self.A = temp
        self.PC += 2
        return 8