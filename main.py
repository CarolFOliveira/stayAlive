import pgzrun
import random
from pgzero.actor import Actor
from pygame import Rect
# Constants
WIDTH = 640
HEIGHT = 480
CELL_SIZE = 40
GRID_WIDTH = WIDTH // CELL_SIZE
GRID_HEIGHT = HEIGHT // CELL_SIZE
FPS = 60
# Game States
STATE_MENU = 'menu'
STATE_PLAYING = 'playing'
STATE_GAMEOVER = 'gameover'
class AnimatedSprite:
    def __init__(self, images, pos):
        # Recebe uma lista de imagens para animação e posição inicial
        self.images = images 
        self.index = 0
        self.actor = Actor(self.images[self.index], pos=pos)
        self.animation_speed = 0.15 # tempo entre troca de frames
        self.anim_timer = 0 #timer para controlar a troca de frames
    def update(self, dt):
        # Atualiza o timer e troca o frame da animação quando o tempo passar
        self.anim_timer += dt
        if self.anim_timer >= self.animation_speed:
            self.anim_timer = 0
            self.index = (self.index + 1) % len(self.images)
            self.actor.image = self.images[self.index]
    def draw(self):
        self.actor.draw()
    def set_pos(self, pos):
        self.actor.pos = pos
    def get_pos(self):
        return self.actor.pos
class Player:
    def __init__(self, grid_x, grid_y):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.moving = False
        self.move_dir = (1, 0)  
        self.move_progress = 0        
        # Sprites for idle and walking animations
        self.idle_images_right = ['player_idle_1', 'player_idle_2']
        self.idle_images_left = ['player_idle_1_left', 'player_idle_2_left']
        self.walk_images_right = ['player_walk_1', 'player_walk_2', 'player_walk_3']
        self.walk_images_left = ['player_walk_1_left', 'player_walk_2_left', 'player_walk_3_left']
        self.facing_left = False
        self.sprite = AnimatedSprite(self.idle_images_right, self.grid_to_pos())
    def grid_to_pos(self):
    # Converte a posição da grade (grid_x, grid_y) para a posição na tela (em pixels)
        return (self.grid_x * CELL_SIZE + CELL_SIZE // 2,
                self.grid_y * CELL_SIZE + CELL_SIZE // 2)
    def update(self, dt):
        if self.moving:
            speed = 120
            self.move_progress += speed * dt            
            # Atualiza para a direção que está se movendo
            if self.move_dir[0] < 0:
                self.facing_left = True
            elif self.move_dir[0] > 0:
                self.facing_left = False            
            if self.move_progress >= CELL_SIZE:
                self.grid_x += self.move_dir[0]
                self.grid_y += self.move_dir[1]
                self.move_progress = 0
                self.moving = False
                # volta para idle na direção certa
                if self.facing_left:
                    self.sprite.images = self.idle_images_left
                else:
                    self.sprite.images = self.idle_images_right
                self.sprite.index = 0
            else:
                # está andando, mostra animação de caminhada na direção certa
                if self.facing_left:
                    self.sprite.images = self.walk_images_left
                else:
                    self.sprite.images = self.walk_images_right
            base_x = self.grid_x * CELL_SIZE + CELL_SIZE // 2
            base_y = self.grid_y * CELL_SIZE + CELL_SIZE // 2
            dx = self.move_dir[0] * self.move_progress
            dy = self.move_dir[1] * self.move_progress
            self.sprite.set_pos((base_x + dx, base_y + dy))
        else:
            # quando está parado, mantém olhando para a última direção
            if self.facing_left:
                self.sprite.images = self.idle_images_left
            else:
                self.sprite.images = self.idle_images_right
            self.sprite.set_pos(self.grid_to_pos())
        self.sprite.update(dt)
    def draw(self):
        self.sprite.draw()
    def try_move(self, dx, dy, game_map):
        # Verifica se o personagem já está se movendo, não permite outro movimento ao mesmo tempo
        if self.moving:
            return  
        # Calcula a nova posição com base na direção desejada (dx, dy)
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        # Verifica se a nova posição está dentro dos limites do mapa
        if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
            # Verifica se a nova posição é possível de andar
            if game_map.is_walkable(new_x, new_y):
                # Marca o personagem como em movimento e define a direção
                self.moving = True
                self.move_dir = (dx, dy)
    def get_grid_pos(self):
        # Retorna a posição atual do objeto no grid como uma tupla (x, y)
        return self.grid_x, self.grid_y    
class Collectible:
    def __init__(self, grid_x, grid_y, image='coin'):
         # Inicializa um item colecionável na posição da grade com a imagem especificada e define uma posição na tela
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.actor = Actor(image)
        self.actor.pos = (grid_x * CELL_SIZE + CELL_SIZE // 2,
                          grid_y * CELL_SIZE + CELL_SIZE // 2)
        self.image = image    
    def draw(self):
        # Desenha o item na tela
        self.actor.draw()
    def get_grid_pos(self):
        # Retorna a posição do item no grid
        return self.grid_x, self.grid_y
class Projectile:
    # Classe que representa um projétil no jogo.
    # Controla a posição na grade, direção, velocidade e a representação visual (sprite).
    # Atualiza a posição do projétil a cada frame, verificando se está dentro dos limites e se o local é caminhável.
    # Retorna True enquanto o projétil pode continuar se movendo, e False caso contrário.
    def __init__(self, x, y, direction):
        self.grid_x = x
        self.grid_y = y
        self.direction = direction
        self.pos = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
        self.speed = 15  
        self.actor = Actor('projectile', pos=self.pos) 
           
    def update(self, dt, game_map):
        dx, dy = self.direction
        self.grid_x += dx
        self.grid_y += dy
        if 0 <= self.grid_x < GRID_WIDTH and 0 <= self.grid_y < GRID_HEIGHT and game_map.is_walkable(self.grid_x, self.grid_y):
            self.pos = (self.grid_x * CELL_SIZE + CELL_SIZE // 2, self.grid_y * CELL_SIZE + CELL_SIZE // 2)
            self.actor.pos = self.pos
            return True
        return False 
    def draw(self):
        self.actor.draw()
    def get_grid_pos(self):
        return self.grid_x, self.grid_y
class Enemy:
    # Classe que representa um inimigo no jogo.
    # Gerencia a posição na grade, área de movimentação (território), e estado de movimento.
    # Controla a animação entre estados de idle e caminhada usando sprites animados.
    # Atualiza a posição e animação com base no tempo decorrido e movimenta o inimigo aleatoriamente dentro do território permitido.
    # Possui métodos para desenhar o inimigo na tela e obter sua posição atual na grade.
    def __init__(self, grid_x, grid_y, territory):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.territory = territory  # (x_min, x_max, y_min, y_max)
        self.moving = False
        self.move_dir = (0, 0)
        self.move_progress = 0
        self.idle_images = ['enemy_idle_1', 'enemy_idle_2', 'enemy_idle_3']
        self.walk_images = ['enemy_walk_1', 'enemy_walk_2', 'enemy_walk_3', 'enemy_walk_4']
        self.sprite = AnimatedSprite(self.idle_images, self.grid_to_pos())
        self.move_cooldown = 0
    def grid_to_pos(self):
        return (self.grid_x * CELL_SIZE + CELL_SIZE // 2,
                self.grid_y * CELL_SIZE + CELL_SIZE // 2)
    def update(self, dt, game_map):
        self.move_cooldown -= dt
        if not self.moving and self.move_cooldown <= 0:
            self.random_move(game_map)
            self.move_cooldown = random.uniform(0.5, 1)
        if self.moving:
            speed = 10
            self.move_progress += speed * dt
            if self.move_progress >= CELL_SIZE:
                self.grid_x += self.move_dir[0]
                self.grid_y += self.move_dir[1]
                self.move_progress = 0
                self.moving = False
                self.sprite.images = self.idle_images
                self.sprite.index = 0
            else:
                self.sprite.images = self.walk_images
            base_x = self.grid_x * CELL_SIZE + CELL_SIZE // 2
            base_y = self.grid_y * CELL_SIZE + CELL_SIZE // 2
            dx = self.move_dir[0] * self.move_progress
            dy = self.move_dir[1] * self.move_progress
            self.sprite.set_pos((base_x + dx, base_y + dy))
        else:
            self.sprite.set_pos(self.grid_to_pos())
        self.sprite.update(dt)
    def random_move(self, game_map):
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(directions)
        for dx, dy in directions:
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and
                self.territory[0] <= new_x <= self.territory[1] and
                self.territory[2] <= new_y <= self.territory[3] and
                game_map.is_walkable(new_x, new_y)):
                self.moving = True
                self.move_dir = (dx, dy)
                return
    def draw(self):
        self.sprite.draw()
    def get_grid_pos(self):
        return self.grid_x, self.grid_y
class GameMap:
    # Classe que representa o mapa do jogo, armazenando a estrutura da grid com áreas caminháveis e paredes.
    # Inicializa o mapa com todas as células caminháveis, e define paredes nas bordas.
    # Fornece método para verificar se uma posição é caminhável.
    # Também desenha o mapa na tela, usando um fundo ou preenchendo retângulos coloridos para paredes e áreas livres se não conseguir carregar a imagem de background.
    def __init__(self):
        # 0 = walkable, 1 = wall
        self.map_data = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        # Exemplo: paredes nas bordas
        for x in range(GRID_WIDTH):
            self.map_data[0][x] = 1
            self.map_data[GRID_HEIGHT - 1][x] = 1
        for y in range(GRID_HEIGHT):
            self.map_data[y][0] = 1
            self.map_data[y][GRID_WIDTH - 1] = 1
    def is_walkable(self, x, y):
        return self.map_data[y][x] == 0
    def draw(self):
        try:
            screen.blit("background", (0, 0))
        except:
            for y in range(GRID_HEIGHT):
              for x in range(GRID_WIDTH):
                rect = Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if self.map_data[y][x] == 1:
                    screen.draw.filled_rect(rect, "darkgreen")
                else:
                    screen.draw.filled_rect(rect, "lightgreen")
class Button:
    # Classe que representa um botão interativo na tela, com área, texto e ação associada.
    # Atualiza seu estado com base na posição do mouse e clique, executando a ação quando clicado.
    def __init__(self, rect, text, action):
        self.rect = rect  # Rect(left, top, width, height)
        self.text = text
        self.action = action
        self.hover = False
    def draw(self):
        color = "white" if not self.hover else "yellow"
        screen.draw.filled_rect(self.rect, "black")
        screen.draw.rect(self.rect, color)
        screen.draw.textbox(self.text, self.rect, color=color)
    def update(self, mouse_pos, mouse_pressed):
        self.hover = self.rect.collidepoint(mouse_pos)
        if self.hover and mouse_pressed:
            self.action()
class MainGame:
    def __init__(self):
        self.state = STATE_MENU
        self.game_map = GameMap()
        self.player = Player(5, 5)
        self.projectiles = []
        self.collectibles = []
        self.enemies =  [
            Enemy(10, 7, (8, 12, 5, 9)),
            Enemy(15, 10, (13, 17, 8, 12))
        ]
        self.spawn_collectible() 
        self.buttons = []
        sounds.bg_music.play(-1)
        sounds.bg_music.set_volume(0.3)
        self.music_on = True
        self.score = 0
        self.points = ""
        self.create_menu_buttons()
        self.collectibles
        #cria coins em posições aleatórias a cada 5 segundos
        clock.schedule_interval(self.spawn_collectible, 5.0)
       
        
    def create_menu_buttons(self):
        self.buttons = []
        self.buttons.append(Button(Rect((WIDTH//2 - 80, HEIGHT//2 - 60, 160, 40)), "Start Game", self.start_game))
        self.buttons.append(Button(Rect((WIDTH//2 - 80, HEIGHT//2, 160, 40)), "Music", self.toggle_music))
        self.buttons.append(Button(Rect((WIDTH//2 - 80, HEIGHT//2 + 60, 160, 40)), "Quit", self.quit_game))
    def spawn_enemy(self):
        #cria novos inimigos em posições aleatórias, no intervalo de 3 segundos
        if len(self.enemies) >= 10:  
            return
        while True:
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            if self.game_map.is_walkable(x, y):
                territory = (x - 2, x + 2, y - 2, y + 2)
                ocupado = any(enemy.get_grid_pos() == (x, y) for enemy in self.enemies)
                if not ocupado and (x, y) != self.player.get_grid_pos():
                    self.enemies.append(Enemy(x, y, territory))
                    break
        clock.schedule_interval(self.spawn_enemy, 3.0)
    def spawn_collectible(self):  
        #cria 3 itens em posições aleatórias
        for _ in range(3):  # 3 itens
            while True:
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                if self.game_map.is_walkable(x, y):
                    occupied = any(enemy.get_grid_pos() == (x, y) for enemy in self.enemies)
                    if not occupied:
                        self.collectibles.append(Collectible(x, y))
                        break
    def start_game(self):
        self.state = STATE_PLAYING
        self.score = 0
        self.player = Player(5, 5)
        self.projectiles = []
        self.collectibles = [] 
        self.coin_collect = False 
        self.spawn_collectible() 
        self.spawn_enemy() 
        self.enemies = [
            Enemy(10, 7, (8, 12, 5, 9)),
            Enemy(15, 10, (13, 17, 8, 12))
        ]    
    def toggle_music(self):
        if self.music_on:
            sounds.bg_music.stop()
            self.music_on = False
        else:
            sounds.bg_music.play(-1)
            self.music_on = True
    def quit_game(self):
        exit()
    def update(self, dt):
        
        if self.state == STATE_MENU:
            pass  
        elif self.state == STATE_PLAYING:
            self.player.update(dt)
            new_projectiles = []
            for proj in self.projectiles:
                if proj.update(dt, self.game_map):
                    new_projectiles.append(proj)
            self.projectiles = new_projectiles
            # Checar colisão tiro vs inimigo
            for proj in self.projectiles[:]:
                px, py = proj.get_grid_pos()
                for enemy in self.enemies[:]:
                    if (px, py) == enemy.get_grid_pos():
                        sounds.hit.play()
                        sounds.hit.set_volume(0.2)
                        self.enemies.remove(enemy)
                        if proj in self.projectiles:
                            self.projectiles.remove(proj)
                        self.score += 10
                        break
            #checar colisão com coin
            px, py = self.player.get_grid_pos()
            for item in self.collectibles[:]:
                if (px, py) == item.get_grid_pos():
                    sounds.collect.play()
                    sounds.collect.set_volume(0.2)
                    self.coin_collect = True
                    self.collectibles.remove(item)
                    self.score += 5
                    break
                for enemy in self.enemies:
                    enemy.update(dt, self.game_map)
            # Check collisions player vs enemies
            px, py = self.player.get_grid_pos()
            for enemy in self.enemies:
                ex, ey = enemy.get_grid_pos()
                if px == ex and py == ey:
                    self.state = STATE_GAMEOVER
                    sounds.bg_music.stop()
                    sounds.lose.play()
                    self.points = f"Score: {self.score}"
        elif self.state == STATE_GAMEOVER:
            pass     
    def draw(self):
        screen.clear() 
        if self.state == STATE_MENU:
            screen.draw.text("Stay alive", center=(WIDTH // 2, HEIGHT // 3 - 80), fontsize=58, color="yellow")
            for button in self.buttons:
                button.draw()
        elif self.state == STATE_PLAYING:
            self.game_map.draw()
            self.player.draw()
            for enemy in self.enemies:
                enemy.draw()
            for item in self.collectibles:
                item.draw()
            for projectile in self.projectiles:
                projectile.draw()
            screen.draw.text(f"Score: {self.score}", topleft=(20, 10), fontsize=30, color="white")    
        elif self.state == STATE_GAMEOVER:
            screen.blit('skeleton',(10,20))
            screen.blit('game_over',(350,10))
            screen.draw.text(self.points, center=(WIDTH // 2+150, HEIGHT // 2), fontsize=40, color="yellow")        
    def on_mouse_down(self, pos, button):
        if self.state == STATE_MENU and button == mouse.LEFT:
            for btn in self.buttons:
                btn.update(pos, True)
game = MainGame()
def update(dt):
    #movimentação do player
    if game.state == STATE_PLAYING:
        if not game.player.moving:
            if keys.UP in keys_pressed:
                game.player.try_move(0, -1, game.game_map)
            elif keys.DOWN in keys_pressed:
                game.player.try_move(0, 1, game.game_map)
            elif keys.LEFT in keys_pressed:
                game.player.try_move(-1, 0, game.game_map)
            elif keys.RIGHT in keys_pressed:
                game.player.try_move(1, 0, game.game_map)
            elif keys.SPACE in keys_pressed:
                if game.player.facing_left:
                    dx, dy = game.player.move_dir if game.player.moving else (-1, 0)
                    x, y = game.player.get_grid_pos()
                    game.projectiles.append(Projectile(x, y, (dx, dy)))
                else:
                    dx, dy = game.player.move_dir if game.player.moving else (1, 0)
                    x, y = game.player.get_grid_pos()
                    game.projectiles.append(Projectile(x, y, (dx, dy)))      
    game.update(dt)
def draw():
    game.draw() 
keys_pressed = set()
def on_key_down(key):
    keys_pressed.add(key)
def on_key_up(key):
    if key in keys_pressed:
        keys_pressed.remove(key)
def on_mouse_down(pos, button):
    game.on_mouse_down(pos, button)
pgzrun.go()
