import pygame

from helpers.settings import *


class Transition:
    """class for the transition when player goes to sleep"""

    def __init__(self, reset, player) -> None:
        self.display_surface = pygame.display.get_surface()
        self.reset = reset
        self.player = player

        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.color = 255
        self.speed = -2

    def play(self, dt):
        """play the transition

        Args:
            dt: delta time
        """
        self.color += self.speed

        if self.color <= 0:
            self.color = 0
            self.speed = 2
            self.reset()
        elif self.color >= 255:
            self.color = 255
            self.player.sleep = False
            self.speed = -2

        self.image.fill((self.color, self.color, self.color))
        self.display_surface.blit(
            self.image, (0, 0), special_flags=pygame.BLEND_RGBA_MULT
        )
