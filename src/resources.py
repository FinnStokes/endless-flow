import pygame


class Cache(dict):
    def __init__(self, *args, **kwargs):
        super(Cache, self).__init__(*args, **kwargs)
        self.hits = 0
        self.misses = 0

    def __contains__(self, key):
        if super(Cache, self).__contains__(key):
            self.hits += 1
            return True
        else:
            self.misses += 1
            return False

    def get(self, key, default=None):
        if super(Cache, self).__contains__(key):
            self.hits += 1
        else:
            self.misses += 1
        super(Cache, self).get(key, default)

cache = Cache()


def load_png(name):
    """Load image and return surface"""
    key = ('png', name)
    if key in cache:
        return cache[key]

    image = pygame.image.load(name)
    if image.get_alpha() is None:
        image = image.convert()
    else:
        image = image.convert_alpha()

    cache[key] = image
    return image


def load_spritesheet(name, size, rotation=0):
    key = ('sprites', name, size, rotation)
    if key in cache:
        return cache[key]

    if rotation == 0:
        img = load_png(name)
        width, height = size
        xframes = img.get_width() / width
        yframes = img.get_height() / height
        sprites = [img.subsurface(pygame.Rect((x * width, y * height),
                                              (width, height)))
                   for x in range(xframes) for y in range(yframes)]
    else:
        sprites = [pygame.transform.rotate(s, rotation)
                   for s in load_spritesheet(name, size)]
    cache[key] = sprites
    return sprites
