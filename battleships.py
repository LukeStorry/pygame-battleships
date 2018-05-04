
import pygame
import random
from enum import Enum


class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def next(self):
        return Direction((self.value + 1) % 4)


class Ship:
    def __init__(self, x, y, d, l):
        self.location = (x, y)
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
        return "Ship: ({},{}), {}, Length {}".format(
            *self.location, self.direction, self.length)


class Board:
    def __init__(self, size=10, ship_sizes=[6, 4, 3, 3, 2]):
        self.size = size
        self.ship_sizes = ship_sizes
        self.ships_list = []
        self.hits_list = []
        self.misses_list = []

    def is_valid(self, ship):
        for x, y in ship.coordinate_list:
            if x < 0 or y < 0 or x >= self.size or y >= self.size:
                return False
        for otherShip in self.ships_list:
            if self.ships_overlap(ship, otherShip):
                return False
        return True

    def add_ship(self, ship: Ship):
        if self.is_valid(ship):
            self.ships_list.append(ship)
            return True
        else:
            return False

    def remove_ship(self, ship):
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
        if x is None or y is None or not self.valid_target(x, y):
            return False

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

        return True

    def colour_grid(self, colours, include_ships):
        grid = [[colours["water"] for _ in range(self.size)]
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


class PlayerBoard(Board):
    def __init__(self, display, board_size, ship_sizes):
        super().__init__(board_size, ship_sizes)
        self.display = display
        self.place_ships()

    def place_ships(self):
        current_ship = None
        ship_direction = Direction.NORTH
        setup_finished = False
        ship_num = 0
        while not setup_finished:
            self.display.show(None, self)

            if current_ship is None:
                text = 'Click where you want your {}-long ship to be:'.format(
                    self.ship_sizes[ship_num])
            elif ship_num < len(self.ship_sizes) - 1:
                text = 'Click again to rotate or add new ' + \
                    '{}-long ship:'.format(self.ship_sizes[ship_num + 1])
            else:
                text = 'Click again to rotate, or elsewhere if ready.'
            self.display.show_text(text, lower=True)

            x, y = self.display.get_input()
            if x is not None and y is not None:
                if current_ship is not None:  # already a ship in the queue
                    if (x, y) == current_ship.location:  # same click, rotate
                        self.remove_ship(current_ship)
                        ship_direction = ship_direction.next()
                    else:  # clicked elsewhere
                        if ship_num >= len(self.ship_sizes) - 1:
                            setup_finished = True
                            return
                        else:  # build new
                            ship_num += 1

                current_ship = Ship(x, y, ship_direction,
                                    self.ship_sizes[ship_num])
                if not self.add_ship(current_ship):
                    ship_direction = ship_direction.next()
                    current_ship = None

            Display.flip()


class AIBoard(Board):
    def __init__(self, board_size, ship_sizes):
        super().__init__(board_size, ship_sizes)
        for ship_length in self.ship_sizes:
            shipFound = False
            while not shipFound:
                x = random.randint(0, board_size - 1)
                y = random.randint(0, board_size - 1)
                ship_direction = random.choice(list(Direction))
                ship = Ship(x, y, ship_direction, ship_length)
                if self.add_ship(ship):
                    shipFound = True


class Display:
    colours = {
        "water": pygame.color.Color("blue"),
        "ship": pygame.color.Color("gray"),
        "hit": pygame.color.Color("red"),
        "miss": pygame.color.Color("lightcyan"),
        "background": pygame.color.Color("navy"),
        "text": pygame.color.Color("white")
    }

    def __init__(self, board_size=10, cell_size=30, margin=15):
        self.board_size = board_size
        self.cell_size = cell_size
        self.margin = margin

        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("Helvetica", 14)

        screen_width = self.cell_size * board_size + 2 * margin
        screen_height = 2 * self.cell_size * board_size + 3 * margin
        self.screen = pygame.display.set_mode(
            [screen_width, screen_height])
        pygame.display.set_caption("Battleships")

    def show(self, upper_board, lower_board, include_top_ships=False):
        if upper_board is not None:
            upper_colours = upper_board.colour_grid(
                self.colours, include_top_ships)

        if lower_board is not None:
            lower_colours = lower_board.colour_grid(
                self.colours, include_ships=True)

        self.screen.fill(Display.colours["background"])
        for y in range(self.board_size):
            for x in range(self.board_size):

                if upper_board is not None:
                    pygame.draw.rect(self.screen, upper_colours[y][x],
                                     [self.margin + x * self.cell_size,
                                      self.margin + y * self.cell_size,
                                      self.cell_size, self.cell_size])

                if lower_board is not None:
                    offset = self.margin * 2 + self.board_size * self.cell_size
                    pygame.draw.rect(self.screen, lower_colours[y][x],
                                     [self.margin + x * self.cell_size,
                                      offset + y * self.cell_size,
                                      self.cell_size, self.cell_size])

    def get_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Display.close()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                y = y % (self.board_size * self.cell_size + self.margin)
                x = (x - self.margin) // self.cell_size
                y = (y - self.margin) // self.cell_size
                if x >= 0 and y >= 0 and \
                        x < self.board_size and y < self.board_size:
                    return x, y
        return None, None

    def show_text(self, text, upper=False, lower=False):
        x = self.margin
        y_up = x
        y_lo = self.board_size * self.cell_size + self.margin
        label = self.font.render(text, True, Display.colours["text"])
        if upper:
            self.screen.blit(label, (x, y_up))
        if lower:
            self.screen.blit(label, (x, y_lo))

    @classmethod
    def flip(cls):
        pygame.display.flip()
        pygame.time.Clock().tick(60)

    @classmethod
    def close(cls):
        pygame.display.quit()
        pygame.quit()


class Game:
    def __init__(self, display, size=10, ship_sizes=[6, 4, 3, 3, 2]):
        self.board_size = size
        self.display = display
        self.ai_board = AIBoard(size, ship_sizes)
        self.player_board = PlayerBoard(display, size, ship_sizes)

    def play(self):
        print("play starts")
        while not self.gameover():
            if self.player_shoot():
                self.ai_shoot()
            self.display.show(self.ai_board, self.player_board)
            self.display.show_text("Click to guess:")
            Display.flip()

    def ai_shoot(self):
        shot = False
        while not shot:
            x = random.randint(0, self.board_size - 1)
            y = random.randint(0, self.board_size - 1)
            shot = self.player_board.shoot(x, y)

    def player_shoot(self):
        x, y = self.display.get_input()
        return self.ai_board.shoot(x, y)

    def gameover(self):
        if self.ai_board.gameover():
            print("Congratulations you won")
            return True
        elif self.player_board.gameover():
            print("Congratulations you lost")
            return True
        else:
            return False


def main():
    replay = True
    while replay:
        d = Display()
        Game(d).play()
        # Game(d, 2, [1,1]).play()
        d.close()

        response = input("Replay? y/n: ")
        while response not in ['y', 'n']:
            response = input("Must be y or n: ")

        if response == 'n':
            replay = False
            print("Thanks, goodbye.")


if __name__ == "__main__":
    main()
