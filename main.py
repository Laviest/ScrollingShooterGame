import random
import pygame
from pygame import mixer
from pygame.locals import *
from random import randint
import math
from sys import path
import time
from itertools import cycle

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 30

screen_width = 1400
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Shooter')

## Define game variables ##
ground_scroll = 0
scroll_speed = 6
game_over = 0
score = 0
lives = 3
main_menu = True
bscore = 1
screen_shake = 0
show = 0
i=1
time_to_blit = None

box_frequency = 4000 # milliseconds
platform_frequency = 1500
brownbird_frequency = 2000
whitebird_frequency = 6300
rocket_frequency = 8000
meteor_frequency = 9000

last_box = pygame.time.get_ticks() - box_frequency
last_platform = pygame.time.get_ticks() - platform_frequency
last_brownbird = pygame.time.get_ticks() - brownbird_frequency
last_whitebird = pygame.time.get_ticks() - whitebird_frequency
last_rocket = pygame.time.get_ticks() - rocket_frequency
last_meteor = pygame.time.get_ticks() - meteor_frequency

## Sounds ##
explosion_fx = pygame.mixer.Sound('sounds/explosion.wav')
gameover_fx = pygame.mixer.Sound('sounds/gameover.wav')
gameover_fx.set_volume(1.5)
jump_fx = pygame.mixer.Sound('sounds/jump.wav')
jump_fx.set_volume(0.2)
laugh_fx = pygame.mixer.Sound('sounds/laugh.mp3')
meteor_fx = pygame.mixer.Sound('sounds/meteor.wav')
bullet_fx = pygame.mixer.Sound('sounds/bullet.mp3')
bullet_fx.set_volume(1.2)
bird_fx = pygame.mixer.Sound('sounds/bird.wav')

pygame.mixer.music.load('sounds/music.wav')
pygame.mixer.music.play(-1, 0.0, 10000)


## Define font ##
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)

## Load images ##
bg_img = pygame.image.load('img/sky1.png')

deadbg_img = pygame.image.load('img/sky2.png')
ground_img = pygame.image.load('img/ground.png')
deadground_img = pygame.image.load('img/ground1.png')
bullet_img = pygame.image.load('img/bullet.png')
start_img = pygame.image.load('img/start.png')
reset_img = pygame.image.load('img/reset.png')
exit_img = pygame.image.load('img/exit.png')
skull_img = pygame.image.load('img/skull.png')
rect = skull_img.get_rect()
grect = ground_img.get_rect()
drect = deadground_img.get_rect()

# Define colours
white = (255, 255, 255)
blue = (0, 0, 255)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))



class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False

        ## Get mouse position ##
        pos = pygame.mouse.get_pos()

        ## Check mouseover and clicked conditions ##
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        ## Draw button ##
        screen.blit(self.image, self.rect)

        return action

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images_right = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'player/R{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            self.images_right.append(img_right)
        self.image = self.images_right[self.index]
        self.dead_image = pygame.image.load('img/ghost.png')
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.rect.y = y
        self.rect.x = x
        self.vel_y = 0
        self.jumped = False
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.in_air = True

    def update(self, game_over):
        dx = 0
        dy = 0
        col_thresh = 10

        if game_over == 0:
            ## Get key pressed ##
            key = pygame.key.get_pressed()
            if key[pygame.K_UP] and self.jumped == False and self.in_air == False:
                self.vel_y = -15
                self.jumped = True
                jump_fx.play()
            if key[pygame.K_UP] == False:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 8
                self.counter += 1
            if key[pygame.K_RIGHT]:
                dx += 8
                self.counter += 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0

            ## Gravity ##
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            if self.rect.y <= 554:
                self.in_air = True
            else:
                self.in_air = False

            ## Animations ##
            walk_cooldown = 3
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
            self.image = self.images_right[self.index]

            ## Collision for rockets ##
            for rocket in rocket_group:
                col_thresh = 5
                ## Collision in the y direction ##
                if rocket.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    explosion = Explosion(rocket.rect.x, rocket.rect.y)
                    explosion_group.add(explosion)
                    rocket.kill()
                    explosion_fx.play()
                    game_over = -1

                if rocket.rect.colliderect(self.rect.x, self.rect.y + dy + 1, self.width, self.height):
                    if abs((self.rect.bottom + dy) - rocket.rect.top) < col_thresh:
                        game_over = -1
                        explosion = Explosion(rocket.rect.x, rocket.rect.y)
                        explosion_group.add(explosion)
                        rocket.kill()
                        explosion_fx.play()

            for meteor in meteor_group:
                if meteor.rect.colliderect(self.rect.x, self.rect.y, self.width, self.height):
                    explosion = Explosion(meteor.rect.x, meteor.rect.y)
                    explosion_group.add(explosion)
                    meteor.kill()
                    meteor_fx.play()
                    game_over = -1

                if meteor.rect.colliderect(self.rect.x, self.rect.y, self.width, self.height):
                    if abs((self.rect.bottom + dy) - meteor.rect.top) < col_thresh:
                        explosion = Explosion(meteor.rect.x, meteor.rect.y)
                        explosion_group.add(explosion)
                        meteor.kill()
                        meteor_fx.play()
                        game_over = -1

            ## Collision for boxes ##
            for box in box_group:
                ## Collision in the y direction ##
                if box.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    ## Check if above platform ##
                    col_thresh = 20
                    if abs((self.rect.bottom + dy) - box.rect.top) < col_thresh:
                        self.rect.bottom = box.rect.top - 1
                        self.in_air = False
                        dy = 0

                ## Collision in the x direction ##
                if box.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0

                ## Check for collision with platforms ##
                for platform in platform_group:
                    ## Collision in the x direction ##
                    if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                        dx = 0
                    ## Collision in the y direction ##
                    if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                        ## Check if below platform ##
                        if abs((self.rect.top + dy) - platform.rect.bottom) < 10:
                            self.vel_y = 0
                            dy = platform.rect.bottom - self.rect.top
                        ## Check if above platform ##
                        elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                            self.rect.bottom = platform.rect.top - 1
                            self.in_air = False
                            dy = 0

                    if platform.rect.y >= (screen_height // 2 + 50):
                        platform.rect.y = 400


            ## Player bounderies ##
            if player.rect.x < 0:
                game_over = -1
                if game_over == -1:
                    gameover_fx.play()

            if player.rect.x > 1360:
                game_over = -1
                if game_over == -1:
                    gameover_fx.play()


            if player.rect.bottom >= 625:
                player.rect.bottom = 625


            ## Update player coordinates ##
            self.rect.x += dx
            if time_now / 1000 < 30:
                self.rect.x -= 3
            else:
                self.rect.x -= 4
            self.rect.y += dy



        return game_over


class Box(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/box.png')
        self.rect = self.image.get_rect()
        self.rect.topleft = [x, y]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        if time_now / 1000 > 30:
            self.image = pygame.image.load('img/platforms/platform1.png')
        if time_now / 1000 < 30:
            self.image = pygame.image.load('img/platforms/platform.png')
        self.image = pygame.transform.scale(self.image, (97, 22))
        self.rect = self.image.get_rect()
        self.rect.topleft = [x, y]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()


class BrownBird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 6):
            img = pygame.image.load(f'bird/brownbird/bird{num}.png')
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()

        ## Animations ##
        walk_cooldown = 5
        self.counter += 1

        if self.counter > walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
        self.image = self.images[self.index]


class WhiteBird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 6):
            img = pygame.image.load(f'bird/whitebird/bird{num}.png')
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.x -= scroll_speed + 3
        if self.rect.right < 0:
            self.kill()

        ## Animations ##
        walk_cooldown = 5
        self.counter += 1

        if self.counter > walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
        self.image = self.images[self.index]


class Rocket(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img = pygame.image.load(f'img/rocket/rocket{num}.png')
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.rect.x -= scroll_speed + 3
        if self.rect.right < 0:
            self.kill()

        ## Animations ##
        walk_cooldown = 1
        self.counter += 1

        if self.counter > walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
        self.image = self.images[self.index]



class Gun(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/gunn.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x = player.rect.x + 15
        self.rect.y = player.rect.y + 15


        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x, rel_y = mouse_x - self.rect.x, mouse_y - self.rect.y
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x)
        if angle >= 60:
            angle = 60

        if angle <= -10:
            angle = -10
        rot_image = pygame.transform.rotate(self.image, int(angle))
        rot_image_rect = rot_image.get_rect(center=self.rect.center)
        screen.blit(rot_image, rot_image_rect.topleft)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 13):
            img = pygame.image.load(f'img/explosion/explosion{num}.png')
            img = pygame.transform.scale(img, (100, 100))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        explosion_speed = 1
        ## Update explosion animation ##
        self.counter += 1

        if self.counter >= explosion_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]

        ## If the animation is complete, reset animation index ##
        if self.index >= len(self.images) - 1 and self.counter >= explosion_speed:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(f'img/meteor/meteor{num}.png')
            img = pygame.transform.scale(img, (128, 128))
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.rect.y += scroll_speed + 8
        if self.rect.top > 800:
            self.kill()

        if self.rect.y == screen_height - 215:
            explosion = Explosion(meteor.rect.x, meteor.rect.y)
            explosion_group.add(explosion)
            meteor.kill()
            meteor_fx.set_volume(0.5)
            meteor_fx.play()

        ## Animations ##
        walk_cooldown = 1
        self.counter += 1

        if self.counter > walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
        self.image = self.images[self.index]


player_group = pygame.sprite.Group()
box_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
gun_group = pygame.sprite.Group()
brownbird_group = pygame.sprite.Group()
whitebird_group = pygame.sprite.Group()
rocket_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
meteor_group = pygame.sprite.Group()


player = Player(300, screen_height - 245)
gun = Gun(player.rect.x + 25, player.rect.y + 25)
player_group.add(player)
gun_group.add(gun)

start = pygame.math.Vector2(player.rect.center)
length = 50
bullets = []
SPEED = 50

clicked = False
laugh = True
play = False
meteor = True

## Create buttons ##
# restart_button = Button(screen_width // 2 - 100, screen_height // 2 + 100, reset_img)
start_button = Button(screen_width // 2, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 - 300, screen_height // 2, exit_img)

start_time = pygame.time.get_ticks()
startTime = time.time()

finalTime = 0
testTime = 0

run = True
while run:


    clock.tick(fps)
    showSkull = True
    time_now = pygame.time.get_ticks() + 10
    if screen_shake > 0:
        screen_shake -= 1

    render_offset = [0, 0]
    if screen_shake:
        render_offset[0] = random.randint(0, 8) - 4
        render_offset[1] = random.randint(0, 8) - 4

    ## Sky background ##
    if time_now / 1000 < 30:
        screen.blit(bg_img, render_offset)
        screen.blit(ground_img, (ground_scroll, render_offset[1]))

    if time_now / 1000 > 30:
        if meteor:
            # meteor_fx.play()
            meteor = False
        scroll_speed = 8
        deadbg_img.set_alpha(i)
        deadground_img.set_alpha(i)
        screen.blit(deadbg_img, render_offset)
        screen.blit(deadground_img, (ground_scroll, render_offset[1]))

    if main_menu:
        if start_button.draw():
            main_menu = False
        if exit_button.draw():
            run = False
    else:
        if game_over == 0:

            if testTime % 40 == 0:
                finalTime += 1

            testTime += 1

            # counting_time = pygame.time.get_ticks() - start_time
            realtime = str(int(time.time() - startTime))
            player_group.update(0)
            gun_group.update()
            brownbird_group.update()
            whitebird_group.update()
            rocket_group.update()
            explosion_group.update()
            meteor_group.update()

            if time_now / 1000 > 30:
                i += 5
                if i == 255:
                    i = 5
                skull_img.set_alpha(i)
                if i < 255:
                    if laugh == True:
                        laugh_fx.play()
                        laugh = False
                    screen.blit(skull_img, (500, 100))
                    screen_shake = 5

            draw_text('X ' + str(score), font_score, white, 0 + 10, 10)
            draw_text('lives ' + str(lives), font_score, white, 1400 - 70, 10)
            draw_text('Time ' + str(finalTime), font_score, white, screen_width // 2, 10)

            ## Generate new everything ##
            if time_now - last_box > box_frequency:
                box = Box(screen_width, screen_height - 215)
                box_group.add(box)
                last_box = time_now
            if time_now - last_platform > platform_frequency:
                platform_height = random.randint(-100, 100)
                platform1 = Platform(screen_width, (screen_height // 2) + platform_height)
                platform_group.add(platform1)
                last_platform = time_now
            if time_now - last_brownbird > brownbird_frequency:
                brownbird_height = random.randint(-300, -130)
                brownbird1 = BrownBird(screen_width, (screen_height // 2) + brownbird_height)
                brownbird_group.add(brownbird1)
                last_brownbird = time_now
            if time_now - last_whitebird > whitebird_frequency:
                whitebird_height = random.randint(-300, -130)
                whitebird1 = WhiteBird(screen_width, (screen_height // 2) + whitebird_height)
                whitebird_group.add(whitebird1)
                last_whitebird = time_now
            if time_now - last_box > box_frequency:
                rocket = Rocket(screen_width, screen_height - 215)
                box_group.add(rocket)
                last_box = time_now
            if time_now // 1000 > 15:
                if time_now - last_rocket > rocket_frequency - 10:
                    rocket = Rocket(screen_width, screen_height - 200)
                    rocket_group.add(rocket)
                    last_rocket = time_now
                if time_now // 1000 > 30:
                    scroll_speed = 7
            if time_now // 1000 > 40:
                if time_now - last_meteor > meteor_frequency:
                    meteor_pos = random.randint(300, 1000)
                    meteor = Meteor(meteor_pos, 0)
                    meteor_group.add(meteor)
                    last_meteor = time_now
            for meteor in meteor_group:
                if meteor.rect.colliderect(grect.x, grect.y + 680, grect.width, grect.height + 680):
                    explosion = Explosion(meteor.rect.centerx, meteor.rect.centery)
                    explosion_group.add(explosion)
                    meteor.kill()
                    meteor_fx.play()




            ## If mouse button is clicked ##
            if clicked:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                distance_x = mouse_x - (player.rect.x + 45)
                distance_y = mouse_y - (player.rect.y + 37)

                angle = math.atan2(distance_y, distance_x)
                if angle < -1.6:
                    angle = -1.6

                if angle > 1.6:
                    angle = 1.6

                speed_x = SPEED * math.cos(angle)
                speed_y = SPEED * math.sin(angle)

                if main_menu == False:
                        if len(bullets) < 1:
                            bullets.append([player.rect.x + 45, player.rect.y + 37, speed_x, speed_y])
                            bullet_fx.play()

                for item in bullets:
                    item[0] += item[2]
                    item[1] += item[3]

                for pos_x, pos_y, speed_x, speed_y in bullets:
                    pos_x = int(pos_x)
                    pos_y = int(pos_y)


                    pygame.draw.circle(screen, (0, 0, 0), (pos_x, pos_y), 3)

                    for bird in brownbird_group:
                        if bird.rect.colliderect((pos_x, pos_y, speed_x, speed_y)):
                            if bird.rect.centerx - pos_x < 5 or bird.rect.centery - pos_y < 5:
                                if len(bullets) > 0:
                                    bullets.pop(0)
                                clicked = False
                                bird.kill()
                                score += 1
                                bscore += 1
                                bird_fx.play()

                    if pos_y < 0 or pos_y > 800 or pos_x < 0 or pos_x > 1400:
                        if len(bullets) > 0:
                            bullets.pop(0)
                            clicked = False


                    for birdd in whitebird_group:
                        if birdd.rect.colliderect((pos_x, pos_y, speed_x, speed_y)):
                            if birdd.rect.x - pos_x < 5:
                                if len(bullets) > 0:
                                    bullets.pop(0)
                                clicked = False
                                birdd.kill()
                                score += 3
                                bscore += 3
                                bird_fx.play()

                    if bscore >= 10:
                        bscore = 0
                        lives += 1


                    for platform in platform_group:
                        ## Collision in the x direction ##
                        if platform.rect.colliderect(pos_x, pos_y, speed_x, speed_y):
                            if len(bullets) > 0:
                                bullets.pop(0)
                            clicked = False

                    for box in box_group:
                        ## Collision in the x direction ##
                        if box.rect.colliderect(pos_x, pos_y, speed_x, speed_y):
                            if len(bullets) > 0:
                                bullets.pop(0)
                            clicked = False


            ## Scrolling ground ##
            ground_scroll -= scroll_speed
            if abs(ground_scroll) > 35:
                ground_scroll = 0

            box_group.update()
            platform_group.update()


            player_group.draw(screen)
            box_group.draw(screen)
            platform_group.draw(screen)
            brownbird_group.draw(screen)
            whitebird_group.draw(screen)
            rocket_group.draw(screen)
            explosion_group.draw(screen)
            meteor_group.draw(screen)

        game_over = player.update(game_over)

        ## If player dies ##
        if game_over == -1:
            if lives > 1:
                player_group.empty()
                player = Player(300, screen_height - 173)
                player_group.add(player)
                game_over = 0
                lives -= 1
                screen_shake = 15
                i=1
                laugh = True
            else:
                print("Your time was " + realtime)
                run = False
                # pygame.mixer.music.fadeout(1500)
                # box_group.empty()
                # brownbird_group.empty()
                # whitebird_group.empty()
                # platform_group.empty()
                # rocket_group.empty()
                # player_group.empty()
                # laugh = True
                # if play == False:
                #     gameover_fx.play()
                #     play = True
                # if restart_button.draw():
                #     finalTime = 0
                #     realtime = 0
                #     score = 0
                #     i=1
                #     pygame.mixer.music.load('sounds/music.wav')
                #     pygame.mixer.music.play(-1, 0.0, 5000)
                #     player = Player(300, screen_height - 173)
                #     player_group.add(player)
                #     lives = 3
                #     game_over = 0

                ### THE PART ABOVE DOESN'T WORK BECAUSE THE WHOLE GAME LOGIC HAS BEEN CODED AROUND THE GAME TICKS
                ### AND I CAN NOT RESET THEM WHEN THE PLAYER DIES, SO THE METEOR, THE RED BACKGROUND, THE SKULL,
                ### ALL OF THEM STAY, SO WHEN THE PLAYER DIES THE GAME JUST ENDS



    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            clicked = True


    pygame.display.update()

pygame.quit()