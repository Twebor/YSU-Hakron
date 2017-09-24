import os
import sys
import random
import itertools
# look into subprocess for opening new window and pipe output.  Look into eztext perhaps for some text input.
# import subprocess
# import eztext
import pygame as pg

CAPTION = "YSU Hackron Project"
SCREEN_SIZE = (750, 750)
BACKGROUND_COLOR = (118, 118, 118)
COLOR_KEY = (25, 25,25)

DIRECT_DICT = {pg.K_LEFT: (-1, 0),
               pg.K_RIGHT: (1, 0),
               pg.K_UP: (0, -1),
               pg.K_DOWN: (0, 1)}


class Player(pg.sprite.Sprite):
    SIZE = (50, 50)

    def __init__(self, pos, speed, facing=pg.K_DOWN, *groups, battleCounter = 0):
        super(Player, self).__init__(*groups)
        self.speed = speed
        self.direction = facing
        self.old_direction = None  # previous direction every frame
        self.direction_stack = []  # held keys in the order pressed.
        self.redraw = True  # force redraw if needed.
        self.animate_timer = 0.0
        self.animate_fps = 7
        self.image = None
        self.walkframes = None
        self.walkframe_dict = self.make_frame_dict()
        self.adjust_images()
        self.rect = self.image.get_rect(center=pos)
        self.steps = 0.0
        self.battleCounter = battleCounter

    def make_frame_dict(self):
        frames = split_sheet(PLAYER_IMAGE, Player.SIZE, 4, 1)[0]
        flips = [pg.transform.flip(frame, True, False) for frame in frames]
        walk_cycles = {pg.K_LEFT : itertools.cycle(frames[0:2]),
                       pg.K_RIGHT: itertools.cycle(flips[0:2]),
                       pg.K_DOWN : itertools.cycle([frames[3], flips[3]]),
                       pg.K_UP   : itertools.cycle([frames[2], flips[2]])}
        return walk_cycles

    def adjust_images(self, now=0):
        """
        Update the sprite's walkframes as the direction changes
        """
        if self.direction != self.old_direction:
            self.walkframes = self.walkframe_dict[self.direction]
            self.old_direction = self.direction
            self.redraw = True
        self.make_image(now)

    def make_image(self, now):
        """
        Update the sprite's animation as needed
        """
        elapsed = now - self.animate_timer > 1000.0 / self.animate_fps
        if self.redraw or (self.direction_stack and elapsed):
            self.image = next(self.walkframes)
            self.animate_timer = now
        self.redraw = False

    def add_direction(self, key):
        """
        Add a pressed direction on the direction stack
        """
        if key in DIRECT_DICT:
            if key in self.direction_stack:
                self.direction_stack.remove(key)
            self.direction_stack.append(key)
            self.direction = self.direction_stack[-1]

    def pop_direction(self, key):
        """
        Pop a released key from the direction stack
        """
        if key in DIRECT_DICT:
            if key in self.direction_stack:
                self.direction_stack.remove(key)
            if self.direction_stack:
                self.direction = self.direction_stack[-1]

    def get_event(self, event):
        """
        Handle events pertaining to player control
        """
        if event.type == pg.KEYDOWN:
            self.add_direction(event.key)
        elif event.type == pg.KEYUP:
            self.pop_direction(event.key)

    def update(self, now, obstacles):
        self.adjust_images(now)
        if self.direction_stack:
            self.movement(obstacles, 0)
            self.movement(obstacles, 1)

    def movement(self, obstacles, i):
        """Move player and then check for collisions"""
        direction_vector = DIRECT_DICT[self.direction]
        self.rect[i] += self.speed * direction_vector[i]
        collision = pg.sprite.spritecollideany(self, obstacles)
        self.steps += 1 # each step increments very quickly
        if self.steps > 1 and self.steps % 300 == 0:
            print(self.steps)
            # os.system("xterm -e 'python test.py'") # works to open completely separate terminal on linux
        while collision:
            self.adjust_on_collision(collision, i)
            collision = pg.sprite.spritecollideany(self, obstacles)
        self.battleCounter += 1
        if self.battleCounter == 100:
            result = random.randint(0, 100)
            if result >= 90:
                print("Trigger battle")
                self.battleCounter = 0
        elif self.battleCounter == 200:
            result = random.randint(0, 100)
            if result >= 80:
                self.battleCounter = 0
        elif self.battleCounter == 300:
            result = random.randint(0, 100)
            if result >= 70:
                print("Trigger battle.")
                self.battleCounter = 0
        elif self.battleCounter == 400:
            result = random.randint(0, 100)
            if result >= 50:
                print("Trigger battle.")
                self.battleCounter = 0
        elif self.battleCounter == 500:
            result = random.randint(0, 100)
            if result >= 0:
                print("Trigger battle.")
                self.battleCounter = 0

    def adjust_on_collision(self, collide, i):
        """
        Adjust a player's position if colliding with a solid block
        """
        if self.rect[i] < collide.rect[i]:
            self.rect[i] = collide.rect[i] - self.rect.size[i]
        else:
            self.rect[i] = collide.rect[i] + collide.rect.size[i]

    def draw(self, surface):
        """Draw sprite to surface (not used if group drawing functions)"""
        surface.blit(self.image, self.rect)


class Block(pg.sprite.Sprite):
    """
    Obstacles for player to collide with
    """

    def __init__(self, pos, *groups, collidable=True):
        super(Block, self).__init__(*groups)
        self.image = self.make_image()
        self.rect = self.image.get_rect(topleft=pos)
        self.collidable = collidable

    def make_image(self):
        fill_color = [random.randint(0, 255) for _ in range(3)]
        image = pg.Surface((50, 50)).convert_alpha()
        image.fill(fill_color)
        image.blit(SHADE_MASK, (0, 0))
        return image


class Control(object):
    """
    Window information and main loop
    """

    def __init__(self):
        """Initialize standard attributes standardly"""
        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.clock = pg.time.Clock()
        self.fps = 60
        self.done = False
        self.keys = pg.key.get_pressed()
        self.player = Player(self.screen_rect.center, 3)
        self.blocks = self.make_blocks()
        self.all_sprites = pg.sprite.Group(self.player, self.blocks)

    def make_blocks(self):
        """
        Create some blocks for collision
        """
        blocks = pg.sprite.Group()
        for pos in [(400, 400), (300, 270), (150, 170)]:
            Block(pos, blocks)
        for i in range(int(SCREEN_SIZE[0] / 50)):
            Block((i * 50, 0), blocks) # Top
            Block((SCREEN_SIZE[0] - 50, 50 * i), blocks) # Right
            if not i == int(SCREEN_SIZE[0] / 50) - 1:
                Block((50 + i * 50, SCREEN_SIZE[1] - 50), blocks) # Bottom
            Block((0, 50 + 50 * i), blocks) # Left
        return blocks

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or self.keys[pg.K_ESCAPE]:
                self.done = True
            elif event.type in (pg.KEYUP, pg.KEYDOWN):
                self.keys = pg.key.get_pressed()
            self.player.get_event(event)

    def display_fps(self):
        caption = "{} - FPS: {:.2f}".format(CAPTION, self.clock.get_fps())
        pg.display.set_caption(caption)

    def update(self):
        """
        Update the player.
        The current time is passed for animation purposes.
        """
        now = pg.time.get_ticks()
        self.player.update(now, self.blocks)

    def render(self):
        """
        Perform all necessary updating and drawing to the screen
        """
        self.screen.fill(BACKGROUND_COLOR)
        # largeText = pg.font.Font('freesansbold.ttf', 115)
        # TextSurf, TextRect = text_objects("MESSAGE TO DISPLAY", largeText)
        # TextRect.center = ((SCREEN_SIZE[0] / 2), (SCREEN_SIZE[1] / 2))
        # self.screen.blit(TextSurf, TextRect)
        self.all_sprites.draw(self.screen)
        pg.display.update()
        pg.display.flip()

    def main_loop(self):
        delta = self.clock.tick(self.fps) / 1000.0
        while not self.done:
            self.event_loop()
            self.render()
            self.update()
            delta = self.clock.tick(self.fps) / 1000.0
            self.display_fps()

def text_objects(text, font):
    textSurface = font.render(text, True, (255, 255, 255))
    return textSurface, textSurface.get_rect()


def split_sheet(sheet, size, columns, rows):
    """
    Divide a loaded sprite sheet into subsurfaces.

    The argument size is the width and height of each frame (w,h)
    columns and rows are the integer number of cells horizontally and
    vertically.
    """
    subsurfaces = []
    for y in range(rows):
        row = []
        for x in range(columns):
            rect = pg.Rect((x * size[0], y * size[1]), size)
            row.append(sheet.subsurface(rect))
        subsurfaces.append(row)
    return subsurfaces

def main():
    global PLAYER_IMAGE, SHADE_MASK
    extra_screen = 50 * 8
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pg.init()
    pg.display.set_caption(CAPTION)
    pg.display.set_mode((SCREEN_SIZE[0] + extra_screen, SCREEN_SIZE[1]))
    PLAYER_IMAGE = pg.image.load("./assets/png/player.png").convert()
    PLAYER_IMAGE.set_colorkey(COLOR_KEY)
    SHADE_MASK = pg.image.load("./assets/png/shader.png")
    Control().main_loop()
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
