# Endless Pipes
# A pipe puzzle game for Adelaide Game Jam 5 "Flow"

import argparse
import cProfile
import collections

import pygame

import level


def main(resolution, fullscreen):
    # Initialise screen
    pygame.init()

    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    screen = pygame.display.set_mode(resolution, flags)
    pygame.display.set_caption("Endless Pipes")
    screenRect = screen.get_rect()

    font = pygame.font.SysFont("sans,arial", 30)

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((255, 255, 255))

    quit = False

    clock = pygame.time.Clock()
    time = 0.0
    frames = 0
    show_fps = False

    l = level.Level(5, 5)

    while not quit:
        dt = clock.tick(200) / 1000.0
        frames += 1
        time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit = True
                elif event.key == pygame.K_f:
                    show_fps = not show_fps
                    if show_fps:
                        frame_times = collections.deque(maxlen=50)

        overflow = l.cells[2][0].flow(level.Tile.TOP, dt * 16)
        print(overflow)
        if l.failed:
            print("You lasted {:0.1f} seconds!".format(time))
            quit = True

        screen.blit(background, (0, 0))
        l.draw(screen, (0, 0))
        if (show_fps):
            frame_times.append(dt)
            fps = len(frame_times) / sum(frame_times)
            widget = font.render("{:0.1f} FPS".format(fps), True, (0, 0, 0))
            fontrect = widget.get_rect()
            fontrect.topright = (screenRect.right - 10, screenRect.top + 10)
            screen.blit(widget, fontrect.topleft)
        pygame.display.flip()

    print("Rendered " + str(frames) + " frames in " + str(time)
          + " seconds (" + str(frames / time) + " FPS)")


def resolution(raw):
    a = raw.split("x")
    if len(a) != 2:
        raise ValueError()
    return (int(a[0]), int(a[1]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='A pipe puzzle game.')
    parser.add_argument('--profile-file', action='store',
                        help="File to store profiling output in")
    parser.add_argument('-p', '--profile', action='store_true',
                        help="Enable profiling using cProfile")
    parser.add_argument('-r', '--resolution', action='store',
                        type=resolution, default=(0, 0),
                        help="Target screen resolution (e.g. 1920x1080)")
    parser.add_argument('-f', '--fullscreen', action='store_true',
                        dest="fullscreen", default=True,
                        help="Run in full screen.")
    parser.add_argument('-w', '--windowed', action='store_false',
                        dest="fullscreen",
                        help="Run in window.")
    args = parser.parse_args()
    if args.profile:
        cProfile.run(
            "main(args.resolution, args.fullscreen)",
            filename=args.profile_file)
    else:
        main(args.resolution, args.fullscreen)
