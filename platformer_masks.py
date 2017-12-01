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
GROUND_HEIGHT   = 260
ALIVE = True

# Used to manage how fast the screen updates
clock = pygame.time.Clock()



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

def vadd(x, y):
    return [x[0] + y[0], x[1] + y[1]]

def vsub(x, y):
    return [x[0] - y[0], x[1] - y[1]]

def vdot(x, y):
    return x[0] * y[0] + x[1] * y[1]

def collision_normal(left_mask, right_mask, left_pos, right_pos):


    offset = map(int,vsub(left_pos,right_pos))

    overlap = left_mask.overlap_area(right_mask,offset)

    if overlap == 0:
        return None, overlap

    #Calculate normal collision parameters

    nx = (left_mask.overlap_area(right_mask,(offset[0]+1,offset[1])) -
          left_mask.overlap_area(right_mask,(offset[0]-1,offset[1])))
    ny = (left_mask.overlap_area(right_mask,(offset[0],offset[1]+1)) -
          left_mask.overlap_area(right_mask,(offset[0],offset[1]-1)))
    if nx == 0 and ny == 0:
        #One sprite is inside another
        return None, overlap

    n = [nx,ny]

    return n, overlap

#Game Classes and Methods
class Player(pygame.sprite.Sprite):
    def __init__(self, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([10,10])
        self.image.fill((0,0,0))
        self.mask = pygame.mask.from_surface(self.image,0)
        self.mask.fill()
        self.rect = self.image.get_rect()
        self.right = False
        self.left = False
        self.up = False
        self.down = False
        self.rect.topleft = location
        self.new_dr = [0, 0]

        self.setPos(location)
        self.vel = [0,0]

        #self.jumping = 0

    def setPos(self,pos):
        self.rect[0] = pos[0]
        self.rect[1] = pos[1]

    def setVelocity(self):
        self.checkMaxVel()
        if self.left == True:
            self.new_dr[0] = -1
            self.move(self.new_dr)
        if self.right == True:
            self.new_dr[0] = 1
            self.move(self.new_dr)
        if self.up == True:
            self.new_dr[1] = -1
            self.move(self.new_dr)
        if self.down == True:
            self.new_dr[1] += .35
            self.move(self.new_dr)



    def move(self,dr):
        pos = vadd(self.rect,dr)
        self.rect[0] = pos[0]
        self.rect[1] = pos[1]
        self.vel[0] = 0
        self.vel[1] = 0
        #print("moving:",pos, self.rect, dr)

    #def kick(self,impulse):
    #    self.move(impulse)


    def collide(self, s):

        offset = list(map(int, vsub(s.rect, self.rect)))
        print("offset:", offset)

        overlap = self.mask.overlap_area(s.mask, offset)

        if overlap == 0:
            return None, overlap

        #Calculate collision normal
        nx = (self.mask.overlap_area(s.mask, (offset[0] + 1, offset[1])) -
              self.mask.overlap_area(s.mask, (offset[0] , offset[1])))
        ny = (self.mask.overlap_area(s.mask, (offset[0], offset[1] + 1)) -
              self.mask.overlap_area(s.mask, (offset[0], offset[1])))
        #print(nx,ny)
        if nx == 0 and ny == 0:
            #One sprite is inside another
            return None, overlap

        n = [nx, ny]

        dv = vsub(s.vel, self.vel)
        J = vdot(dv, n) / (2 * vdot(n, n))
        #print("j:", J)
        if J > 0:
            #Collision bounce. J can go up to 2
            J *= .001
            #print("jkick:", nx,ny,j)
            self.move([nx * J, ny * J])
            s.move([-J * nx, -J * ny])
            return
        #print("overlap,n:", overlap, n)
        #Separate the sprites
        c1 = float(-overlap / vdot(n, n))
        c2 = float(-c1 / 2)
        #print("move:", c2, nx, c2, ny,)
        self.move([c2 * nx, c2 * ny])
        s.move([(c1 + c2) * nx, (c1 + c2) * ny])

    def checkMaxVel(self):
        #adjusts velocity (x,y) so it doesn't exceed max_vel
        max_vel = 1
        if self.vel[0] > max_vel:
            self.vel[0] = max_vel
        if self.vel[0] < -max_vel:
            self.vel[0] = -max_vel

        if self.new_dr[1] > max_vel:
            self.new_dr[1] = max_vel
        if self.vel[1] < -max_vel:
            self.vel[1] = -max_vel

    def gravity(self, s):

        if self.rect.y + 12 < GROUND_HEIGHT:
            self.down = True
            #print(self.down, self.rect[1], self.vel[1])
        else:
            self.down = False




class Block(pygame.sprite.Sprite):
    """An object that gets in the way of the player"""

    def __init__(self, x, y,image):
        pygame.sprite.Sprite.__init__(self)

        self.image = load_image(image, -1)

        self.rect = self.image.get_rect(midleft=(x,y))
        self.mask = pygame.mask.from_surface(self.image)
        self.mask.fill()
        self.vel = [0,0]

    def move(self,impulse):
        pass

    def collide(self,s):
        pass

class Terrain(pygame.sprite.Sprite):
    """An object that gets in the way of the player"""

    def __init__(self, x, y, width, height):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([width, height])
        self.image.fill((160, 82, 45))
        self.mask = pygame.mask.from_surface(self.image, 0)
        self.mask.fill()
        self.rect = self.image.get_rect(midleft=(x,y))
        self.mask = pygame.mask.from_surface(self.image)
        self.mask.fill()
        self.vel = [0,0]

    def move(self,impulse):
        pass

    def collide(self,s):
        pass

#Main Loop function
def main():
    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((714, 260))
    pygame.display.set_caption("Scott's Platformer")



    # Fill background
    background = pygame.Surface(screen.get_size())
    background.fill((135,206,235))



    #Initialize player
    player = Player((5,GROUND_HEIGHT-10))
    block = Block(50,GROUND_HEIGHT-10,"brick_block.png")
    ground = Terrain(-10, GROUND_HEIGHT, SCREEN_WIDTH+20, 5)


    #Initialize sprites
    all_sprites = pygame.sprite.RenderPlain(player)
    all_sprites.add(block,ground)
    moving_sprites = pygame.sprite.Group(player)
    non_moving_sprites = pygame.sprite.Group(block,ground)
    #sprites = all_sprites.sprites()
    #print(sprites)


    # allow for keys to be held
    pygame.key.set_repeat(50, 30)

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()
    ALIVE = True

    # Event loop
    while ALIVE:

        events = pygame.event.get()
        for event in events:

            if event.type == QUIT:
                ALIVE = False

            if event.type == pygame.KEYDOWN:
                player_rect = player.vel
                if event.key in [K_LEFT]:
                    player.left = True
                if event.key in [K_RIGHT]:
                    player.right = True
                if event.key in [K_UP]:
                    player.up = True

                #if event.key in [K_DOWN]:
                #    player.down = True

            if event.type == pygame.KEYUP:
                if event.key in [K_LEFT]:
                    player.left = False
                    player.new_dr[0] = 0
                if event.key in [K_RIGHT]:
                    player.right = False
                    player.new_dr[0] = 0
                if event.key in [K_UP]:
                    player.up = False
                    player.new_dr[1] = 0


        player.gravity(block)
        player.setVelocity()

        if 1:
            msprites = list(moving_sprites)
            nsprites = list(non_moving_sprites)
            for i in range(len(msprites)):
                for j in range(len(nsprites)):
                    msprites[i].collide(nsprites[j])


        #bounce sprites off walls
        for s in moving_sprites:
            s.setVelocity()
            if s.rect[0] < -s.image.get_width() - 5:
                s.rect[0] = 10
                s.vel[0] = 1
            elif s.rect[0] > screen.get_width() + 5:
                s.rect[0] = SCREEN_WIDTH-10
                s.vel[0] = -1
            if s.rect[1] < -s.image.get_height() - 5:
                s.rect[1] = 10
                s.vel[1] = 1
            elif s.rect[1] > screen.get_height():
                s.rect[1] = SCREEN_HEIGHT-10
                s.vel[1] = -1


        player_rect = player.rect
        player_mask = player.mask
        block_rect = block.rect
        block_mask = block.mask
        #size = player_mask.get_size(), block_mask.get_size()
        #print(size)

        bx, by = (player_rect[0], player_rect[1])
        #offset_x = bx - block_rect[0]
        #offset_y = by - block_rect[1]
        #print(offset_x, offset_y)

        # print bx, by
        #overlap = block_mask.overlap(player_mask,(0,0))
        #block_centroid = block_mask.centroid()
        #player_centroid = player_mask.centroid()
        #print(overlap, block_centroid, player_centroid)


        #
        last_bx, last_by = bx, by

        screen.blit(background, (0, 0))
        screen.blit(background,player.rect, player.rect)

        all_sprites.draw(screen)


        #don't draw below this comment

        # Limit to 30 frames per second
        clock.tick(60)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__': main()