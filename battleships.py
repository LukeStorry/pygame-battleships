
from typing import NamedTuple
from enum import Enum
import random
import pygame
import sys


ship_sizes = [6, 4, 3, 3, 2]
board_size = 10
margin = 15
cell_size = 40


colours = {
    "water": (0, 0, 150),
    "ship": (50, 50, 50),
    "hit": (255, 0, 0),
    "miss": (100, 150, 255),
    "background": (0, 0, 0),
    "text": (255, 255, 255)
}


class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    def next(self):
        return Direction((self.value + 1) % 4)


class Ship:
    def __init__(self, x, y, d, l):
        self.x = x
        self.y = y
        self.direction = d
        self.length = l

        self.coordinate_list = []
        for i in range(self.length):
            if self.direction is Direction.NORTH:
                self.coordinate_list.append((x, y - i))
            elif self.direction is Direction.EAST:
                self.coordinate_list.append((x + i, y))
            elif self.direction is Direction.SOUTH:
                self.coordinate_list.append((x, y + i))
            elif self.direction is Direction.WEST:
                self.coordinate_list.append((x - i, y))

    def __str__(self):
        return "Ship: ({}, {}), {}, Length {}".format(
            self.x, self.y, self.direction, self.length)


class Board:
    def __init__(self, size):
        self.size = size
        self.ships_list = []
        self.hits_list = []
        self.misses_list = []

    def is_valid(self, ship: Ship):
        for x, y in ship.coordinate_list:
            if x < 0 or y < 0 or x >= self.size or y >= self.size:
                return False
        for otherShip in self.ships_list:
            if self.ships_overlap(ship, otherShip):
                return False
        return True

    def add(self, ship):
        if self.is_valid(ship):
            self.ships_list.append(ship)
            return True
        else:
            return False

    def remove(self, ship):
        self.ships_list.remove(ship)

    def ships_overlap(self, ship1, ship2):
        for ship1_coord in ship1.coordinate_list:
            for ship2_coord in ship2.coordinate_list:
                if ship1_coord == ship2_coord:
                    return True
        return False

    def valid_target(self, x, y):
        for shot_x, shot_y in self.misses_list:
            if x == shot_x and y == shot_y:
                return False
        for shot_x, shot_y in self.hits_list:
            if x == shot_x and y == shot_y:
                return False
        return True

    def shoot(self, x, y):
        if x is None or y is None:
            return

        hit = False
        for ship in self.ships_list:
            for ship_x, ship_y in ship.coordinate_list:
                if x == ship_x and y == ship_y:
                    hit = True
                    break
        if hit:
            self.hits_list.append((x, y))
        else:
            self.misses_list.append((x, y))

    def colour_grid(self, include_ships):
        grid = [
            [colours["water"] for _ in range(self.size)]
            for _ in range(self.size)]

        if include_ships:
            for ship in self.ships_list:
                for x, y in ship.coordinate_list:
                    grid[y][x] = colours["ship"]

        for x, y in self.hits_list:
            grid[y][x] = colours["hit"]

        for x, y in self.misses_list:
            grid[y][x] = colours["miss"]

        return grid

    def gameover(self):
        for ship in self.ships_list:
            for coordinate in ship.coordinate_list:
                if coordinate not in self.hits_list:
                    return False
        return True

    def __str__(self):
        output = (("~" * self.size) + "\n") * self.size
        for ship in self.ships_list:
            for x, y in ship.coordinate_list:
                output[x + y * (self.size + 1)] = "S"
        return output


def init_screen():
    pygame.init()
    pygame.font.init()

    screen_width = cell_size * board_size + 2 * margin
    screen_height = 2 * cell_size * board_size + 3 * margin
    screen = pygame.display.set_mode([screen_width, screen_height])

    pygame.display.set_caption("Battleships")
    return screen


def display(screen, board1, board2, include_ai_ships=False):
    screen.fill(colours["background"])
    for y in range(board_size):
        for x in range(board_size):
            grid = board1.colour_grid(include_ships=include_ai_ships)
            rectangle = [margin + x * cell_size,
                         margin + y * cell_size, cell_size, cell_size]
            pygame.draw.rect(screen, grid[y][x], rectangle)

            grid = board2.colour_grid(include_ships=True)
            offset = margin * 2 + board_size * cell_size
            rectangle = [margin + x * cell_size, offset + y * cell_size,
                         cell_size, cell_size]
            pygame.draw.rect(screen, grid[y][x], rectangle)


def get_input(board):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_game()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            x = (x - margin) // cell_size
            if board == "upper":
                y = (y - margin) // cell_size
            else:
                y = (y - (board_size * cell_size + 2 * margin)) // cell_size
            if x >= 0 and y >= 0 and x < board_size and y < board_size:
                return x, y
    return None, None


def setup_ai_board():
    board = Board(board_size)
    for ship_length in ship_sizes:
        shipFound = False
        while not shipFound:
            x = random.randint(0, board_size - 1)
            y = random.randint(0, board_size - 1)
            ship_direction = random.choice(list(Direction))
            ship = Ship(x, y, ship_direction, ship_length)

            if board.is_valid(ship):
                board.add(ship)
                shipFound = True
    return board


def setup_player_board(screen):
    board = Board(board_size)
    ship = None
    ship_direction = Direction.NORTH
    setup_finished = False
    ship_num = 0
    while not setup_finished:
        display(screen, board, board)

        if ship is None:
            text = 'Click where you want your {}-long ship to be:'.format(
                ship_sizes[ship_num])
        elif ship_num < len(ship_sizes):
            text = 'Click again to rotate or add new {}-long ship:'.format(
                ship_sizes[ship_num + 1])
        else:
            text = 'Click again to rotate, or here if ready.'

        font = pygame.font.SysFont("Helvetica", 14)
        screen.blit(font.render(text, True, colours["text"]),
                    (margin, board_size * cell_size + margin * 2))

        click_x, click_y = get_input("lower")
        if click_x is not None and click_y is not None:
            if ship is not None:  # already a ship in the queue
                if ship.x == click_x and ship.y == click_y:  # rotate
                    board.remove(ship)
                    ship_direction = ship_direction.next()
                else:  # build new
                    ship_num += 1
            ship = Ship(click_x, click_y, ship_direction, ship_sizes[ship_num])

            # Add ship to board, or delete if not valid
            if board.is_valid(ship):
                board.add(ship)
            else:
                ship_direction = ship_direction.next()
                ship = None

        if len(board.ships_list) == len(ship_sizes):
            setup_finished = True

        pygame.display.flip()
        pygame.time.Clock().tick(60)
    return board


def ai_shoot(board):
    shot = False
    while not shot:
        x = random.randint(0, board_size - 1)
        y = random.randint(0, board_size - 1)
        if board.valid_target(x, y):
            board.shoot(x, y)
            shot = True


def player_shoot(board):
    x, y = get_input("upper")
    if x is not None and y is not None:
        if board.valid_target(x, y):
            board.shoot(x, y)
            return True
    else:
        return False


def check_gameover(board1, board2):
    if board1.gameover():
        print("Congratulations you won")
        return True
    elif board2.gameover():
        print("Congratulations you lost")
        return True
    else:
        return False


def play_game(ai_board, player_board, screen):
    game_finished = False
    while not game_finished:
        player_done = player_shoot(ai_board)

        if player_done:
            ai_shoot(player_board)

        display(screen, ai_board, player_board)
        text = "Click to guess:"
        font = pygame.font.SysFont("Helvetica", 14)
        screen.blit(font.render(
            text, True, colours["text"]), (margin, margin))
        pygame.display.flip()
        pygame.time.Clock().tick(60)

        game_finished = check_gameover(ai_board, player_board)


def new_game():
    screen = init_screen()
    ai_board = setup_ai_board()
    player_board = setup_player_board(screen)
    play_game(ai_board, player_board, screen)
    pygame.quit()


def main():
    replay = True
    while replay:
        new_game()
        response = input("Replay? y/n: ")

        while response not in ['y', 'n']:
            response = input("Must be y or n: ")

        if response == 'n':
            replay = False
            print("Thanks, goodbye.")


def quit_game():
    pygame.display.quit()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
