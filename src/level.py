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
        self.dirty = True

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
            self.dirty = False

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
            src = (source - self.orientation) % 4
            anim_len = len(self.tile.fills[src][self.orientation])
            if self.animation[source] <= anim_len and amount - overflow > 0.0:
                self.dirty = True
            self.animation[source] += amount - overflow
            return overflow
        else:
            self.fill[source] += amount
            self.animation[source] += amount
            self.dirty = True
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

        self.surf = pygame.Surface((width * TILESIZE, 2 * height * TILESIZE),
                                   flags=pygame.SRCALPHA)

        tiles = [[self.random_tile()
                  for x in range(width)] for y in range(2 * height)]
        self.cells = [[Cell(tiles[y][x],
                            random.choice(tiles[y][x].orientations),
                            pygame.Rect((x * TILESIZE, y * TILESIZE),
                                        (TILESIZE, TILESIZE)),
                            self, x, y)
                       for x in range(width)] for y in range(2 * height)]
        while (not self.cells[0][2].connected(Tile.TOP)
                or len(self.cells[0][2].tile.connectivity) <= 1):
            tile = self.random_tile()
            self.cells[0][2] = Cell(tile,
                                    random.choice(tile.orientations),
                                    pygame.Rect((2 * TILESIZE, 0 * TILESIZE),
                                                (TILESIZE, TILESIZE)),
                                    self, 2, 0)
        self.width = width
        self.height = height
        self.failed = False
        self.screenrect = pygame.Rect((0, 0),
                                      (width * TILESIZE, height * TILESIZE))
        self.rect = self.screenrect.copy()
        self.scroll = 0.0
        self.mouseselect = None
        self.mouseselectold = None
        self.mouseframe = resources.load_png('img/SelectorPanel.png')
        self.rate = 0.0
        self.growth = 1.0

    def random_tile(self):
        total = sum(t.frequency for t in self.tileset)
        r = random.uniform(0, total)
        for t in self.tileset:
            r -= t.frequency
            if r <= 0:
                return t

    def draw(self, surface):
        if self.mouseselectold != self.mouseselect:
            if self.mouseselectold is not None:
                self.mouseselectold.dirty = True
            if self.mouseselect is not None:
                self.mouseselect.dirty = True
            self.mouseselectold = self.mouseselect
        for c in itertools.chain(*self.cells[-2 * self.height:]):
            if c.dirty:
                c.draw(self.surf)
        if self.mouseselect is not None:
            self.surf.blit(self.mouseframe, self.mouseselect.rect)
        surface.blit(self.surf, self.screenrect, self.rect)

    def click(self, pos, button):
        if button == 1:
            if self.screenrect.collidepoint(pos):
                pos = tuple(
                    p - o + r for p, o, r in
                    zip(pos, self.screenrect.topleft, self.rect.topleft)
                )
                for c in itertools.chain(*self.cells):
                    if c.rect.collidepoint(pos) and max(c.fill) == 0.0:
                        if self.mouseselect is None:
                            self.mouseselect = c
                        elif self.mouseselect == c:
                            self.mouseselect = None
                        else:
                            if max(self.mouseselect.fill) == 0.0:
                                x = self.mouseselect.x
                                y = self.mouseselect.y
                                rect = self.mouseselect.rect
                                self.cells[y][x] = c
                                self.cells[c.y][c.x] = self.mouseselect
                                self.mouseselect.rect = c.rect
                                self.mouseselect.x = c.x
                                self.mouseselect.y = c.y
                                self.mouseselect.dirty = True
                                c.rect = rect
                                c.x = x
                                c.y = y
                                c.dirty = True
                            self.mouseselect = None
                        break
        elif button == 3:
            self.mouseselect = None

    def update(self, dt):
        flow = (self.rate + dt * self.growth / 2.0) * dt
        self.scroll += dt * (self.rate + dt * self.growth / 2.0) / 4.0
        if self.scroll > self.rect.height:
            for row in self.cells[-self.height:]:
                for cell in row:
                    cell.rect.top -= self.height * TILESIZE
                    cell.dirty = True
            tiles = [[self.random_tile()
                      for x in range(self.width)]
                     for dy in range(self.height)]
            self.cells = (self.cells +
                          [[Cell(tiles[dy][x],
                                 random.choice(tiles[dy][x].orientations),
                                 pygame.Rect((x * TILESIZE,
                                              (self.height + dy) * TILESIZE),
                                             (TILESIZE, TILESIZE)),
                                 self, x, len(self.cells) + dy)
                            for x in range(self.width)]
                           for dy in range(self.height)])
            self.scroll -= self.rect.height
        self.rect.top = self.scroll
        self.rate += self.growth * dt
        if self.cells[0][2].flow(Tile.TOP, flow) > 0.0:
           self.failed = True
        if self.mouseselect is not None and max(self.mouseselect.fill) > 0.0:
            self.mouseselect = None

    def get_from(self, cell, direction):
        if direction == Tile.TOP:
            if cell.y - 1 >= 0:
                return Tile.BOTTOM, self.cells[cell.y - 1][cell.x]
            else:
                return None, None
        elif direction == Tile.BOTTOM:
            if cell.y + 1 < len(self.cells):
                return Tile.TOP, self.cells[cell.y + 1][cell.x]
            else:
                return None, None
        elif direction == Tile.LEFT:
            if cell.x - 1 >= 0:
                return Tile.RIGHT, self.cells[cell.y][cell.x - 1]
            else:
                return None, None
        elif direction == Tile.RIGHT:
            if cell.x + 1 < self.width:
                return Tile.LEFT, self.cells[cell.y][cell.x + 1]
            else:
                return None, None
