# Example file showing a basic pygame "game loop"
import pygame
import math

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
scroll_y = 0.0
scroll_target = 0.0
scroll_speed = 60

def target(screen, x, y, size, rings=5, colors=((235, 235, 235), (220, 50, 50))):
    radius = size / 2
    center = (x + radius, y + radius)
    for i in range(rings):
        r = radius * (rings - i) / rings
        pygame.draw.circle(screen, colors[i % 2], center, r)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEWHEEL:
            scroll_target -= event.y * scroll_speed
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                scroll_target += scroll_speed
            elif event.key == pygame.K_UP:
                scroll_target -= scroll_speed

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")
    screen.fill((0, 0, 0))
    sizes = [140 + i * 30 for i in range(5)]
    gap = 45
    top_margin = 20
    content_height = top_margin + sum(sizes) + gap * (len(sizes) - 1)
    max_scroll = max(0, content_height - screen.get_height())
    scroll_target = max(0, min(scroll_target, max_scroll))
    dt = clock.get_time() / 1000
    scroll_y += (scroll_target - scroll_y) * (1 - math.exp(-12 * dt))

    y = top_margin - scroll_y
    for size in sizes:
        target(screen, (screen.get_width() - size) / 2, y, size=size)
        y += size + gap
    # RENDER YOUR GAME HERE

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()