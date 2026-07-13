import pygame as pyg
import pymunk
import pymunk.pygame_util as pgut
import math
import glob, os, random

from pygame.math import Vector2     #pygame.math.Vector2() is too long

pyg.init()

#getting display size to set the position of window when creating a screen surface
display_info = pyg.display.Info()
display_size = Vector2(display_info.current_w, display_info.current_h)
def set_window_pos(surf):
    global display_info, display_size
    surf_size = Vector2(surf.get_size())
    display_pos = tuple((display_size - surf_size)/2)
    pyg.display.set_window_position(display_pos)


#the menu of the game, currently only has title and start button to start the simulation of pymunk
def menu():
    pyg.font.init()
    #title
    title_font_name = pyg.font.match_font('comic sans')     #i like comic sans
    title_font = pyg.font.Font(title_font_name, size = 50)  #big font
    title_text = "BONK.PYGM"    #bonk.py 'g'ame+'m'unk      #kinda looks like just pygame in short lol
    title = title_font.render(title_text, False, "black")

    #button rect
    start_button_rect = pyg.Rect(0, 0, 100, 30)
    #button text
    start_button_font = pyg.font.Font(title_font_name, size = 30)
    start_button = start_button_font.render(" start ", False, "black")
    start_button_rect = start_button.get_rect(center = start_button_rect.center)
 
    screen = pyg.display.set_mode((640, 480))   #the screen res for all
    set_window_pos(screen)  #moving window to the middle of the monitor
    clock = pyg.time.Clock
    run = 1     #RUN
    scr_size = Vector2(screen.get_size())   #too lazy to type screen.get_width() and screen.get_height() every time

    while run:      #actual loop
        mouse_pos = pyg.mouse.get_pos()
        click = False   #getting mouse click

        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                run = 0
                return "quit"
            '''
            if event.type == pyg.VIDEORESIZE:
                w, h = event.dict['size'][0], event.dict['size'][1]
                if w/4 <= h/3:
                    w, h = w, w/4 * 3
                else:
                    w, h = h/3 * 4, h
                    screen = pyg.display.set_mode(
                        (w, h), flags = pyg.RESIZABLE
                        )
                scr_size = Vector2(screen.get_size())
                '''     #this is for the game window
            if event.type == pyg.MOUSEBUTTONDOWN and event.button == 1:
                click = True


        screen.fill("grey")

        #title and buttons
        title_pos = ((scr_size.x - title.get_width())/2, 125)
        screen.blit(title, title_pos)

        if start_button_rect.collidepoint(mouse_pos):
            pyg.draw.rect(screen, (220, 220, 220), start_button_rect)
            if click:
                game()
                break

        else:
            pyg.draw.rect(screen, (170, 170, 170), start_button_rect)
           

        start_button_rect.center = scr_size/2
        screen.blit(start_button, start_button_rect)
        
        pyg.display.flip()


def game():
    screen = pyg.display.set_mode((1280, 720))  #the superior scren res
    set_window_pos(screen)  #centering window
    scr_size = Vector2(screen.get_size())   #i should global this

    run = 1     #RUN

    clock = pyg.time.Clock()
    dt = 0

    pgut.positive_y_is_up = True
    space = pymunk.Space()
    space.gravity = (0, -200)
    space.collision_bias = 0

    global global_movement
    global_movement = Vector2()     #not implemented currently

    #player and map
    pos_reset(space)

    while run:
        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                run = 0
            if event.type == pyg.VIDEORESIZE:
                w, h = event.dict['size'][0], event.dict['size'][1]
                if w/16 <= h/9:
                    w, h = w, w/16 * 9
                else:
                    w, h = h/9 * 16, h
                    screen = pyg.display.set_mode(
                        (w, h), flags = pyg.RESIZABLE
                        )
                scr_size = Vector2(screen.get_size())

            
        if pyg.display.get_active():
            dt = clock.tick(60) / 1000
            if dt < 0.1:
                space.step(dt)

            screen.fill("white")
            for rect in Rect.group:
                rect.cycle(screen, dt)
            for player in Player.group:
                player.cycle(screen, space, dt)

            if global_movement:
                for rect in Rect.group:
                    rect.body.position += global_movement * dt
                for player in Player.group:
                    player.body.position += global_movement * dt

            #fps
            fps(screen, dt)

            pyg.display.flip()

#define pos_reset
def pos_reset(space):
    import shutil
    global players, rects, map_display_name, map_display_timer
    import pygame

    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    players = {}
    rects = {}
    Player.group.clear()
    Rect.group.clear()
    Player.death_count = 0
    
    if not glob.glob(f"{dir_path}/maps/*.txt"):
        if glob.glob(f"{dir_path}/maps/Used/*.txt"):
            for map_file in glob.glob(f"{dir_path}/maps/Used/*.txt"):
                shutil.move(map_file, f"{dir_path}/maps")
        else:
            raise FileNotFoundError("no map or folder existing")

    map_files = glob.glob(f"{dir_path}/maps/*.txt")
    map_c = random.choice(map_files)

    # Extract the map name and set up the 2-second display timer
    map_display_name = os.path.splitext(os.path.basename(map_c))[0]
    map_display_timer = pyg.time.get_ticks() + 2000

    bonk_map = []
    with open(map_c, "r", encoding="utf-8") as f:
        for line in f:
            if "\\" in line:
                break
            bonk_map.append(line)

    exec("".join(bonk_map))

    for p in Player.group:
        space.add(p.shape, p.body)
    for r in Rect.group:
        space.add(r.shape, r.body)

    shutil.move(map_c, f"{dir_path}/maps/Used")

    
def fps(surf, dt):
    font = pyg.font.Font(None, 30)
    framepersec = round((1/dt), 2)
    if framepersec >= 50:
        color = "green"
    elif framepersec >= 30:
        color = "yellow"
    else:
        color = "red" 
    fps_surf = font.render(f"FPS:{framepersec}", False, color)
    surf.blit(fps_surf)


class Player:
    group = []
    id_group = {}
    score = {}
    death_count = 0

    def __init__(self, pid, pos_x, pos_y, col,
                 kleft, kright, kjump, kfall, kheavy,
                 radius = 20):
        
        self.pid = pid
        self.col = col

        self.body = pymunk.Body(radius, 1)
        self.body.position = (pos_x, pos_y)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.parent_object = self
        self.shape.friction = 0
        self.shape.collision_type = 2    #COLLTYPE_BALL
        self.shape.elasticity = 0.7
        self.shape.data = self
        self.pos = self.body.position

        self.kleft = kleft
        self.kright = kright
        self.kjump = kjump
        self.kfall = kfall
        self.kheavy = kheavy

        self.onground = 1
        self.coyote_time = 5   #frames
        self.alive = 1

        Player.group.append(self)
        if pid not in Player.score:
            Player.score[pid] = 0

    def render(self, surf):
        y_condition = self.body.position.y < surf.get_height() + self.shape.radius
        x_condition = -self.shape.radius < self.body.position.x < self.shape.radius + surf.get_width()
        if y_condition and x_condition:
            render_pos = pgut.to_pygame(self.shape.body.position, surf)
            pyg.draw.circle(surf, self.col, render_pos, self.shape.radius)
        else:
            shadow_pos = (
                max(15, min(self.body.position.x, surf.get_width()- 15)),
                max(15, min(self.body.position.y, surf.get_height() - 15))
            )
            bar_vector = Vector2(Vector2(shadow_pos)- self.body.position).normalize()
            render_pos = pgut.to_pygame(shadow_pos, surf)
            pyg.draw.circle(surf, "black", render_pos, 10, 2)
            bar_render_pos_1 = pgut.to_pygame(shadow_pos, surf)
            bar_render_pos_2 = pgut.to_pygame(shadow_pos - bar_vector * 8, surf)
            pyg.draw.line(surf, self.col, bar_render_pos_1, bar_render_pos_2, 2)

    def move(self, dt):
        keys = pyg.key.get_pressed()
        if keys[self.kjump]:
            if self.onground > 0:
                self.body.apply_impulse_at_local_point((0, 3000 - self.body.velocity.y * self.body.mass))
                self.onground = 0
            if self.onground <= 0:
                self.body.velocity_func = Player.lower_gravity
        elif keys[self.kfall]:
            self.body.velocity_func = Player.higher_gravity
        else:
            self.body.velocity_func = Player.normal_gravity
        
        if keys[self.kleft]:
            self.body.apply_impulse_at_local_point((-90, 0))
        if keys[self.kright]:
            self.body.apply_impulse_at_local_point((90, 0))
            
        if 0 < self.onground < self.coyote_time:
            self.onground -= dt * 60

    def cycle(self, surf, space, dt):
        self.jump(space, dt)
        self.move(dt)
        self.render(surf)

    def jump(self, space, dt):
        def pre_solve(arbiter, space, data):
            for shape in arbiter.shapes:
                if type(shape) == pymunk.Circle:
                    circle = shape
                elif type(shape) == pymunk.Poly:
                    rect = shape
            test_points = arbiter.contact_point_set.points[0]

            if rect.data.bouncy == False and rect.data.death == False:
                c = circle.body.position
                p = test_points.point_a
                if c.y > p.y and abs(c.x - p.x) < circle.radius / 3 * 2:
                    circle.data.onground = circle.data.coyote_time    #coyote time
            return True
        
        def separate(arbiter, space, data):
            for shape in arbiter.shapes:
                if type(shape) == pymunk.Circle:
                    circle = shape
                elif type(shape) == pymunk.Poly:
                    rect = shape
            circle.data.onground -= dt * 60
            return True
        
        space.on_collision(0, 2, pre_solve=pre_solve, separate=separate, data=self)

    def normal_gravity(body, gravity, damping, dt):
        jump_gravity = (0, -250)
        pymunk.Body.update_velocity(body, jump_gravity, damping, dt)

    def lower_gravity(body, gravity, damping, dt):
        jump_gravity = (0, -110)
        pymunk.Body.update_velocity(body, jump_gravity, damping, dt)

    def higher_gravity(body, gravity, damping, dt):
        jump_gravity = (0, -350)
        pymunk.Body.update_velocity(body, jump_gravity, damping, dt)


class Rect:
    group = []
    def __init__(self, col, center, width, height,
                 facing = 0, bouncy = False, rotation = False, movement = False, death = False):
        self.width = width
        self.height = height
        self.facing = facing
        self.color = pyg.Color(col)
        self.bouncy = bouncy
        if type(self.bouncy) == int:
            self.bouncy *= 0.7     #faithful to original game
        self.do_update = rotation or movement
        self.rotating = rotation    #rotation = (orb_center, orb_vel, rot_vel)
        self.moving = movement    #movement = ((x, y)'min', (x, y)'max', (x,y)'vector')
        self.death = death

        self.body = pymunk.Body(body_type = pymunk.Body.KINEMATIC)
        self.shape = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.shape.data = self
        self.shape.collision_type = 0
        self.shape.body.position = tuple(center)
        self.shape.body.angle = -math.radians(facing)
        self.shape.friction = 1
        if self.bouncy:
            self.shape.elasticity = self.bouncy

        if self.do_update:
            if self.rotating:
                if not self.rotating[0]:
                    self.orb_center = self.shape.body.position
                else:
                    self.orb_center = self.rotating[0]
                self.orb_speed = self.rotating[1]
                self.rot_speed = self.rotating[2]
                self.vel = Vector2(0,0) #orb_vel
                self.defalut_vector_length = Vector2(
                    center - self.orb_center
                    ).length()

            if self.moving:
                self.min_pos = Vector2(self.moving[0])
                self.max_pos = Vector2(self.moving[1])
                self.speed = Vector2(self.moving[2])    #move_vel
                
        Rect.group.append(self)

    def render(self, surf):
        self.position = pgut.to_pygame(self.shape.body.position, surf)
        points = self.shape.get_vertices()
        world_points = []
        for point in points:
            world_point = self.shape.body.local_to_world(point)
            world_points.append(pgut.to_pygame(world_point, surf))
        pyg.draw.polygon(surf, self.color, world_points)

    def cycle(self, surf, dt):
        self.update(dt)
        self.render(surf)

    def rotation(self, dt):
        #orbiting
        if self.rotating[0] and self.rotating[1]:
            direction = Vector2(
                self.shape.body.position - self.orb_center
                ).normalize()
            length = Vector2(self.shape.body.position - self.orb_center
                ).length()
            interpolation = self.defalut_vector_length - length
            length += interpolation
            direction.rotate_ip(90)
            self.body.velocity = tuple(direction * length * -self.orb_speed)
        #rotating
        self.body.angular_velocity = self.rot_speed
           

    def movement(self, dt):
        #movement
        if self.min_pos.x > self.shape.body.position.x:
            self.speed.x = abs(self.speed.x)
        elif self.max_pos.x < self.shape.body.position.x:
            self.speed.x = -abs(self.speed.x)
        if self.min_pos.y > self.shape.body.position.y:
            self.speed.y = abs(self.speed.y)
        elif self.max_pos.y < self.shape.body.position.y:
            self.speed.y = -abs(self.speed.y)
        
        #apply speed!
        def speed_set(body, gravity, damping, dt):
            self.body.velocity = tuple(self.speed)
        self.body.velocity_func = speed_set
        
    def update(self, dt):
        if self.do_update:
            if self.rotating:
                self.rotation(dt)
            if self.moving:
                self.movement(dt)


class Line:
    def init(self, col, pos1, pos2, width=10,
             facing = 0, bouncy = False, rotation = False, movement = False, death = False):
        self.center = (pos1+pos2) / 2
        self.facing = (Vector2(pos1)-Vector2(pos2)).angle
        self.color = pyg.Color(col)
        self.bouncy = bouncy
        if type(self.bouncy) == int:
            self.bouncy *= 0.7     #faithful to original game
        self.do_update = rotation or movement
        self.rotating = rotation    #rotation = (orb_center, orb_vel, rot_vel)
        self.moving = movement    #movement = ((x, y)'min', (x, y)'max', (x,y)'vector')
        self.death = death

        self.body = pymunk.Body(body_type = pymunk.Body.KINEMATIC)
        self.shape = pymunk.Poly.create_box(self.body, (self.width, self.height))
        self.shape.data = self
        self.shape.collision_type = 0
        self.shape.body.position = tuple(self.center)
        self.shape.body.angle = -math.radians(facing)
        self.shape.friction = 1
        if self.bouncy:
            self.shape.elasticity = self.bouncy

        if self.do_update:
            if self.rotating:
                if not self.rotating[0]:
                    self.orb_center = self.shape.body.position
                else:
                    self.orb_center = self.rotating[0]
                self.orb_speed = self.rotating[1]
                self.rot_speed = self.rotating[2]
                self.vel = Vector2(0,0) #orb_vel

            if self.moving:
                self.min_pos = Vector2(self.moving[0])
                self.max_pos = Vector2(self.moving[1])
                self.speed = Vector2(self.moving[2])    #move_vel
                
        Rect.group.append(self)

    def render(self, surf):
        self.position = pgut.to_pygame(self.shape.body.position, surf)
        points = self.shape.get_vertices()
        world_points = []
        for point in points:
            world_point = self.shape.body.local_to_world(point)
            world_points.append(pgut.to_pygame(world_point, surf))
        pyg.draw.polygon(surf, self.color, world_points)

    def cycle(self, surf, dt):
        self.update(dt)
        self.render(surf)

    def rotation(self, dt):
        #orbiting
        if self.rotating[0] and self.rotating[1]:
            direction = Vector2(
                self.shape.body.position - self.orb_center
                ).normalize()
            length = Vector2(self.shape.body.position - self.orb_center
                ).length()
            direction.rotate_ip(90)
            self.body.velocity = tuple(direction * length * -self.orb_speed)
        #rotating
        self.body.angular_velocity = self.rot_speed
           

    def movement(self, dt):
        #movement
        if self.min_pos.x > self.shape.body.position.x:
            self.speed.x = abs(self.speed.x)
        elif self.max_pos.x < self.shape.body.position.x:
            self.speed.x = -abs(self.speed.x)
        if self.min_pos.y > self.shape.body.position.y:
            self.speed.y = abs(self.speed.y)
        elif self.max_pos.y < self.shape.body.position.y:
            self.speed.y = -abs(self.speed.y)
        
        #apply speed!
        def speed_set(body, gravity, damping, dt):
            self.body.velocity = tuple(self.speed)
        self.body.velocity_func = speed_set
        
    def update(self, dt):
        if self.do_update:
            if self.moving:
                self.movement(dt)
            if self.rotating:
                self.rotation(dt)



while menu() != 'quit':
    pass

pyg.quit()
