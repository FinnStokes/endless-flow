import itertools
import math
import random

import pygame


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
        self.base_img = pygame.image.load(img)
        self.base_img.convert_alpha()

        def get_frames(img):
            width, height = self.base_img.get_size()
            img.convert_alpha()
            xframes = img.get_width() / width
            yframes = img.get_height() / height
            return [img.subsurface(pygame.Rect((x * width, y * height),
                                               (width, height)))
                    for x in range(xframes) for y in range(yframes)]

        self.base_fills = [get_frames(pygame.image.load(fill))
                           for fill in fills]
        self.img = [pygame.transform.rotate(self.base_img, 90 * o)
                    for o in (Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT)]
        self.fills = [[[pygame.transform.rotate(f, 90 * o) for f in fill]
                       for o in (Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT)]
                      for fill in self.base_fills]
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

    def draw(self, surface):
        surface.blit(self.tile.img[self.orientation], self.rect)
        if sum(self.fill) > 0.0:
            fills = self.tile.fills[Tile.TOP][self.orientation]
            # frames = len(fills)
            # frame = int(math.floor(frames * (1.0 - sum(self.fill)
            #                                  / self.tile.volume)))
            frame = max(0,
                        len(fills) - 1 - int(math.floor(sum(self.animation))))
            surface.blit(fills[frame], self.rect)

    def flow(self, source, amount):
        if not self.tile.connected(self.orientation, source):
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
                fills=('img/FillAnimateStraightPipe_vertical.png',),
                connectivity=(Tile.TOP, Tile.BOTTOM),
                orientations=(Tile.VERTICAL, Tile.HORIZONTAL),
                volume=128.0,
                frequency=1.0,
            ),
            Tile(
                name='corner',
                img='img/CornerPipe.png',
                fills=('img/FillAnimateStraightPipe_vertical.png',),
                connectivity=(Tile.TOP, Tile.LEFT),
                orientations=(Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT),
                volume=128.0,
                frequency=2.0,
            ),
            Tile(
                name='tee',
                img='img/TeePipe.png',
                fills=('img/FillAnimateStraightPipe_vertical.png',),
                connectivity=(Tile.TOP, Tile.LEFT, Tile.RIGHT),
                orientations=(Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT),
                volume=128.0,
                frequency=0.25,
            ),
            Tile(
                name='end',
                img='img/EndPipe.png',
                fills=('img/FillAnimateStraightPipe_vertical.png',),
                connectivity=(Tile.TOP,),
                orientations=(Tile.TOP, Tile.LEFT, Tile.BOTTOM, Tile.RIGHT),
                volume=128.0,
                frequency=0.25,
            ),
            Tile(
                name='cross',
                img='img/CrossPipe.png',
                fills=('img/FillAnimateStraightPipe_vertical.png',),
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
