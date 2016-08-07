import itertools
import math
import random

import pygame

import resources


TILESIZE = 128


class Tile(object):
    TOP = 0
    LEFT = 1
    BOTTOM = 2
    RIGHT = 3

    VERTICAL = TOP
    HORIZONTAL = LEFT

    def __init__(self, name, img, fills, connectivity, orientations, volume,
                 frequency):
        self.name = name
        self.base_img = resources.load_png(img)
        self.img = [pygame.transform.rotate(self.base_img, 90 * o)
                    for o in (Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT)]
        self.fills = {
            c: {
                o: resources.load_spritesheet(
                    fill, self.base_img.get_size(), 90 * ((c + o) % 4),
                ) for o in orientations
            } for c, fill in fills.items()
        }
        self.volume = volume
        self.connectivity = frozenset(connectivity)
        self.orientations = orientations
        self.frequency = frequency

    def connected(self, orientation, direction):
        return (direction - orientation) % 4 in self.connectivity

    def connections(self, orientation):
        for connection in self.connectivity:
            yield (connection + orientation) % 4

    def ascii(self, orientation):
        return " {top} \n{left}#{right}\n {bottom} ".format(
            top="#" if self.connected(orientation, Tile.TOP) else " ",
            left="#" if self.connected(orientation, Tile.LEFT) else " ",
            bottom="#" if self.connected(orientation, Tile.BOTTOM) else " ",
            right="#" if self.connected(orientation, Tile.RIGHT) else " ",
        )


class Cell(object):
    def __init__(self, tile, orientation, rect, level, x, y):
        self.tile = tile
        self.orientation = orientation
        self.fill = [0.0] * 4
        self.animation = [0.0] * 4
        self.rect = rect
        self.flowing = False
        self.level = level
        self.x = x
        self.y = y

    def connected(self, direction):
        return self.tile.connected(self.orientation, direction)

    def draw(self, surface):
        surface.blit(self.tile.img[self.orientation], self.rect)
        for direction, fill in enumerate(self.animation):
            if fill > 0.0:
                source = (direction - self.orientation) % 4
                fills = self.tile.fills[source][self.orientation]
                frame = max(0, len(fills) - 1 - int(math.floor(fill)))
                surface.blit(fills[frame], self.rect)

    def flow(self, source, amount):
        if not self.connected(source):
            self.level.failed = True
            return amount
        if self.flowing:
            return amount
        if sum(self.fill) + amount > self.tile.volume:
            outgoing = []
            for c in self.tile.connections(self.orientation):
                if self.fill[c] == 0.0:
                    outgoing.append(c)
            self.flowing = True
            overflow = sum(self.fill) + amount - self.tile.volume
            self.fill[source] += self.tile.volume - sum(self.fill)
            while overflow > 0.0 and len(outgoing) > 0:
                overflow_new = 0.0
                outgoing_new = []
                for c in outgoing:
                    new_source, other = self.level.get_from(self, c)
                    if other is None:
                        self.level.failed = True
                        overflow_new += overflow / len(outgoing)
                        continue

                    remainder = other.flow(new_source,
                                           overflow / len(outgoing))
                    if remainder > 0.0:
                        overflow_new += remainder
                    else:
                        outgoing_new.append(c)
                overflow = overflow_new
                outgoing = outgoing_new
            self.flowing = False
            self.animation[source] += amount - overflow
            return overflow
        else:
            self.fill[source] += amount
            self.animation[source] += amount
            return 0.0


class Level(object):
    def __init__(self, width, height):
        self.tileset = [
            Tile(
                name='straight',
                img='img/StraightPipe.png',
                fills={
                    Tile.TOP: 'img/FillAnimateStraightPipe.png',
                    Tile.BOTTOM: 'img/FillAnimateStraightPipe.png',
                },
                connectivity=(Tile.TOP, Tile.BOTTOM),
                orientations=(Tile.VERTICAL, Tile.HORIZONTAL),
                volume=128.0,
                frequency=1.0,
            ),
            Tile(
                name='corner',
                img='img/CornerPipe.png',
                fills={
                    Tile.TOP: 'img/FillAnimateStraightPipe.png',
                    Tile.LEFT: 'img/FillAnimateStraightPipe.png',
                },
                connectivity=(Tile.TOP, Tile.LEFT),
                orientations=(Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT),
                volume=128.0,
                frequency=2.0,
            ),
            Tile(
                name='tee',
                img='img/TeePipe.png',
                fills={
                    Tile.TOP: 'img/FillAnimateStraightPipe.png',
                    Tile.LEFT: 'img/FillAnimateStraightPipe.png',
                    Tile.RIGHT: 'img/FillAnimateStraightPipe.png',
                },
                connectivity=(Tile.TOP, Tile.LEFT, Tile.RIGHT),
                orientations=(Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT),
                volume=128.0,
                frequency=0.25,
            ),
            Tile(
                name='end',
                img='img/EndPipe.png',
                fills={
                    Tile.TOP: 'img/FillAnimateEndPipe.png',
                },
                connectivity=(Tile.TOP,),
                orientations=(Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT),
                volume=69.0,
                frequency=0.25,
            ),
            Tile(
                name='cross',
                img='img/CrossPipe.png',
                fills={
                    Tile.TOP: 'img/FillAnimateStraightPipe.png',
                    Tile.LEFT: 'img/FillAnimateStraightPipe.png',
                    Tile.RIGHT: 'img/FillAnimateStraightPipe.png',
                    Tile.BOTTOM: 'img/FillAnimateStraightPipe.png',
                },
                connectivity=(Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT),
                orientations=(Tile.TOP,),
                volume=128.0,
                frequency=0.05,
            ),
        ]

        self.surf = pygame.Surface((width * TILESIZE, height * TILESIZE),
                                   flags=pygame.SRCALPHA)

        tiles = [[self.random_tile()
                  for y in range(height)] for x in range(width)]
        self.cells = [[Cell(tiles[x][y],
                            random.choice(tiles[x][y].orientations),
                            pygame.Rect((x * TILESIZE, y * TILESIZE),
                                        (TILESIZE, TILESIZE)),
                            self, x, y)
                       for y in range(height)] for x in range(width)]
        while not self.cells[2][0].connected(Tile.TOP):
            tile = self.random_tile()
            self.cells[2][0] = Cell(tile,
                                    random.choice(tile.orientations),
                                    pygame.Rect((2 * TILESIZE, 0 * TILESIZE),
                                                (TILESIZE, TILESIZE)),
                                    self, 2, 0)
        self.width = width
        self.height = height
        self.failed = False

    def random_tile(self):
        total = sum(t.frequency for t in self.tileset)
        r = random.uniform(0, total)
        for t in self.tileset:
            r -= t.frequency
            if r <= 0:
                return t

    def draw(self, surface, rect):
        for c in itertools.chain(*self.cells):
            c.draw(self.surf)
        surface.blit(self.surf, rect)

    def get_from(self, cell, direction):
        if direction == Tile.TOP:
            if cell.y - 1 >= 0:
                return Tile.BOTTOM, self.cells[cell.x][cell.y - 1]
            else:
                return None, None
        elif direction == Tile.BOTTOM:
            if cell.y + 1 < self.height:
                return Tile.TOP, self.cells[cell.x][cell.y + 1]
            else:
                return None, None
        elif direction == Tile.LEFT:
            if cell.x - 1 >= 0:
                return Tile.RIGHT, self.cells[cell.x - 1][cell.y]
            else:
                return None, None
        elif direction == Tile.RIGHT:
            if cell.x + 1 < self.width:
                return Tile.LEFT, self.cells[cell.x + 1][cell.y]
            else:
                return None, None
