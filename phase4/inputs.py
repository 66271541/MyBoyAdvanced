import pynput

keyboard = pynput.keyboard.Controller
keys = pynput.keyboard.Key


def start():
    return 11010111


def select():
    return 11011011


def A():
    return 11011110


def B():
    return 11011101


def left():
    return 11101101


def right():
    return 11101110


def up():
    return 11101011


def down():
    return 11100111


def start_input_listener():
    def on_press(key):
        print(key)

        if key == keys.esc:
            return False
        if key == keys.up:
            return up()
        if key == keys.down:
            return down()
        if key == keys.left:
            return left()
        if key == keys.right:
            return right()
        if key == keys.enter:
            return start()
        if key == keys.space:
            return select()
        if key == 'A':
            return A()
        if key == 'B':
            return B()

    listener = pynput.keyboard.Listener(on_press=on_press)
    listener.start()
