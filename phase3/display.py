from pyxel import *

from phase4.inputs import *


class Interface:
    def __init__(self, cpu, mb):
        init(160, 144)
        self.cpu = cpu
        self.mb = mb

        run(self.update, self.draw)

    def update(self):

        self.cpu.execute()

        if btnp(GAMEPAD1_BUTTON_A):
            print(A())
        if btnp(GAMEPAD1_BUTTON_B):
            print(B())
        if btnp(GAMEPAD1_BUTTON_START):
            print(start())
        if btnp(GAMEPAD1_BUTTON_BACK):
            print(select())
        if btnp(GAMEPAD1_BUTTON_DPAD_DOWN):
            print(down())
        if btnp(GAMEPAD1_BUTTON_DPAD_UP):
            print(up())
        if btnp(GAMEPAD1_BUTTON_DPAD_LEFT):
            print(left())
        if btnp(GAMEPAD1_BUTTON_DPAD_RIGHT):
            print(right())


    def draw(self):
        cls(0)
        # pyxel.line()
    # == add inputs below
