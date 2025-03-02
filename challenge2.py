import pyglet as pg
from pyglet.gl import *
from pyglet.window import key
from pyglet import font
import numpy as np

font.add_file('font/KiwiSoda.ttf') # Custom font

# Initial game settings
bullet_limit = 30
player_health = 100
aliens_health = 30 # For use later if i get to creating levels
gravity = 300 # Gravitational pull

class GameWindow(pg.window.Window):
    def __init__(self):
        super().__init__(fullscreen=False, caption='Space Invaders (isj) Game')
        self.width = 900
        self.height = 600
        
        self.time = 0 # Time variable for use with interpolation functions
        
        self.background = Background()           # Initialize background
        self.player = Player()              # Initialize Player
        self.player_stats = Stats(0,player_health,bullet_limit)    # Player starts with: Score = 0, Health = player_health
        self.game_instructions = Instructions()
        
        # Create a handler for keypresses
        self.key_handler = key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        
        # Initialize the first platoon of aliens
        self.aliens = [Aliens(np.random.randint(100, 800), np.random.randint(350, 600)) for _ in range(12)]
        
        self.killer_alien = []
        self.explosions = []
        self.game_over = []


    # Create new explosion
    def createExplosion(self, x, y):
        explosion = Explosion(x, y)
        self.explosions.append(explosion)
    
    # Create new killer alien
    def createKillerAlien(self):
        killer_alien = KillerAlien(np.random.randint(100, 800), np.random.randint(450, 500))
        self.killer_alien.append(killer_alien)
        
    # Create new aliens
    def create_aliens(self):
        self.aliens = [Aliens(np.random.randint(100, 800), np.random.randint(350, 600)) for _ in range(12)]
        
    # Update Player Stats with new values
    def updatePlayerStats(self, score_change, health_change, bullet_change):
        self.player_stats = Stats(self.player_stats.score + score_change, self.player_stats.health + health_change, self.player_stats.bullets + bullet_change)
    
    # Show Game Over screen
    def gameOver(self, score):
        # Remove remaining aliens, cannonballs and explosions
        for alien in self.aliens:
            self.aliens.remove(alien)
        
        for cannonball in self.player.cannonballs:
            self.player.cannonballs.remove(cannonball)
            
        for explosion in self.explosions:
            self.explosions.remove(explosion)
            
        # Hide player
        self.player.sprite_cannon.opacity = 0
        self.player.sprite_base.opacity = 0
        # Show GameOver screen
        self.game_over.append(GameOver(score))

    # Handle keypress
    def on_key_press(self, symbol, modifiers):
        # Quit the game using the "q" key
        if (symbol == key.SPACE) and (self.player_stats.health > 0): # Shoot (placed here to retrict to one cannonball pr press)
            if self.player.bullets > 0:
                self.updatePlayerStats(0,0,-1)
                self.player.bullets -= 1
                self.player.shoot()
        elif symbol == key.Q:
            pg.app.exit()
        elif (symbol == key.R) and (self.player_stats.health > 0):   # Don't let the user restart in the middle of a game
            # TRIGGER RESTART OF GAME
            pass
    
    # Output elements to screen
    def on_draw(self):
        self.clear()  # Clear the window
        self.background.draw()
        
        self.player_stats.draw() # Ouput game stats
        self.game_instructions.draw() # Output game instructions
        
        self.player.draw() # Draw Player
        
        for alien in self.aliens: # Draw Aliens
            alien.draw()
        
        for killer_alien in self.killer_alien: # Draw Killer Alien
            killer_alien.draw()
        
        for explosion in self.explosions: # Draw Explosions
            explosion.draw()
        
        for gameover in self.game_over: # Ouput Game over screen
            gameover.draw()

    
    # Handle collisions between aliens
    # This function is a refactorization of the code used in an earlier assignment to suit this need
    def alien_alien_collision_handler(self, alien1, alien2):
        # Calculate distance between aliens
        dist_x = alien2.sprite.x - alien1.sprite.x
        dist_y = alien2.sprite.y - alien1.sprite.y
        distance = np.sqrt(dist_x**2+dist_y**2)
        
        # Handle collisions between aliens
        if distance < (alien1.radius + alien2.radius):
            
            # Calculate the normal vector
            vectnormal = [alien2.sprite.x - alien1.sprite.x, alien2.sprite.y - alien1.sprite.y]
            unitvectnormal = vectnormal / np.sqrt(vectnormal[0]**2 + vectnormal[1]**2)
            
            # Calculate the tangent vector
            unitvecttangent = [-unitvectnormal[1], unitvectnormal[0]]
            
            # "Vectorize" the velocities
            alien1vel = np.array((alien1.dx, alien1.dy))
            alien2vel = np.array((alien2.dx, alien2.dy))
            
            alien1velPREnorm = np.dot(alien1vel, unitvectnormal)
            alien1velPREtang = np.dot(alien1vel, unitvecttangent)
            alien2velPREnorm = np.dot(alien2vel, unitvectnormal)
            alien2velPREtang = np.dot(alien2vel, unitvecttangent)
            
            # One dimentional collision formulas
            alien1velPOSTnorm = (alien1velPREnorm*(alien1.mass-alien2.mass) + 2*alien2.mass*alien2velPREnorm)/(alien1.mass+alien2.mass)
            alien2velPOSTnorm = (alien2velPREnorm*(alien2.mass-alien1.mass) + 2*alien1.mass*alien1velPREnorm)/(alien1.mass+alien2.mass)
            alien1velPOSTtang = alien1velPREtang
            alien2velPOSTtang = alien2velPREtang
            
            alien1velPOSTnormvect = np.dot(alien1velPOSTnorm, unitvectnormal)
            alien2velPOSTnormvect = np.dot(alien2velPOSTnorm, unitvectnormal)
            alien1velPOSTtangvect = np.dot(alien1velPOSTtang, unitvecttangent)
            alien2velPOSTtangvect = np.dot(alien2velPOSTtang, unitvecttangent)
            
            alien1velPOST = alien1velPOSTnormvect + alien1velPOSTtangvect
            alien2velPOST = alien2velPOSTnormvect + alien2velPOSTtangvect
            
            alien1.dx = alien1velPOST[0]
            alien1.dy = alien1velPOST[1]
            alien2.dx = alien2velPOST[0]
            alien2.dy = alien2velPOST[1]
            
            # Calculate overlap
            overlap = (distance - (alien1.radius + alien2.radius)) /2
            
            # move objects out of collision
            alien1.sprite.x += overlap * (dist_x / distance)
            alien1.sprite.y += overlap * (dist_y / distance)
            alien2.sprite.x -= overlap * (dist_x / distance)
            alien2.sprite.y -= overlap * (dist_y / distance)
            
            
    # Handle collisions between cannonballs and aliens
    # This function is a refactorization of the code used in an earlier assignment to suit this need
    def cannonball_alien_collision_handler(self, cannonball, alien):
        # Calculate distance between cannonball and alien
        dist_x = cannonball.x - alien.sprite.x
        dist_y = cannonball.y - alien.sprite.y
        distance = np.sqrt(dist_x**2+dist_y**2)
        
        # Handle collisions
        if distance < (cannonball.radius + alien.radius):
            # Calculate the normal vector
            vectnormal = [alien.sprite.x - cannonball.x, alien.sprite.y - cannonball.y]
            unitvectnormal = vectnormal / np.sqrt(vectnormal[0]**2 + vectnormal[1]**2)
            
            # Calculate the tangent vector
            unitvecttangent = [-unitvectnormal[1], unitvectnormal[0]]
            
            # "Vectorize" the velocities
            cannonballvel = np.array((cannonball.dx, cannonball.dy))
            alienvel = np.array((alien.dx, alien.dy))
            
            cannonballvelPREnorm = np.dot(cannonballvel, unitvectnormal)
            cannonballvelPREtang = np.dot(cannonballvel, unitvecttangent)
            alienvelPREnorm = np.dot(alienvel, unitvectnormal)
            
            # One dimentional collision formulas
            cannonballvelPOSTnorm = (cannonballvelPREnorm*(cannonball.mass-alien.mass) + 2*alien.mass*alienvelPREnorm)/(cannonball.mass+alien.mass)
            cannonballvelPOSTtang = cannonballvelPREtang
            
            cannonballvelPOSTnormvect = np.dot(cannonballvelPOSTnorm, unitvectnormal)
            cannonballvelPOSTtangvect = np.dot(cannonballvelPOSTtang, unitvecttangent)
            
            cannonballvelPOST = cannonballvelPOSTnormvect + cannonballvelPOSTtangvect
            
            # Alter directional speeds of the cannonball
            cannonball.dx = cannonballvelPOST[0]
            cannonball.dy = cannonballvelPOST[1]
            
            # Calculate overlap
            overlap = (distance - (cannonball.radius + alien.radius)) /2
            
            # move objects out of collision
            cannonball.x += overlap * (dist_x / distance)
            cannonball.y += overlap * (dist_y / distance)
            
            self.updatePlayerStats(20,0,0) # Increase Player score
            self.createExplosion(alien.sprite.x, alien.sprite.y) # Create explosion
            
            # Remove alien that was hit
            self.aliens.remove(alien)
            
            # Remove cannonball if is hitlimit has been reached
            if cannonball.hits_left == 1:
                self.player.cannonballs.remove(cannonball)
            else:
                cannonball.hits_left -= 1
            
            
    def update(self, dt):
        # Play while Player's health is not 0
        if self.player_stats.health > 0:
            
            
            ### Set random time interval for killer alien ####
            self.time += dt / np.random.randint(3,8)
            if self.time >= 1:
                if len(self.killer_alien) == 0: # Only one killer alien at a time
                    self.createKillerAlien()
                self.time = 0
            
                
            # Player controls
            if self.key_handler[key.LEFT]:    # Move Player left while left key is pressed
                self.player.moveLeft()
            elif self.key_handler[key.RIGHT]: # Move Player right while right key is pressed
                self.player.moveRight()
            # ToDo: Fix Angle locks in extreme positions.
            elif self.key_handler[key.UP]: # Raise cannon
                self.player.aimUp()
            elif self.key_handler[key.DOWN]: # Lower cannon
                self.player.aimDown()
                

            
            # Animate cannonballs
            for cannonball in self.player.cannonballs:
                # Apply vertical acceleration due to gravity
                cannonball.dy += gravity * dt

                # Update particles with new positions
                cannonball.x -= (cannonball.dx) * dt
                cannonball.y -= (cannonball.dy) * dt
                
                # Remove cannonballs that go out of frame
                if ((cannonball.y + cannonball.radius) > window.height) or ((cannonball.x + cannonball.radius) > window.width):
                    self.player.cannonballs.remove(cannonball)
            
            # Animate Aliens
            for alien in self.aliens:
                # In the alien collision event where an alien is moving upwards; apply gravity
                if alien.dy < 15:
                    # Apply vertical acceleration due to gravity
                    alien.dy += gravity * dt
                
                # Update position
                alien.updateAlienPosition(self.player_stats.score, dt)
                
                    
                # Turn around at window edge
                if (alien.sprite.x > (window.width - 60)):
                    alien.sprite.x = window.width - 60      # Avoid alien sticking to edge of screen
                    alien.direction *= -1
                elif (alien.sprite.x < 0):
                    alien.sprite.x = 0                      # Avoid alien sticking to edge of screen
                    alien.direction *= -1
                    
                # Reduce Player's health by 10 if Aliens reach the bottom
                if (alien.sprite.y < -64):
                    self.updatePlayerStats(0,-10,0) # Decrease Player health
                    self.createExplosion(alien.sprite.x, alien.sprite.y) # Create explosion
                    self.aliens.remove(alien)
                
                # Handle collisions between aliens
                # ToDo: Find a less costly algorithm for this
                for alien2 in self.aliens:
                    if alien != alien2:
                        self.alien_alien_collision_handler(alien, alien2)
                        
            # Update Killer Alien position
            for killer in self.killer_alien:
                if (abs(killer.sprite.x - self.player.position[0]) < 40) and (killer.sprite.y <= self.player.position[1]):
                    self.updatePlayerStats(0,-50,0)
                    self.createExplosion(killer.sprite.x, killer.sprite.y)
                    self.killer_alien.remove(killer)
                elif (killer.sprite.y < -50):
                    self.killer_alien.remove(killer)
                else:
                    killer.updateAlienPosition(self.player.position[0], self.player.position[1], dt)
                                
                
            # Handle collisions between cannonballs and aliens
            # ToDo: Find a less costly algorithm for this
            for cannonball in self.player.cannonballs:
                for alien in self.aliens:
                    self.cannonball_alien_collision_handler(cannonball, alien)
            
            # Remove explosions after a given period (explosion.timer)
            for explosion in self.explosions:
                if explosion.timer < 0:
                    self.explosions.remove(explosion)
                else:
                    explosion.timer -= dt
                    explosion.sprite.scale -= (dt/2)

            # Create new aliens if none are left and reload cannonballs
            if (len(self.aliens) == 0):
                self.create_aliens()
                self.updatePlayerStats(0,0,bullet_limit - self.player.bullets)
                self.player.bullets = bullet_limit
                
        # Game Over when Player's health reaches 0
        else: # self.player_stats.health <= 0: 
            self.gameOver(self.player_stats.score)


class KillerAlien:
    def __init__(self, x, y):
        self.x = x # Alien starting position
        self.y = y # Alien starting position
        self.center_offset = 32 # add to x and y to get true center point for calculations
        self.radius = 32
        
        self.health = aliens_health # May be used for harder levels (if I get to creating levels)
        
        self.angle = np.random.uniform(low=(np.pi/8), high=(6*(np.pi/8)))      # Set random start angle
     
        self.dx = np.random.uniform(50, 80) * np.cos(self.angle) # Initial horizontal speed based on random starting speed
        self.dy = np.random.uniform(15, 40) * np.sin(self.angle) # Initial vertical speed based on random starting speed

        # Load the image for the sprite
        killer_alien_image = pg.image.load(f'aliens/killer_alien_128px_001.png')
        # Create the sprite from the image
        self.sprite = pg.sprite.Sprite(img=killer_alien_image, x=self.x, y=self.y, z=0)
        
        self.explosions = [] # empty list for future explosions

    def updateAlienPosition(self, target_x, target_y, dt):
        self.sprite.x += (target_x - self.sprite.x) * dt # adjust to hit target
        self.sprite.y -= 100 * dt
        # Update particles with new positions and adjust speed based on player score

        
    def draw(self):
        self.sprite.draw()

class Aliens:
    def __init__(self, x, y):
        self.x = x # Alien starting position
        self.y = y # Alien starting position
        self.center_offset = 32 # add to x and y to get true center point for calculations
        self.radius = 32
        self.mass = 200
        self.direction = 1
        self.health = aliens_health       # May be used for harder levels (if I get to creating levels)
        
        self.angle = np.random.uniform(low=(np.pi/8), high=(6*(np.pi/8)))      # Set random start angle
     
        self.dx = np.random.uniform(50, 80) * np.cos(self.angle) # Initial horizontal speed based on random starting speed
        self.dy = np.random.uniform(15, 40) * np.sin(self.angle) # Initial vertical speed based on random starting speed

        # Load the image for the sprite
        alien_image = pg.image.load(f'aliens/aliens_128px_00{np.random.randint(1,8)}.png')
        # Create the sprite from the image
        self.sprite = pg.sprite.Sprite(img=alien_image, x=self.x, y=self.y, z=0)
        
        self.explosions = [] # empty list for future explosions

    def updateAlienPosition(self, score, dt):
        # Update Aliens with new positions and adjust speed based on player score
        if score < 500: # Linear motion
            self.sprite.x -= self.dx * dt * self.direction
            self.sprite.y -= self.dy * dt
        elif score > 499 and score < 1000:
            self.sprite.x -= (self.dx * 2) * dt * self.direction
            self.sprite.y -= (self.dy * 2) * dt
        elif score > 999 and score < 1500:
            self.sprite.x -= (self.dx * 4) * dt * self.direction
            self.sprite.y -= (self.dy * 4) * dt
        elif score > 1499 and score < 2000:
            self.sprite.x -= (self.dx * 6) * dt * self.direction
            self.sprite.y -= (self.dy * 6) * dt
        
    def draw(self):
        self.sprite.draw()


class Player:
    def __init__(self):
        
        self.position = [450, 24, 0]  # Player starting position
        self.direction = 1           # Starting direction; 1 = "right", -1 = "left"
        
        self.angle = np.pi/4
        
        self.bullets = bullet_limit # Initiated in settings at top
        
        # # Load the image for the sprite
        # self.cannon_left = pg.image.load('cannon/cannon_left_64px.png') # FIXED CANNON
        # self.cannon_right = pg.image.load('cannon/cannon_right_64px.png') # FIXED CANNON
        
        # # Create the sprite from the image
        # self.sprite = pg.sprite.Sprite(img=self.cannon_left, x=self.position[0], y=self.position[1], z=0) # FIXED CANNON
        
        self.cannon_base = pg.image.load('cannon/cannon_base_64px.png') # NON-FIXED CANNON
        self.cannon_base.anchor_x = self.cannon_base.width // 2
        self.cannon_base.anchor_y = self.cannon_base.height // 2
        self.cannon = pg.image.load('cannon/cannon_64px.png') # NON-FIXED CANNON
        self.cannon.anchor_x = self.cannon.width // 2
        self.cannon.anchor_y = self.cannon.height // 2
    
        self.sprite_base = pg.sprite.Sprite(img=self.cannon_base, x=self.position[0], y=self.position[1], z=0) # NON-FIXED CANNON
        self.sprite_cannon = pg.sprite.Sprite(img=self.cannon, x=self.position[0], y=self.position[1], z=0) # NON-FIXED CANNON
        
        
        # Create a list to contain cannonballs
        self.cannonballs = []
    
    def moveLeft(self):
        # self.sprite = pg.sprite.Sprite(img=self.cannon_left, x=self.position[0], y=self.position[1], z=0) # FIXED CANNON
        # self.sprite_base = pg.sprite.Sprite(img=self.cannon_base, x=self.position[0], y=self.position[1], z=0) # NON-FIXED CANNON
        # self.sprite_cannon = pg.sprite.Sprite(img=self.cannon, x=self.position[0], y=self.position[1], z=0) # NON-FIXED CANNON
        # self.direction = -1
        if self.position[0] > -32:
            self.position[0] -= 5
            self.sprite_base.x -= 5
            self.sprite_cannon.x -= 5
    
    def moveRight(self):
        # self.sprite = pg.sprite.Sprite(img=self.cannon_right, x=self.position[0], y=self.position[1], z=0) # FIXED CANNON
        self.sprite_base = pg.sprite.Sprite(img=self.cannon_base, x=self.position[0], y=self.position[1], z=0) # NON-FIXED CANNON
        # self.sprite_cannon = pg.sprite.Sprite(img=self.cannon, x=self.position[0], y=self.position[1], z=0) # NON-FIXED CANNON
        # self.direction = 1
        if self.position[0] < (window.width - 32):
            self.position[0] += 5
            self.sprite_base.x += 5
            self.sprite_cannon.x += 5
    
    def aimUp(self):
        # if (self.player.angle <= np.pi) and (self.player.angle >= 0):
        self.angle += (np.pi) / 180
        self.sprite_cannon.rotation -= 1
                
    
    def aimDown(self):
        # if (self.player.angle <= np.pi) and (self.player.angle >= 0):
        self.angle -= (np.pi) / 180
        self.sprite_cannon.rotation += 1
    
    def shoot(self):
        cannonball = Cannonball(self.position[0] - 36, self.position[1] - 36, self.angle, self.direction)
        self.cannonballs.append(cannonball)
        
    def draw(self):
        # self.sprite.draw() # FIXED CANNON
        self.sprite_cannon.draw() # NON-FIXED CANNON
        for cannonball in self.cannonballs:
            cannonball.draw()
        self.sprite_base.draw() # NON-FIXED CANNON


class Cannonball:
    def __init__(self, x, y, angle, direction):
        self.x = x
        self.y = y
        self.radius = 8
        self.segments = 8
        self.color = (255,255,255)
        self.mass = 8
        self.direction = direction
        if direction > 0:
            self.angle = angle      # Set exit angle based on the cannon direction
        else:
            self.angle = np.pi - angle    # Set exit angle based on the cannon direction
        self.speed = -500 # Starting speed
        self.dx = self.speed * np.cos(self.angle) # Initial horizontal speed based on random starting speed
        self.dy = self.speed * np.sin(self.angle) # Initial vertical speed based on random starting speed
        self.hits_left = 2    # Number of aliens each cannonball can destroy
    
    def draw(self):
        if self.direction > 0:
            circle = pg.shapes.Circle(self.x + 46, self.y + 52, self.radius, color=self.color)
        else:
            circle = pg.shapes.Circle(self.x + 12, self.y + 52, self.radius, color=self.color)
        circle.draw()

# class Missile:
#     def __init__(self, x, y):
#         self.x = x # Missile starting position
#         self.y = y # Missile starting position
#         self.center_offset = 32 # add to x and y to get true center point for calculations
#         self.radius = 32
#         self.mass = 200
#         self.direction = 1
#         self.health = 100 # May be used for harder levels (if I get to creating levels)
        
#         # self.angle = np.random.uniform(low=(np.pi/8), high=(6*(np.pi/8)))      # Set exit angle based on the alien position
     
#         self.dx = np.random.uniform(50, 80) * np.cos(self.angle) # Initial horizontal speed based on random starting speed
#         self.dy = np.random.uniform(15, 40) * np.sin(self.angle) # Initial vertical speed based on random starting speed

#         # Load the image for the sprite
#         missile_image = pg.image.load(f'missiles/missile_0{np.random.randint(1,3)}.png')
#         # Create the sprite from the image
#         self.sprite = pg.sprite.Sprite(img=missile_image, x=self.x, y=self.y, z=0)
        
#         self.explosions = [] # empty list for future explosions
        
#         # https://physics.stackexchange.com/questions/249321/angle-required-to-hit-the-target-in-projectile-motion
        
#     def draw(self):
#         self.sprite.draw()


class Explosion:
    def __init__(self, x, y):
        self.timer = 2 # Number of seconds before the explosion disappears
        # Load the image for the sprite
        explosion_image = pg.image.load(f'explosions/explosion_128px_00{np.random.randint(1,4)}.png')
        # Create the sprite from the image
        self.sprite = pg.sprite.Sprite(img=explosion_image, x=x, y=y, z=0)
        self.sprite.scale = 1
    
    def draw(self):
        self.sprite.draw()


class Background:
    def __init__(self):
        # Load the image for the sprite
        background_img = pg.image.load(f'BGs/BG_0{np.random.randint(2,5)}.png')
        # Create the sprite from the image
        self.sprite = pg.sprite.Sprite(img=background_img, x=0, y=0, z=0)
        self.sprite.scale = 1
        
    def draw(self):
        self.sprite.draw()


class Stats:
    def __init__(self, score, health, bullets):
        self.score = score
        self.health = health
        self.bullets = bullets
        
        self.background = pg.shapes.BorderedRectangle(10, 590, 130, -70, 1, (50,50,50), (100,100,100))
        self.background.opacity = 128 # Make 50% translucient
        self.label = pg.text.Label(f'Score:  {self.score}\nHealth: {self.health}\nBullets: {self.bullets}',
                                    font_name='KiwiSoda',
                                    font_size=16,
                                    x=20, y=570,
                                    width=220,
                                    multiline=True)
        
    def draw(self):
        self.background.draw()
        self.label.draw()


class Instructions:
    def __init__(self):
        
        self.background = pg.shapes.BorderedRectangle(890, 590, -180, -95, 1, (50,50,50), (100,100,100))
        self.background.opacity = 128 # Make 50% translucient
        self.label = pg.text.Label(f'Move: [left]/[right]\nAim: [up]/[down]\nShoot: [space]\nQuit: [q]',
                                    font_name='KiwiSoda',
                                    font_size=16,
                                    x=720, y=570,
                                    width=220,
                                    multiline=True)
        
    def draw(self):
        self.background.draw()
        self.label.draw()
        
        
class GameOver:
    def __init__(self, score):
        self.score = score
        
        self.background = pg.shapes.BorderedRectangle(100, 100, 700, 400, 2, (50,50,50), (100,100,100))
        self.background.opacity = 128   # Make 50% translucient
        self.gameover_label = pg.text.Label(f'Game\nOver!',
                          font_name='KiwiSoda',
                          font_size=82,
                          x=100, y=350,
                          width=700,
                          multiline=True,
                          align='center')
        self.final_stats_label = pg.text.Label(f'Final score: {self.score}',
                          font_name='KiwiSoda',
                          font_size=24,
                          x=100, y=180,
                          width=700,
                          align='center')
        self.options_label = pg.text.Label(f'[r] - retry (not working), [q] - quit',
                          font_name='KiwiSoda',
                          font_size=18,
                          x=100, y=140,
                          width=700,
                          align='center')
        
    def draw(self):
        self.background.draw()
        self.gameover_label.draw()
        self.final_stats_label.draw()
        self.options_label.draw()


if __name__ == '__main__':
    window = GameWindow()
    pg.clock.schedule_interval(window.update, 1/60.0)  # Update at 60 FPS
    pg.app.run()