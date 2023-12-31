import os

import pygame

from helpers.settings import *
from helpers.support import *
from helpers.timer import Timer


class Player(pygame.sprite.Sprite):
    def __init__(
        self,
        pos,
        group,
        collision_sprites,
        tree_sprites,
        interaction_sprites,
        soil_layer,
        toggle_shop,
    ):
        super().__init__(group)

        # animation attrs
        self.import_assets()
        self.status = "down_idle"
        self.frame_index = 0

        # general setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.copy().inflate(-126, -70)
        self.z = LAYERS["main"]
        self.sleep = False

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 600

        # additional sprites to be aware of
        self.collision_sprites = collision_sprites
        self.tree_sprites = tree_sprites
        self.soil_layer = soil_layer
        self.interaction = interaction_sprites

        # timers (cooldowns)
        self.timers = {
            "tool use": Timer(350, self.use_tool),
            "tool switch": Timer(300),
            "seed use": Timer(350, self.use_seed),
            "seed switch": Timer(300),
        }

        # tools
        self.tools = ["hoe", "water", "axe"]
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]

        # seeds
        self.seeds = ["corn", "tomato"]
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]

        # inventory
        self.item_inventory = {
            "wood": 3,
            "apple": 3,
            "corn": 3,
            "tomato": 3,
        }

        self.seed_inventory = {
            "corn": 5,
            "tomato": 5,
        }

        # shop
        self.toggle_shop = toggle_shop
        self.money = 200

    def use_tool(self):
        """Use selected tool"""
        if self.selected_tool == "hoe":
            self.soil_layer.get_hit(self.target_pos)
        elif self.selected_tool == "water":
            self.soil_layer.water(self.target_pos)
        elif self.selected_tool == "axe":
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()

    def get_target_pos(self):
        """get the position of the used tool"""
        self.target_pos = (
            self.rect.center + PLAYER_TOOL_OFFSET[self.status.split("_")[0]]
        )

    def use_seed(self):
        """Use selected seed"""
        if self.seed_inventory[self.selected_seed] > 0:
            self.seed_inventory[self.selected_seed] -= 1
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed)

    def import_assets(self):
        """import all assets for the player"""
        self.animations = {}

        for animation in os.listdir("../graphics/character"):
            full_path = "../graphics/character/" + animation
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        """animate the player

        Args:
            dt: delta time
        """
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]

    def movement(self, keys):
        """move the player in the direction of the pressed key

        Args:
            keys: pressed keys
        """
        if keys[pygame.K_UP]:
            self.direction.y = -1
            self.status = "up"
        elif keys[pygame.K_DOWN]:
            self.direction.y = 1
            self.status = "down"
        else:
            self.direction.y = 0

        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.status = "right"
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.status = "left"
        else:
            self.direction.x = 0

    def actions(self, keys):
        """make the player do some actions

        Args:
            keys: the pressed keys
        """
        # tool actions
        if keys[pygame.K_SPACE]:
            self.timers["tool use"].activate()
            self.direction = pygame.math.Vector2()
            self.frame_index = 0

        if keys[pygame.K_q] and not self.timers["tool switch"].active:
            self.timers["tool switch"].activate()
            self.tool_index += 1
            if self.tool_index == len(self.tools):
                self.tool_index = 0
            self.selected_tool = self.tools[self.tool_index]

        # seed actions
        if keys[pygame.K_LCTRL]:
            self.timers["seed use"].activate()
            self.direction = pygame.math.Vector2()
            self.frame_index = 0

        if keys[pygame.K_e] and not self.timers["seed switch"].active:
            self.timers["seed switch"].activate()
            self.seed_index += 1
            if self.seed_index == len(self.seeds):
                self.seed_index = 0
            self.selected_seed = self.seeds[self.seed_index]

        # interactions
        if keys[pygame.K_RETURN]:
            collided_interaction_sprites = pygame.sprite.spritecollide(
                self, self.interaction, False
            )
            if collided_interaction_sprites:
                name = collided_interaction_sprites[0].name
                if name == "Trader":
                    self.toggle_shop()
                else:
                    self.status = "left_idle"
                    self.sleep = True

    def input(self):
        """parse the input of the player"""
        keys = pygame.key.get_pressed()

        if (
            not self.timers["tool use"].active and not self.sleep
        ):  # player is not moving with the tool
            self.movement(keys)
            self.actions(keys)

    def get_status(self):
        """get the status of the player, can be idle or using a tool, important for displaying the right animation"""
        # idle
        if self.direction.magnitude() == 0:
            self.status = self.status.split("_")[0] + "_idle"

        # tool use
        if self.timers["tool use"].active:
            self.status = self.status.split("_")[0] + "_" + self.selected_tool

    def update_timers(self):
        """update all the various cooldowns (timers)"""
        for timer in self.timers.values():
            timer.update()

    def x_collision(self, sprite):
        """determine collision in the x direction, and eliminate any weird teleporting around the sprite

        Args:
            sprite: sprite to check collision with
        """
        if self.direction.x > 0:
            self.hitbox.right = sprite.hitbox.left
            self.rect.right = self.hitbox.right
        elif self.direction.x < 0:
            self.hitbox.left = sprite.hitbox.right
            self.rect.left = self.hitbox.left
        self.rect.centerx = self.hitbox.centerx
        self.pos.x = self.hitbox.centerx

    def y_collision(self, sprite):
        """determine collision in the y direction, and eliminate any weird teleporting around the sprite

        Args:
            sprite: sprite to check collision with
        """
        if self.direction.y > 0:
            self.hitbox.bottom = sprite.hitbox.top
            self.rect.bottom = self.hitbox.bottom
        elif self.direction.y < 0:
            self.hitbox.top = sprite.hitbox.bottom
            self.rect.top = self.hitbox.top
        self.rect.centery = self.hitbox.centery
        self.pos.y = self.hitbox.centery

    def collision(self, direction):
        """detect collision with other sprites

        Args:
            direction: direction of the possible collision
        """
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, "hitbox"):
                if self.hitbox.colliderect(sprite.hitbox):
                    if direction == "horizontal":
                        self.x_collision(sprite)
                    if direction == "vertical":
                        self.y_collision(sprite)

    def move_x(self, dt):
        """move the player in the x direction

        Args:
            dt: delta time
        """
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision("horizontal")

    def move_y(self, dt):
        """move the player in the y direction

        Args:
            dt: delta time
        """
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision("vertical")

    def move(self, dt):
        """move the player in the direction of the pressed key"""
        # normalizing a vector
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        self.move_x(dt)
        self.move_y(dt)

    def update(self, dt):
        """update the player in time

        Args:
            dt: delta time
        """
        self.input()
        self.get_status()
        self.update_timers()
        self.get_target_pos()
        self.move(dt)
        self.animate(dt)
        # print(self.item_inventory)
