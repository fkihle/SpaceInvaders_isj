import pyglet as pg
from pyglet.gl import *
from pyglet.window import key
from pyglet import font
import numpy as np

font.add_file('font/KiwiSoda.ttf') # Custom font

class GameWindow(pg.window.Window):
    def __init__(self):
        super().__init__(fullscreen=False, caption='Space Invaders Game')
        self.width = 900
        self.height = 600
        
        self.time = 0 # Time variable for use with interpolation functions
        
        self.gravity = 200
        
        self.background = Space()           # Initialize background
        self.player = Player()              # Initialize Player
        self.player_stats = Stats(0,100)    # Player starts with: Score = 0, Health = 100
        
        # Create a handler for keypresses
        self.key_handler = key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        
        # Initialize the first platoon of aliens
        self.aliens = [Aliens(np.random.randint(100, 800), np.random.randint(350, 600)) for _ in range(12)]
        
        self.explosions = []
        self.game_over = []


    def createExplosion(self, x, y):
        explosion = Explosion(x, y)
        self.explosions.append(explosion)
    
    
    # Create new aliens
    def create_aliens(self):
        self.aliens = [Aliens(np.random.randint(100, 800), np.random.randint(350, 600)) for _ in range(12)]
        
        
    def updatePlayerStats(self, score_change, health_change):
        self.player_stats = Stats(self.player_stats.score + score_change, self.player_stats.health + health_change)
    
    
    def gameOver(self, score):
        # Remove remaining aliens, cannonballs and explosions
        for alien in self.aliens:
            self.aliens.remove(alien)
        
        for cannonball in self.player.cannonballs:
            self.player.cannonballs.remove(cannonball)
            
        for explosion in self.explosions:
            self.explosions.remove(explosion)
            
        # Hide player
        self.player.sprite.opacity = 0
        # Show GameOver screen
        self.game_over.append(GameOver(score))

        
    def on_key_press(self, symbol, modifiers):
        # Quit the game using the "q" key
        if (symbol == key.SPACE) and (self.player_stats.health > 0): # Shoot (placed here to retrict to one cannonball pr press)
            self.player.shoot()
        elif symbol == key.Q:
            pg.app.exit()
        elif (symbol == key.R) and (self.player_stats.health > 0):  # Don't let the user restart in the middle of a game
            # TRIGGER RESTART OF GAME
            pass
    
    
    def on_draw(self):
        self.clear()  # Clear the window
        self.background.draw()
        self.player.draw()
        for alien in self.aliens:
            alien.draw()
        for explosion in self.explosions:
            explosion.draw()
        self.player_stats.draw()
        for gameover in self.game_over:
            gameover.draw()
    
    
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
            tangent = [-vectnormal[1], vectnormal[0]]
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
            
            
    # This function is a refactorization of the code used in an earlier assignment to suit this need
    def cannonball_alien_collision_handler(self, cannonball, alien):
        # Calculate distance between cannonball and alien
        dist_x = cannonball.x - alien.sprite.x
        dist_y = cannonball.y - alien.sprite.y
        distance = np.sqrt(dist_x**2+dist_y**2)
        
        # Handle collisions between particles
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
            p2velPREnorm = np.dot(alienvel, unitvectnormal)
            
            # One dimentional collision formulas
            cannonballvelPOSTnorm = (cannonballvelPREnorm*(cannonball.mass-alien.mass) + 2*alien.mass*p2velPREnorm)/(cannonball.mass+alien.mass)
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
            
            
            self.updatePlayerStats(20,0) # Increase Player score
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
            
            
            ### Set time interval for interpolation functions ####
            self.time += dt / 3
            if self.time >= 1:
                self.time = 0
                
            # Player controls
            if self.key_handler[key.LEFT]:    # Move Player left while left key is pressed
                self.player.moveLeft()
            elif self.key_handler[key.RIGHT]: # Move Player right while right key is pressed
                self.player.moveRight()
            
            # Animate cannonballs
            for cannonball in self.player.cannonballs:
                # Apply vertical acceleration due to gravity
                cannonball.dy += self.gravity * dt

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
                    alien.dy += self.gravity * dt
                    
                # Update particles with new positions and adjust speed based on player score
                if self.player_stats.score < 500: # Linear motion
                    alien.sprite.x -= alien.dx * dt * alien.direction
                    alien.sprite.y -= alien.dy * dt
                elif self.player_stats.score > 499 and self.player_stats.score < 1000:
                    alien.sprite.x -= (alien.dx * 2) * dt * alien.direction
                    alien.sprite.y -= (alien.dy * 2) * dt
                elif self.player_stats.score > 999 and self.player_stats.score < 1500:
                    alien.sprite.x -= (alien.dx * 4) * dt * alien.direction
                    alien.sprite.y -= (alien.dy * 4) * dt
                elif self.player_stats.score > 1499 and self.player_stats.score < 2000:
                    alien.sprite.x -= (alien.dx * 6) * dt * alien.direction
                    alien.sprite.y -= (alien.dy * 6) * dt
                    
                # Turn around at window edge
                if (alien.sprite.x > (window.width - 60)):
                    alien.sprite.x = window.width - 60      # Avoid alien sticking to edge of screen
                    alien.direction *= -1
                elif (alien.sprite.x < 0):
                    alien.sprite.x = 0                      # Avoid alien sticking to edge of screen
                    alien.direction *= -1
                    
                # Reduce Player's health by 10 if Aliens reach the bottom
                if (alien.sprite.y < -64):
                    self.updatePlayerStats(0,-10) # Decrease Player health
                    self.createExplosion(alien.sprite.x, alien.sprite.y) # Create explosion
                    self.aliens.remove(alien)
                
                # Handle collisions between aliens
                # ToDo: Find a less costly algorithm for this
                for alien2 in self.aliens:
                    if alien != alien2:
                        self.alien_alien_collision_handler(alien, alien2)
                        
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

            # Create new aliens if none are left
            if (len(self.aliens) == 0):
                self.create_aliens()
        # Game Over when Player's health reaches 0
        else: # self.player_stats.health <= 0: 
            self.gameOver(self.player_stats.score)


class Aliens:
    def __init__(self, x, y):
        self.x = x # Alien starting position
        self.y = y # Alien starting position
        self.center_offset = 32 # add to x and y to get true center point for calculations
        self.radius = 32
        self.mass = 200
        self.direction = 1
        self.health = 100 # May be used for harder levels (if I get to creating levels)
        
        self.angle = np.random.uniform(low=(np.pi/8), high=(6*(np.pi/8)))      # Set exit angle based on the cannon direction
     
        self.dx = np.random.uniform(50, 80) * np.cos(self.angle) # Initial horizontal speed based on random starting speed
        self.dy = np.random.uniform(15, 40) * np.sin(self.angle) # Initial vertical speed based on random starting speed

        # Load the image for the sprite
        alien_image = pyglet.image.load(f'aliens/aliens_128px_00{np.random.randint(1,8)}.png')
        # Create the sprite from the image
        self.sprite = pyglet.sprite.Sprite(img=alien_image, x=self.x, y=self.y, z=0)
        
        self.explosions = [] # empty list for future explosions

        
    def draw(self):
        self.sprite.draw()


class Player:
    def __init__(self):
        
        self.position = [450, -8, 0]  # Player starting position
        self.direction = -1           # Starting direction; 1 = "right", -1 = "left"
        
        # Load the image for the sprite
        self.cannon_left = pg.image.load('cannon/cannon_left_64px.png')
        self.cannon_right = pg.image.load('cannon/cannon_right_64px.png')
    
        # Create the sprite from the image
        self.sprite = pg.sprite.Sprite(img=self.cannon_left, x=self.position[0], y=self.position[1], z=0)
        
        # Create a list to contain cannonballs
        self.cannonballs = []
    
    def moveLeft(self):
        self.sprite = pg.sprite.Sprite(img=self.cannon_left, x=self.position[0], y=self.position[1], z=0)
        self.direction = -1
        if self.position[0] > -32:
            self.position[0] -= 5
    
    def moveRight(self):
        self.sprite = pg.sprite.Sprite(img=self.cannon_right, x=self.position[0], y=self.position[1], z=0)
        self.direction = 1
        if self.position[0] < (window.width - 32):
            self.position[0] += 5
    
    def shoot(self):
        cannonball = Cannonball(self.position[0], self.position[1], self.direction)
        self.cannonballs.append(cannonball)
        
    def draw(self):
        self.sprite.draw()
        for cannonball in self.cannonballs:
            cannonball.draw()


class Cannonball:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.radius = 8
        self.segments = 8
        self.color = (255,255,255)
        self.mass = 8
        self.direction = direction
        if direction > 0:
            self.angle = np.pi/4      # Set exit angle based on the cannon direction
        else:
            self.angle = 3*np.pi/4    # Set exit angle based on the cannon direction
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


class Space:
    def __init__(self):
        # Load the image for the sprite
        space_background = pg.image.load('BGs/BG_04.png')
        # Create the sprite from the image
        self.sprite = pg.sprite.Sprite(img=space_background, x=0, y=0, z=0)
        self.sprite.scale = 1
        
    def draw(self):
        self.sprite.draw()


class Stats:
    def __init__(self, score, health):
        self.score = score
        self.health = health
        
        self.background = pg.shapes.BorderedRectangle(10, 590, 130, -50, 1, (50,50,50), (100,100,100))
        self.background.opacity = 128 # Make 50% translucient
        self.label = pg.text.Label(f'Score:  {self.score}\nHealth: {self.health}',
                          font_name='KiwiSoda',
                          font_size=16,
                          x=20, y=570,
                          width=220,
                          multiline=True)
        
    def draw(self):
        self.background.draw()
        self.label.draw()


class GameOver:
    def __init__(self, score):
        self.score = score
        
        self.background = pg.shapes.BorderedRectangle(100, 100, 700, 400, 2, (50,50,50), (100,100,100))
        self.background.opacity = 128                         # Make 50% translucient
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