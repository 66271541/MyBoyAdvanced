from pathlib import Path


def phase_1_game_rom():
    game = Path('games/snake.gb')
    game_data = game.read_bytes()

    print(f"Length of cartridge data: {len(game_data)}")

    # header_data = game_data[0x100: 0x14F]
    print(f"Undecoded data: {game_data[:100]}")

    title = game_data[0x134: 0x142].decode(encoding='utf-8').replace("\x00", "")

    print(f"title: {title}")
    print(f"Colour mode (cdb): {int(game_data[0x143])}")
    print(f"license code: {game_data[0x144:0x145].decode(encoding='utf-8')}")
    print(f"sdb: {game_data[0x146]}")
    print(f"cartridge_type: {game_data[0x147]}")
    print(f"rom_size: {game_data[0x148]}")
    print(f"ram_size: {game_data[0x149]}")

    return game_data
