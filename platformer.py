import sys, os
import random
import math
import getopt
import pygame
from socket import *
from pygame.locals import *


##Game attributes
SCREEN_WIDTH    = 714
SCREEN_HEIGHT   = 260
SCREEN_RECT     = Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
MOVE_SPEED      = 3
GROUND_HEIGHT   = 15
ALIVE = True
# dictionary method for pressing multiple keys


##Resource Functions
def load_image(file, colorkey=None):
    "loads an image, prepares it for play"
    file = os.path.join('data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s'%(file, pygame.get_error()))

    if colorkey is not None:
        if colorkey is -1:
            colorkey = surface.get_at((0,0))
        surface.set_colorkey(colorkey, RLEACCEL)

    return surface.convert()

def load_images(colorkey=None, *files):
    imgs = []
    for file in files:
        imgs.append(load_image(file))
        if colorkey is not None:
            if colorkey is -1:
                colorkey = file.get_at((0, 0))
            file.set_colorkey(colorkey, RLEACCEL)
    return imgs


class dummysound:
    def play(self): pass

def load_sound(file):
    if not pygame.mixer: return dummysound()
    file = os.path.join('data', file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print ('Warning, unable to load, %s' % file)
    return dummysound()


#Game Objects
class Player (pygame.sprite.Sprite):
    """A sprite that is moved by the player in a platformer-style

    """

    def __init__(self, (x,y), x_vel, y_vel):
        pygame.sprite.Sprite.__init__(self)
        self.image = load_image('mario_run.png', -1)
        self.rect = self.image.get_rect(midleft=(x,y))
        self.x_vel = x_vel
        self.y_vel = y_vel
        self.state = "ground"
        self.right = False
        self.left = False
        self.up = False

        # List of sprites we can bump against
        self.level = None

    def check_collision(self, rect):
        self.rect = rect

        # check for collision
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            # If we are moving right,
            # set our right side to the left side of the item we hit
            if self.x_vel > 0 and self.rect.bottom > block.rect.top + 3:
                self.rect.right = block.rect.left

            if self.x_vel < 0 and self.rect.bottom > block.rect.top + 3:
                self.rect.left = block.rect.right

            if self.y_vel < 0:
                self.rect.top = block.rect.bottom

            if self.y_vel > 0:
                print("in y_vel collision")
                self.rect.bottom = block.rect.top
                self.y_vel = 0

    def update(self, keystate):
        #gravity
        self.calc_grav()

        #left/right/up movement
        if keystate[K_UP] == 1:
            self.up = True

        if self.up:
            self.y_vel = -1

        if keystate[K_LEFT] == 1:
            self.left = True

        if self.left:
            self.x_vel = -1

        if keystate[K_RIGHT] == 1:
            self.right = True

        if self.right:
            self.x_vel = 1

        newpos = self.calcnewpos(self.rect, self.x_vel, self.y_vel)
        self.rect = newpos

        self.check_collision(self.rect)



    def calcnewpos(self, rect, x_vel, y_vel):
        x_vel = x_vel * MOVE_SPEED
        y_vel = y_vel * MOVE_SPEED
        return rect.move(x_vel, y_vel)


    def alive(self):
        return True

    def stop(self, event_key):
        if event_key == pygame.K_LEFT:
            self.x_vel = 0
            self.left = False
        if event_key == pygame.K_RIGHT:
            self.x_vel = 0
            self.right = False
        if event_key == pygame.K_UP:
            self.up = False


    def calc_grav(self):
        """ Calculate effect of gravity. """
        if self.y_vel == 0:
            self.y_vel = 1
        else:
            self.y_vel += .35
        print("in calc grav", self.y_vel)

         #See if we are on the ground. NEED TO UPDATE USING GROUND COLLISION
        if self.rect.y >= SCREEN_HEIGHT - GROUND_HEIGHT - self.rect.height and self.y_vel > 0:
            print("in calc grav IF")
            self.y_vel = 0
            self.rect.y = SCREEN_HEIGHT - self.rect.height - GROUND_HEIGHT


class Block(pygame.sprite.Sprite):
    """An object that gets in the way of the player"""

    def __init__(self, x, y,image):
        pygame.sprite.Sprite.__init__(self)

        self.image = load_image(image, -1)

        self.rect = self.image.get_rect(midleft=(x,y))

class Ground(pygame.sprite.Sprite):
    """The floor"""

    def __init__(self, x, y,width,height,surface):
        pygame.sprite.Sprite.__init__(self)
        self.image = surface

        self.rect = self.image.get_rect(topleft=(x,y))

class Level(object):
    """ This is a generic super-class used to define a level.
        Create a child class for each level with level-specific
        info. """

    def __init__(self, player):
        """ Constructor. Pass in a handle to player. Needed for when moving platforms
            collide with the player. """
        self.platform_list = pygame.sprite.Group()
       #self.enemy_list = pygame.sprite.Group()
        self.player = player

        # Background image
        self.background = None

    # Update everythign on this level
    def update(self):
        """ Update everything in this level."""
        self.platform_list.update()
        #self.enemy_list.update()

    def draw(self, screen):
        """ Draw everything on this level. """

        # Draw the background
        #screen.fill(BLUE)

        # Draw all the sprite lists that we have
        self.platform_list.draw(screen)
        #self.enemy_list.draw(screen)

class Level_01(Level):
    """ Definition for level 1. """

    def __init__(self, player):
        """ Create level 1. """

        # Call the parent constructor
        Level.__init__(self, player)

        # Array with x, and y of platform
        level = [[300,230],
                 [400,240],
                 [420,220],
                 [440,200],
                 [660,160]]

        #x,y, width height
        ground = [[-10,SCREEN_HEIGHT - GROUND_HEIGHT,SCREEN_WIDTH+20,GROUND_HEIGHT]]

        # Go through the array above and add platforms
        for platform in level:
            block = Block(platform[0], platform[1],'brick_block.png')
            block.player = self.player #??
            self.platform_list.add(block)



        for g in ground:
            self.surface = pygame.Surface((g[2], g[3]))
            self.surface.fill((139, 69, 19))
            floor = Ground(g[0],g[1],g[2],g[3],self.surface)
            floor.player = self.player
            self.platform_list.add(floor)

#Main Loop function
def main():
    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((714, 260))
    pygame.display.set_caption("Scott's Platformer")

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background = load_image("mario_bg.jpg")

    # Display some text
    font = pygame.font.Font(None, 36)
    text = font.render("Run!", 1, (10, 10, 10))
    textpos = text.get_rect()
    textpos.centerx = background.get_rect().centerx
    background.blit(text, textpos)

    #Initialize player
    global player
    player = Player((1,230),0,0)
    ALIVE = True


    # Create all the levels
    level_list = []
    level_list.append(Level_01(player))
    # Set the current level
    current_level_no = 0
    current_level = level_list[current_level_no]

    #Initialize sprites
    #playersprite = pygame.sprite.RenderPlain(player)
    #blocksprite = pygame.sprite.RenderPlain(block)
    player.level = current_level
    active_sprite_list = pygame.sprite.Group()
    active_sprite_list.add(player)



    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    #allow for keys to be held
    pygame.key.set_repeat(50,30)



    # Event loop
    while ALIVE:

        for event in pygame.event.get():
            #print event
            if event.type == QUIT:
                ALIVE = False

            if event.type == pygame.KEYDOWN:
                keystate = pygame.key.get_pressed()

                # handle player input
                player.update(keystate)

            if event.type == pygame.KEYUP:
                player.stop(event.key)

        if player.left or player.right or player.up == True:
            keystate = pygame.key.get_pressed()
            player.update(keystate)

        #check if player is in the air and use gravity to force a fall without any other key input
        if player.rect.y < SCREEN_HEIGHT - GROUND_HEIGHT - player.rect.height:
            player.calc_grav()
            newpos = player.calcnewpos(player.rect,player.x_vel,player.y_vel)
            player.rect = newpos
            player.check_collision(player.rect)

        # If the player gets near the right side, shift the world left (-x)
        if player.rect.right > SCREEN_WIDTH:
            player.rect.x = SCREEN_WIDTH - player.rect.width

        # If the player gets near the left side, shift the world right (+x)
        if player.rect.left < 0:
            player.rect.left = 0

        screen.blit(background, (0, 0))
        screen.blit(background,player.rect, player.rect)

        ##playersprite.update()
        current_level.update()
        #active_sprite_list.update()
        #playersprite.draw(screen)
        #blocksprite.draw(screen)
        current_level.draw(screen)
        active_sprite_list.draw(screen)

        #don't draw below this comment

        # Limit to 60 frames per second
        clock.tick(30)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__': main()