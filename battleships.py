
import pygame
import random
from abc import ABC
from enum import Enum
from itertools import zip_longest


class Direction(Enum):
    """A enum for storing the four points of the compass"""
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    @property
    def next(self):
        """Returns the next point of the compass, for rotations"""
        return Direction((self.value + 1) % 4)


class Ship:
    """An object to store the data of one ship"""

    def __init__(self, x, y, d, l):
        self.location = (x, y)
        self.direction = d
        self.length = l

    @property
    def coordinate_list(self):
        """Calculates the list of coordinates that the ship is located over"""
        x, y = self.location
        if self.direction == Direction.NORTH:
            return [(x, y - i) for i in range(self.length)]
        elif self.direction == Direction.EAST:
            return [(x + i, y) for i in range(self.length)]
        elif self.direction == Direction.SOUTH:
            return [(x, y + i) for i in range(self.length)]
        elif self.direction == Direction.WEST:
            return [(x - i, y) for i in range(self.length)]

    def rotate(self):
        """Rotates the ship"""
        self.direction = self.direction.next

    def __repr__(self):
        """A nice representation of the Ship object, for debugging"""
        return "<Ship Object: ({},{}), {}, Length {}>".format(
            *self.location, self.direction, self.length)


class Board(ABC):
    """A abstract base class for boards"""

    def __init__(self, size=10, ship_sizes=[6, 4, 3, 3, 2]):
        self.size = size
        self.ship_sizes = ship_sizes
        self.ships_list = []
        self.hits_list = []
        self.misses_list = []

    def is_valid(self, ship):
        """Checks whether a ship would be a valid placement on the board"""
        for x, y in ship.coordinate_list:
            if x < 0 or y < 0 or x >= self.size or y >= self.size:
                return False
        for otherShip in self.ships_list:
            if self.ships_overlap(ship, otherShip):
                return False
        return True

    def add_ship(self, ship: Ship):
        """Adds a ship to the board"""
        if self.is_valid(ship):
            self.ships_list.append(ship)
            return True
        else:
            return False

    def remove_ship(self, ship):
        """Removes a ship from the board"""
        self.ships_list.remove(ship)

    def ships_overlap(self, ship1, ship2):
        """Checks whether two ships overlap"""
        for ship1_coord in ship1.coordinate_list:
            for ship2_coord in ship2.coordinate_list:
                if ship1_coord == ship2_coord:
                    return True
        return False

    def get_ship(self, x, y):
        """Gets a ship object from coordinates"""
        for ship in self.ships_list:
            if (x, y) in ship.coordinate_list:
                return ship
        return None

    def valid_target(self, x, y):
        """Checks whether a set of coordinates is a valid shot

        Coordinates are within the board, and shot hasn't previously been taken
        """
        if x not in range(self.size) or y not in range(self.size):
            return False
        for previous_shot in self.misses_list + self.hits_list:
            if (x, y) == previous_shot:
                return False
        return True

    def shoot(self, x, y):
        """Registers a shot on the board, saving to appropriate list"""
        if not self.valid_target(x, y):
            return False

        for ship in self.ships_list:
            for ship_coordinate in ship.coordinate_list:
                if (x, y) == ship_coordinate:
                    self.hits_list.append((x, y))
                    return True

        self.misses_list.append((x, y))
        return True

    def colour_grid(self, colours, include_ships=True):
        """Calculates a colour representation of the board for display"""
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

    @property
    def gameover(self):
        """Checks to see if all the ships have been fully hit"""
        for ship in self.ships_list:
            for coordinate in ship.coordinate_list:
                if coordinate not in self.hits_list:
                    return False
        return True

    def __str__(self):
        """String representation of the board

        similar to colour grid but for printing
        """
        output = (("~" * self.size) + "\n") * self.size
        for ship in self.ships_list:
            for x, y in ship.coordinate_list:
                output[x + y * (self.size + 1)] = "S"
        return output


class PlayerBoard(Board):
    """A Board for user input"""

    def __init__(self, display, board_size, ship_sizes):
        """Initialises the board by placing ships."""
        super().__init__(board_size, ship_sizes)
        self.display = display

        direction = Direction.NORTH
        while True:
            self.display.show(None, self)

            if self.ship_to_place:
                text = 'Click where you want your {}-long ship to be:'.format(
                    self.ship_to_place)
            else:
                text = 'Click again to rotate a ship, or elsewhere if ready.'
            self.display.show_text(text, lower=True)

            x, y = self.display.get_input()
            if x is not None and y is not None:
                ship = self.get_ship(x, y)
                if ship:
                    self.remove_ship(ship)
                    ship.rotate()
                    if self.is_valid(ship):
                        self.add_ship(ship)
                elif self.ship_to_place:
                    ship = Ship(x, y, direction, self.ship_to_place)
                    if self.is_valid(ship):
                        self.add_ship(ship)
                    else:
                        direction = direction.next
                else:
                    break

                if self.is_valid(ship):
                    self.add_ship(ship)

            Display.flip()

    @property
    def ship_to_place(self):
        """Returns a ship length that needs to be placed, if any"""
        placed_sizes = sorted(ship.length for ship in self.ships_list)
        sizes = sorted(self.ship_sizes)
        for placed, to_place in zip_longest(placed_sizes, sizes):
            if placed != to_place:
                return to_place
        return None


class AIBoard(Board):
    """A Board controlled by a AI"""

    def __init__(self, board_size, ship_sizes):
        """Initialises the board by randomly placing ships"""
        super().__init__(board_size, ship_sizes)
        for ship_length in self.ship_sizes:
            ship_added = False
            while not ship_added:
                x = random.randint(0, board_size - 1)
                y = random.randint(0, board_size - 1)
                ship_direction = random.choice(list(Direction))
                ship = Ship(x, y, ship_direction, ship_length)
                if self.is_valid(ship):
                    self.add_ship(ship)
                    ship_added = True


class Display:
    """Class to handle PyGame input and output"""
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
        """Requests appropriate COlour Grids from boards, and draws them"""
        if upper_board is not None:
            upper_colours = upper_board.colour_grid(
                self.colours, include_top_ships)

        if lower_board is not None:
            lower_colours = lower_board.colour_grid(
                self.colours)

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
        """Converts MouseEvents into board corrdinates, for input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Display.close()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                y = y % (self.board_size * self.cell_size + self.margin)
                x = (x - self.margin) // self.cell_size
                y = (y - self.margin) // self.cell_size
                if x in range(self.board_size) and y in range(self.board_size):
                    return x, y
        return None, None

    def show_text(self, text, upper=False, lower=False):
        """Displays text on the screen, either upper or lower """
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
    """The overall class to control the game"""

    def __init__(self, display, size=10, ship_sizes=[6, 4, 3, 3, 2]):
        """Sets up the game by generating two Boards"""
        self.display = display
        self.board_size = size
        self.ai_board = AIBoard(size, ship_sizes)
        self.player_board = PlayerBoard(display, size, ship_sizes)

    def play(self):
        """The main game loop, alternating shots until someone wins"""
        print("Play starts")
        while not self.gameover:
            if self.player_shot():
                self.ai_shot()
            self.display.show(self.ai_board, self.player_board)
            self.display.show_text("Click to guess:")
            Display.flip()

    def ai_shot(self):
        """The AI's shot selection just randomly selects coordinates"""
        x, y = -1, -1
        while not self.player_board.valid_target(x, y):
            x = random.randint(0, self.board_size - 1)
            y = random.randint(0, self.board_size - 1)
        self.player_board.shoot(x, y)

    def player_shot(self):
        """Uses input to decide if a shot is valid or not"""
        x, y = self.display.get_input()
        if self.ai_board.valid_target(x, y):
            self.ai_board.shoot(x, y)
            return True
        else:
            return False

    @property
    def gameover(self):
        """Determines and prints the winner"""
        if self.ai_board.gameover:
            print("Congratulations you won")
            return True
        elif self.player_board.gameover:
            print("Congratulations you lost")
            return True
        else:
            return False


if __name__ == "__main__":
    while True:
        d = Display()
        Game(d).play()
        # Game(d, 2, [1,1]).play()
        d.close()

        response = input("Replay? y/n: ").lower()
        while response not in ['y', 'n']:
            response = input("Must be y or n: ")
        if response == 'n':
            print("Thanks, goodbye.")
            break
