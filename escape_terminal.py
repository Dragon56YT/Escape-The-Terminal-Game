"""
Escape the Terminal - single-file Python roguelike for the terminal
By: Dragon56YT
Version: v0.6-beta
"""

import curses
import random
import json
import time
import os
from collections import deque

SAVE_FILE = "escape_terminal_save.json"
LORE_LINES = [
    "UNAUTHORIZED ACCESS",
    "TRACE IN PROGRESS...",
    "FIREWALL MOBILIZED",
    "SYSTEM ROOT AHEAD",
    "ANOMALY DETECTED",
    "EXIT NODE DETECTED",
    "THE SYSTEM IS ALWAYS WATCHING...",
    "YOU HEAR ECHOES OF FOOTSTEPS THAT DON'T EXIST.",
    "EVERY TERMINAL HOLDS A FORGOTTEN SECRET.",
    "WHO CONTROLS THIS LABYRINTH?",
    "DON'T TRUST THE NUMBERS YOU SEE ON SCREEN.",
    "DATA STREAMS WHISPER THINGS YOU SHOULDN'T KNOW.",
    "A SHADOW MOVES WHERE THERE IS NO LIGHT."
]

# CONSTANTS - OPTIMIZED
WALL = '#'
FLOOR = '.'
PLAYER_CHAR = '@'
EXIT_CHAR = '>'
AMMO_CHAR = 'o'
HEALTH_CHAR = '+'
ULTRAFIRE_CHAR = 'U'
SHIELD_CHAR = 'S'
INVINCIBILITY_CHAR = 'I'
SPEED_CHAR = 'V'

# MOVEMENT: ONLY arrow keys
MOVE_KEYS = {
    curses.KEY_UP: -1j,
    curses.KEY_DOWN: 1j,
    curses.KEY_LEFT: -1,
    curses.KEY_RIGHT: 1
}

# SHOOTING: ONLY WASD
SHOOT_KEYS = {
    ord('w'): -1j, ord('W'): -1j,
    ord('s'): 1j, ord('S'): 1j,
    ord('a'): -1, ord('A'): -1,
    ord('d'): 1, ord('D'): 1
}

# TIMING - OPTIMIZED
INITIAL_REPEAT_DELAY = 0.4
REPEAT_INTERVAL = 0.2
DAMAGE_STUN_DURATION = 0.8
MIN_ENEMY_SPAWN_DISTANCE = 8
MAX_LEVEL = 10
ULTRAFIRE_DURATION = 7.0
SHIELD_DURATION = -1
INVINCIBILITY_DURATION = 6.0
SPEED_DURATION = 10.0
SNIPER_COOLDOWN = 3.5
MAX_BULLETS = 20  # REDUCED for performance
MAX_ACTIVE_BULLETS = 15  # REDUCED for performance

# HUD LAYOUT
HUD_LINES = 5
MIN_GAME_HEIGHT = 20
MIN_GAME_WIDTH = 40

# OPTIMIZATION CONSTANTS
MAX_ENEMIES = 12  # Limit enemies for performance
CACHE_DURATION = 0.1  # Cache calculations for this duration

def to_xy(pos):
    return int(pos.real), int(pos.imag)

class GameMap:
    def __init__(self, width, height, walls=None):
        self.width = width
        self.height = height
        self.walls = set(walls) if walls else set()
        self._grid_cache = None
        self._cache_time = 0

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_wall(self, x, y):
        return (x, y) in self.walls

    def neighbors(self, x, y):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and not self.is_wall(nx, ny):
                yield nx, ny

    def to_grid(self):
        # OPTIMIZATION: Cache grid generation
        current_time = time.time()
        if self._grid_cache is None or current_time - self._cache_time > CACHE_DURATION:
            self._grid_cache = [[FLOOR for _ in range(self.width)] for __ in range(self.height)]
            for (wx, wy) in self.walls:
                if 0 <= wy < self.height and 0 <= wx < self.width:
                    self._grid_cache[wy][wx] = WALL
            self._cache_time = current_time
        return self._grid_cache

    def random_floor_positions(self):
        for y in range(self.height):
            for x in range(self.width):
                if not self.is_wall(x, y):
                    yield x, y

    def serialize(self):
        return {'width': self.width, 'height': self.height, 'walls': [list(w) for w in self.walls]}

    @staticmethod
    def deserialize(data):
        w = data.get('width')
        h = data.get('height')
        walls = [tuple(wi) for wi in data.get('walls', [])]
        return GameMap(w, h, walls=walls)

def ensure_path(width, height, wall_chance, rng, max_tries=100):  # REDUCED tries for performance
    for _ in range(max_tries):
        walls = set()
        for y in range(height):
            for x in range(width):
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    walls.add((x, y))
                else:
                    if rng.random() < wall_chance:
                        walls.add((x, y))
        sx, sy = 1, 1
        ex, ey = width - 2, height - 2
        walls.discard((sx, sy))
        walls.discard((ex, ey))
        gm = GameMap(width, height, walls=walls)
        if is_reachable(gm, (sx, sy), (ex, ey)):
            return gm, (sx, sy), (ex, ey)
    gm = GameMap(width, height, walls=set())
    return gm, (1, 1), (width - 2, height - 2)

def is_reachable(gm, start, goal):
    sx, sy = start
    gx, gy = goal
    if gm.is_wall(sx, sy) or gm.is_wall(gx, gy):
        return False
    q = deque([(sx, sy)])
    seen = {(sx, sy)}
    while q:
        x, y = q.popleft()
        if (x, y) == (gx, gy):
            return True
        for nx, ny in gm.neighbors(x, y):
            if (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))
    return False

class Player:
    def __init__(self, x, y, hp=3, ammo=10):
        self.x = int(x)
        self.y = int(y)
        self.max_hp = 3
        self.hp = int(hp)
        self.ammo = int(ammo)
        self.current_weapon = 'pistol'
        self.ultrafire_until = 0.0
        self.has_shield = False
        self.invincible_until = 0.0
        self.speed_until = 0.0
        self.score = 0
        self.enemies_killed = {'normal': 0, 'tank': 0, 'sniper': 0}
        self.active_powerup = None
        self._last_damage_time = 0
        self._damage_cooldown = 0.5
        self._last_move_time = 0
        self._move_cooldown = 0.15
        self._last_shot_time = 0
        self._shot_cooldown = 0.2

    def pos(self):
        return (self.x, self.y)

    def has_ultrafire(self):
        return time.time() < self.ultrafire_until

    def has_shield_buff(self):
        return self.has_shield

    def has_invincibility(self):
        return time.time() < self.invincible_until

    def has_speed(self):
        return time.time() < self.speed_until

    def can_take_damage(self):
        return time.time() - self._last_damage_time > self._damage_cooldown

    def can_move(self):
        return time.time() - self._last_move_time > self._move_cooldown

    def can_shoot(self):
        return time.time() - self._last_shot_time > self._shot_cooldown

    def take_damage(self, amount=1):
        if not self.can_take_damage():
            return False
            
        if self.has_shield:
            self.has_shield = False
            self._last_damage_time = time.time()
            return False
        elif not self.has_invincibility():
            self.hp -= amount
            self._last_damage_time = time.time()
            return True
        return False

    def reset_powerups(self):
        self.ultrafire_until = 0.0
        self.has_shield = False
        self.invincible_until = 0.0
        self.speed_until = 0.0
        self.active_powerup = None

    def update_active_powerup(self):
        current_time = time.time()
        self.active_powerup = None
        
        if current_time < self.ultrafire_until:
            self.active_powerup = "UltraFire"
        elif self.has_shield:
            self.active_powerup = "Shield"
        elif current_time < self.invincible_until:
            self.active_powerup = "Invincibility"
        elif current_time < self.speed_until:
            self.active_powerup = "Speed"

    def add_kill(self, enemy_type):
        if enemy_type in self.enemies_killed:
            self.enemies_killed[enemy_type] += 1

    def serialize(self):
        return {
            'x': self.x, 'y': self.y, 
            'hp': self.hp, 'ammo': self.ammo,
            'current_weapon': self.current_weapon,
            'ultrafire_until': self.ultrafire_until,
            'has_shield': self.has_shield,
            'invincible_until': self.invincible_until,
            'speed_until': self.speed_until,
            'score': self.score,
            'max_hp': self.max_hp,
            'enemies_killed': self.enemies_killed,
            'active_powerup': self.active_powerup,
            '_last_damage_time': self._last_damage_time,
            '_last_move_time': self._last_move_time,
            '_last_shot_time': self._last_shot_time
        }

    @staticmethod
    def deserialize(d):
        p = Player(d['x'], d['y'], hp=d.get('hp', 3), ammo=d.get('ammo', 10))
        p.current_weapon = d.get('current_weapon', 'pistol')
        p.ultrafire_until = d.get('ultrafire_until', 0.0)
        p.has_shield = d.get('has_shield', False)
        p.invincible_until = d.get('invincible_until', 0.0)
        p.speed_until = d.get('speed_until', 0.0)
        p.score = d.get('score', 0)
        p.max_hp = d.get('max_hp', 3)
        p.enemies_killed = d.get('enemies_killed', {'normal': 0, 'tank': 0, 'sniper': 0})
        p.active_powerup = d.get('active_powerup', None)
        p._last_damage_time = d.get('_last_damage_time', 0.0)
        p._last_move_time = d.get('_last_move_time', 0.0)
        p._last_shot_time = d.get('_last_shot_time', 0.0)
        return p

class Enemy:
    def __init__(self, x, y, enemy_type="normal"):
        self.x = int(x)
        self.y = int(y)
        self.type = enemy_type
        
        if enemy_type == "tank":
            self.char = 'T'
            self.speed = 4
            self.health = 2
            self.score_value = 300
            self.color_pair = 12
            self.aggro_radius = 7
        elif enemy_type == "sniper":
            self.char = 'S'
            self.speed = 3
            self.health = 1
            self.score_value = 250
            self.color_pair = 13
            self.last_shot_time = 0
            self.shot_cooldown = SNIPER_COOLDOWN
            self.aggro_radius = 10
        else:
            self.char = 'E'
            self.speed = 2
            self.health = 1
            self.score_value = 100
            self.color_pair = 4
            self.aggro_radius = 6

    def pos(self):
        return (self.x, self.y)

    def take_damage(self, damage=1):
        self.health -= damage
        return self.health <= 0

    def can_shoot(self):
        if self.type != "sniper":
            return False
        return time.time() - self.last_shot_time >= self.shot_cooldown

    def update_shot_time(self):
        self.last_shot_time = time.time()

    def serialize(self):
        data = {'x': self.x, 'y': self.y, 'type': self.type}
        if self.type == "sniper":
            data['last_shot_time'] = self.last_shot_time
        return data

    @staticmethod
    def deserialize(d):
        enemy = Enemy(d['x'], d['y'], enemy_type=d.get('type', 'normal'))
        if enemy.type == "sniper":
            enemy.last_shot_time = d.get('last_shot_time', 0)
        return enemy

class Bullet:
    def __init__(self, x, y, dx, dy, weapon_type='pistol', is_enemy_bullet=False, pierce_walls=False):
        self.x = int(x)
        self.y = int(y)
        self.dx = int(dx)
        self.dy = int(dy)
        self.weapon_type = weapon_type
        self.damage = 1
        self.pierce_walls = pierce_walls
        self.char = '*' if not is_enemy_bullet else '!'
        self.is_enemy_bullet = is_enemy_bullet
        self.hit_enemies = set()
        self.created_time = time.time()
        self.max_lifetime = 4.0  # REDUCED for performance

    def pos(self):
        return (self.x, self.y)

    def step(self):
        self.x += self.dx
        self.y += self.dy

    def is_expired(self):
        return time.time() - self.created_time > self.max_lifetime

    def serialize(self):
        return {
            'x': self.x, 'y': self.y, 
            'dx': self.dx, 'dy': self.dy,
            'weapon_type': self.weapon_type,
            'is_enemy_bullet': self.is_enemy_bullet,
            'pierce_walls': self.pierce_walls,
            'created_time': self.created_time
        }

    @staticmethod
    def deserialize(d):
        bullet = Bullet(d['x'], d['y'], d['dx'], d['dy'], 
                       d.get('weapon_type', 'pistol'),
                       d.get('is_enemy_bullet', False),
                       d.get('pierce_walls', False))
        bullet.created_time = d.get('created_time', time.time())
        return bullet

def _state_to_list(obj):
    if isinstance(obj, tuple):
        return [_state_to_list(x) for x in obj]
    if isinstance(obj, list):
        return [_state_to_list(x) for x in obj]
    return obj

def _list_to_state(obj):
    if isinstance(obj, list):
        return tuple(_list_to_state(x) for x in obj)
    return obj

class GameState:
    def __init__(self, level=1, seed=None):
        self.level = int(level)
        self.seed = seed if seed is not None else str(random.randint(0, 10 ** 9))
        self.rng = random.Random(self.seed)
        self.map = None
        self.player = None
        self.enemies = []
        self.bullets = []
        self.ammos = []
        self.powerups = []
        self.exit = None
        self.lore_message = None
        self.special_effects = set()
        self._last_key = None
        self._next_repeat_time = 0.0
        self.stunned_until = 0.0
        self.start_time = time.time()
        self.enemies_killed_this_level = 0
        self._last_enemy_move_time = 0
        self._enemy_move_interval = 0.4  # INCREASED for performance
        self._last_optimization_time = 0  # OPTIMIZATION: Periodic cleanup

    def calculate_enemy_distribution(self):
        if self.level == 1:
            return ["normal"] * 100
        elif self.level <= 3:
            return ["normal"] * 75 + ["tank"] * 25
        elif self.level <= 5:
            return ["normal"] * 65 + ["tank"] * 25 + ["sniper"] * 10
        elif self.level <= 7:
            return ["normal"] * 60 + ["tank"] * 25 + ["sniper"] * 15
        else:
            return ["normal"] * 55 + ["tank"] * 30 + ["sniper"] * 15

    def new_level(self):
        base_w, base_h = 30, 16
        w = min(80, base_w + (self.level - 1) * 2)
        h = min(40, base_h + (self.level - 1) * 1)
        wall_chance = min(0.20 + (self.level - 1) * 0.01, 0.35)
        
        self.map, start, exitpos = ensure_path(w, h, wall_chance, self.rng)
        self.exit = exitpos
        
        if self.player is None:
            self.player = Player(start[0], start[1])
        else:
            self.player.x, self.player.y = start[0], start[1]
            self.player.reset_powerups()
            if self.level % 2 == 0 and self.player.max_hp < 5:
                self.player.max_hp += 1
                self.player.hp = self.player.max_hp

        self.apply_seed_effects_on_start()
        
        # OPTIMIZATION: Limit enemy count
        enemy_count = min(MAX_ENEMIES, 3 + max(0, (self.level - 1) * 2))
        if 'SAFE' in self.special_effects:
            enemy_count = max(1, enemy_count - 3)
            
        floor_positions = list(self.map.random_floor_positions())
        self.rng.shuffle(floor_positions)

        valid_positions = []
        for pos in floor_positions:
            x, y = pos
            if (self.map.in_bounds(x, y) and not self.map.is_wall(x, y) and
                pos != start and pos != exitpos and
                is_reachable(self.map, start, pos)):
                valid_positions.append(pos)

        filtered_positions = []
        px, py = start
        for pos in valid_positions:
            x, y = pos
            distance_to_player = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if distance_to_player >= MIN_ENEMY_SPAWN_DISTANCE:
                filtered_positions.append(pos)

        self.enemies = []
        enemy_distribution = self.calculate_enemy_distribution()
        
        spawn_positions = filtered_positions if filtered_positions else valid_positions
        
        for _ in range(min(enemy_count, len(spawn_positions))):
            if not spawn_positions:
                break
            x, y = spawn_positions.pop()
            enemy_type = self.rng.choice(enemy_distribution)
            self.enemies.append(Enemy(x, y, enemy_type))

        self.ammos = []
        ammo_count = max(1, 2 + self.level // 3)
        ammo_positions = [p for p in valid_positions if p != start and p != exitpos]
        self.rng.shuffle(ammo_positions)
        for _ in range(min(ammo_count, len(ammo_positions))):
            if not ammo_positions:
                break
            x, y = ammo_positions.pop()
            if self.map.in_bounds(x, y) and not self.map.is_wall(x, y):
                self.ammos.append((int(x), int(y)))
        
        self.powerups = []
        powerup_types = ["health", "ultrafire", "shield", "invincibility", "speed"]
        weights = [0.35, 0.15, 0.20, 0.15, 0.15]
        
        occupied_positions = set(start) | set(exitpos) | set(e.pos() for e in self.enemies) | set(self.ammos)
        powerup_positions = [p for p in valid_positions if p not in occupied_positions]
        self.rng.shuffle(powerup_positions)
        
        min_powerups = 1 if self.level % 2 == 0 else 0
        powerups_placed = 0
        
        for ptype, weight in zip(powerup_types, weights):
            if (self.rng.random() < weight or powerups_placed < min_powerups) and powerup_positions:
                x, y = powerup_positions.pop()
                self.powerups.append((x, y, ptype))
                powerups_placed += 1
            
        self.bullets = []
        self.lore_message = self.rng.choice(LORE_LINES)
        self.enemies_killed_this_level = 0
        self._last_enemy_move_time = time.time()
        self._last_optimization_time = time.time()

    def apply_seed_effects_on_start(self):
        s = (self.seed or '').upper()
        if s == 'SAFE':
            self.special_effects.add('SAFE')
        if s == 'H4CK3R':
            if self.player:
                self.player.ammo += 10
            self.special_effects.add('H4CK3R')
        if s == 'GOD':
            if self.player:
                self.player.hp = 999
                self.player.max_hp = 999
            self.special_effects.add('GOD')

    def optimize_game_state(self):
        """OPTIMIZATION: Periodic cleanup of game state"""
        current_time = time.time()
        if current_time - self._last_optimization_time < 2.0:  # Cleanup every 2 seconds
            return
            
        self._last_optimization_time = current_time
        
        # Clean up expired bullets more aggressively
        self.bullets = [b for b in self.bullets if not b.is_expired()]
        
        # Limit bullets to prevent memory issues
        if len(self.bullets) > MAX_ACTIVE_BULLETS:
            self.bullets.sort(key=lambda b: b.created_time)
            self.bullets = self.bullets[-MAX_ACTIVE_BULLETS:]
            
        # Clear map cache to free memory
        if self.map and hasattr(self.map, '_grid_cache'):
            self.map._grid_cache = None

    def serialize(self):
        data = {
            'level': self.level,
            'seed': self.seed,
            'map': self.map.serialize() if self.map else None,
            'player': self.player.serialize() if self.player else None,
            'enemies': [e.serialize() for e in self.enemies],
            'bullets': [b.serialize() for b in self.bullets],
            'ammos': [list(a) for a in self.ammos],
            'powerups': [list(p) for p in self.powerups],
            'exit': list(self.exit) if self.exit else None,
            'lore_message': self.lore_message,
            'special_effects': list(self.special_effects),
            'start_time': self.start_time,
            'stunned_until': self.stunned_until,
            'enemies_killed_this_level': self.enemies_killed_this_level,
            '_last_enemy_move_time': self._last_enemy_move_time
        }
        try:
            rng_state = self.rng.getstate()
            data['rng_state'] = _state_to_list(rng_state)
        except Exception:
            data['rng_state'] = None
        return data

    @staticmethod
    def deserialize(d):
        if not isinstance(d, dict):
            raise ValueError('Invalid save data')
        gs = GameState(level=d.get('level', 1), seed=d.get('seed'))
        if d.get('map'):
            gs.map = GameMap.deserialize(d['map'])
        if d.get('player'):
            gs.player = Player.deserialize(d['player'])
        gs.enemies = [Enemy.deserialize(ed) for ed in d.get('enemies', [])]
        gs.bullets = [Bullet.deserialize(bd) for bd in d.get('bullets', [])]
        gs.ammos = [tuple(a) for a in d.get('ammos', [])]
        gs.powerups = [tuple(p) for p in d.get('powerups', [])]
        gs.exit = tuple(d['exit']) if d.get('exit') else None
        gs.lore_message = d.get('lore_message')
        gs.special_effects = set(d.get('special_effects', []))
        gs.start_time = d.get('start_time', time.time())
        gs.stunned_until = d.get('stunned_until', 0.0)
        gs.enemies_killed_this_level = d.get('enemies_killed_this_level', 0)
        gs._last_enemy_move_time = d.get('_last_enemy_move_time', time.time())
        try:
            if d.get('rng_state'):
                gs.rng.setstate(_list_to_state(d['rng_state']))
        except Exception:
            gs.rng = random.Random(gs.seed)
        return gs

def save_game(gs):
    data = gs.serialize()
    tmp = SAVE_FILE + '.tmp'
    try:
        with open(tmp, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, SAVE_FILE)
        return True
    except Exception as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False

def load_game():
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
        gs = GameState.deserialize(data)
        return gs
    except Exception as e:
        return None

def play_sound(sound_type):
    try:
        if sound_type == 'shoot':
            print('\a', end='', flush=True)
        elif sound_type == 'hit':
            for _ in range(2): 
                print('\a', end='', flush=True)
                time.sleep(0.1)
        elif sound_type == 'powerup':
            for _ in range(3):
                print('\a', end='', flush=True)
                time.sleep(0.05)
        elif sound_type == 'level_up':
            for _ in range(2):
                for i in range(3):
                    print('\a', end='', flush=True)
                    time.sleep(0.1)
                time.sleep(0.2)
    except Exception:
        pass

def move_player(gs, dx, dy):
    if not gs.player or not gs.map:
        return
    if not gs.player.can_move():
        return
        
    nx, ny = gs.player.x + int(dx), gs.player.y + int(dy)
    if not gs.map.in_bounds(nx, ny):
        return
    if gs.map.is_wall(nx, ny):
        return
        
    gs.player.x, gs.player.y = nx, ny
    gs.player._last_move_time = time.time()
    
    # OPTIMIZATION: Use sets for faster lookups
    player_pos = (nx, ny)
    
    if player_pos in gs.ammos:
        try:
            gs.ammos.remove(player_pos)
            gs.player.ammo += 3
            play_sound('powerup')
        except ValueError:
            pass
    
    for powerup in list(gs.powerups):
        px, py, ptype = powerup
        if player_pos == (px, py):
            try:
                gs.powerups.remove(powerup)
                if ptype == "health":
                    gs.player.hp = min(gs.player.max_hp, gs.player.hp + 1)
                elif ptype == "ultrafire":
                    gs.player.ultrafire_until = time.time() + ULTRAFIRE_DURATION
                elif ptype == "shield":
                    gs.player.has_shield = True
                elif ptype == "invincibility":
                    gs.player.invincible_until = time.time() + INVINCIBILITY_DURATION
                elif ptype == "speed":
                    gs.player.speed_until = time.time() + SPEED_DURATION
                play_sound('powerup')
            except ValueError:
                pass

def fire_bullet(gs, dx, dy):
    if not gs.player:
        return
    if gs.player.ammo <= 0 and not gs.player.has_ultrafire():
        return
    if dx == 0 and dy == 0:
        return
    if not gs.player.can_shoot():
        return
        
    # OPTIMIZATION: More aggressive bullet limiting
    if len(gs.bullets) >= MAX_ACTIVE_BULLETS:
        gs.bullets.sort(key=lambda b: b.created_time)
        gs.bullets = gs.bullets[-MAX_ACTIVE_BULLETS//2:]  # Remove half of oldest bullets
        
    if not gs.player.has_ultrafire():
        gs.player.ammo -= 1
        
    pierce_walls = gs.player.has_ultrafire()
    b = Bullet(gs.player.x, gs.player.y, int(dx), int(dy), pierce_walls=pierce_walls)
    gs.bullets.append(b)
    gs.player._last_shot_time = time.time()
    play_sound('shoot')

def enemy_fire_bullet(e, gs, dx, dy):
    if len(gs.bullets) >= MAX_ACTIVE_BULLETS:
        return
        
    b = Bullet(e.x, e.y, int(dx), int(dy), is_enemy_bullet=True)
    gs.bullets.append(b)
    e.update_shot_time()
    play_sound('shoot')

def step_bullets(gs):
    new_bullets = []
    bullet_positions = set()  # OPTIMIZATION: Track bullet positions for collision
    
    for b in gs.bullets:
        if b.is_expired():
            continue
            
        b.step()
        bullet_pos = (b.x, b.y)
        
        if not gs.map.in_bounds(b.x, b.y):
            continue
            
        if gs.map.is_wall(b.x, b.y) and not b.pierce_walls:
            continue
            
        hit_something = False
        
        if not b.is_enemy_bullet:
            # OPTIMIZATION: Check enemy collisions
            for e in list(gs.enemies):
                if bullet_pos == (e.x, e.y) and id(e) not in b.hit_enemies:
                    if e.take_damage(b.damage):
                        gs.player.score += e.score_value
                        gs.player.add_kill(e.type)
                        gs.enemies_killed_this_level += 1
                        try:
                            gs.enemies.remove(e)
                        except ValueError:
                            pass
                    b.hit_enemies.add(id(e))
                    hit_something = True
                    play_sound('hit')
                    if not b.pierce_walls:
                        break
        else:
            if bullet_pos == (gs.player.x, gs.player.y):
                if gs.player.take_damage():
                    apply_damage_stun(gs)
                    play_sound('hit')
                hit_something = True
            
        if not hit_something or b.pierce_walls:
            new_bullets.append(b)
            
    gs.bullets = new_bullets

def enemy_detects_player(e, gs):
    if not gs.player:
        return False
    # OPTIMIZATION: Use squared distance to avoid sqrt
    dx = gs.player.x - e.x
    dy = gs.player.y - e.y
    distance_squared = dx * dx + dy * dy
    return distance_squared <= e.aggro_radius * e.aggro_radius

def can_enemy_move_to(gs, nx, ny, occupied):
    if not gs.map.in_bounds(nx, ny):
        return False
    if gs.map.is_wall(nx, ny):
        return False
    if (nx, ny) in occupied:
        return False
    return True

def try_random_enemy_move(e, gs, occupied):
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]
    gs.rng.shuffle(dirs)
    for dx, dy in dirs:
        nx, ny = e.x + dx, e.y + dy
        if can_enemy_move_to(gs, nx, ny, occupied):
            if (nx, ny) != (e.x, e.y):
                occupied.discard((e.x, e.y))
                e.x, e.y = nx, ny
                occupied.add((e.x, e.y))
            return

def move_enemies(gs):
    if time.time() < gs.stunned_until or not gs.player:
        return
        
    current_time = time.time()
    if current_time - gs._last_enemy_move_time < gs._enemy_move_interval:
        return
        
    gs._last_enemy_move_time = current_time
        
    occupied = set((e.x, e.y) for e in gs.enemies)
    
    # OPTIMIZATION: Handle stuck enemies first
    for e in list(gs.enemies):
        count_at_pos = sum(1 for other in gs.enemies if (other.x, other.y) == (e.x, e.y))
        if count_at_pos > 1:
            try_random_enemy_move(e, gs, occupied)
    
    for e in list(gs.enemies):
        detected = enemy_detects_player(e, gs)
        
        # SNIPER SHOOTING LOGIC
        if e.type == "sniper" and detected and e.can_shoot():
            dx = gs.player.x - e.x
            dy = gs.player.y - e.y
            
            if abs(dx) > abs(dy):
                shot_dx = 1 if dx > 0 else -1
                shot_dy = 0
            else:
                shot_dy = 1 if dy > 0 else -1
                shot_dx = 0
                
            has_line_of_sight = True
            check_x, check_y = e.x, e.y
            
            while (check_x, check_y) != (gs.player.x, gs.player.y):
                check_x += shot_dx
                check_y += shot_dy
                
                if (abs(check_x - e.x) > abs(dx) or 
                    abs(check_y - e.y) > abs(dy)):
                    break
                    
                if not gs.map.in_bounds(check_x, check_y) or gs.map.is_wall(check_x, check_y):
                    has_line_of_sight = False
                    break
                    
            if has_line_of_sight and (check_x, check_y) == (gs.player.x, gs.player.y):
                enemy_fire_bullet(e, gs, shot_dx, shot_dy)
                continue
        
        if detected:
            dx = gs.player.x - e.x
            dy = gs.player.y - e.y
            
            # OPTIMIZATION: Use squared distance
            distance_squared = dx * dx + dy * dy
            
            if distance_squared <= 2.25:  # 1.5 squared
                if gs.player.take_damage():
                    apply_damage_stun(gs)
                    play_sound('hit')
                continue
            else:
                if abs(dx) > abs(dy):
                    choices = [(1 if dx > 0 else -1, 0), (0, 1 if dy > 0 else -1)]
                else:
                    choices = [(0, 1 if dy > 0 else -1), (1 if dx > 0 else -1, 0)]
                
            moved = False
            for dxm, dym in choices:
                nx, ny = e.x + dxm, e.y + dym
                if can_enemy_move_to(gs, nx, ny, occupied):
                    occupied.discard((e.x, e.y))
                    e.x, e.y = nx, ny
                    occupied.add((e.x, e.y))
                    moved = True
                    break
                    
            if not moved:
                all_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                gs.rng.shuffle(all_dirs)
                for dxm, dym in all_dirs:
                    nx, ny = e.x + dxm, e.y + dym
                    if can_enemy_move_to(gs, nx, ny, occupied):
                        occupied.discard((e.x, e.y))
                        e.x, e.y = nx, ny
                        occupied.add((e.x, e.y))
                        moved = True
                        break
        else:
            try_random_enemy_move(e, gs, occupied)
            
        if (e.x, e.y) == (gs.player.x, gs.player.y):
            if gs.player.take_damage():
                apply_damage_stun(gs)
                play_sound('hit')

def draw_game(stdscr, gs):
    stdscr.erase()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()
    
    if max_y < MIN_GAME_HEIGHT or max_x < MIN_GAME_WIDTH:
        try:
            stdscr.addstr(0, 0, f"Terminal too small: {max_x}x{max_y}", curses.color_pair(1))
            stdscr.addstr(1, 0, f"Minimum: {MIN_GAME_WIDTH}x{MIN_GAME_HEIGHT}", curses.color_pair(1))
        except curses.error:
            pass
        stdscr.refresh()
        return
        
    if gs.map is None or gs.player is None:
        return
        
    gs.player.update_active_powerup()
        
    grid = gs.map.to_grid()
    
    hud_height = HUD_LINES
    game_area_height = max_y - hud_height
    
    view_h = min(gs.map.height, game_area_height)
    view_w = min(gs.map.width, max_x)
    
    offset_x = max(0, gs.player.x - view_w // 2)
    offset_y = max(0, gs.player.y - view_h // 2)
    
    offset_x = min(offset_x, gs.map.width - view_w)
    offset_y = min(offset_y, gs.map.height - view_h)
    
    # OPTIMIZATION: Pre-calculate visible area
    visible_area = set()
    
    # Draw terrain and collect visible positions
    for y in range(view_h):
        for x in range(view_w):
            map_x, map_y = offset_x + x, offset_y + y
            if 0 <= map_x < gs.map.width and 0 <= map_y < gs.map.height:
                try:
                    ch = grid[map_y][map_x]
                    if ch == WALL:
                        stdscr.addch(hud_height + y, x, ch, curses.color_pair(1))
                    else:
                        stdscr.addch(hud_height + y, x, ch, curses.color_pair(2))
                    visible_area.add((map_x, map_y))
                except curses.error:
                    pass
                
    # Draw items only in visible area
    for (ax, ay) in gs.ammos:
        if (ax, ay) in visible_area:
            try:
                screen_y = hud_height + (ay - offset_y)
                screen_x = ax - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height):
                    stdscr.addch(screen_y, screen_x, AMMO_CHAR, curses.color_pair(6))
            except curses.error:
                pass
                
    for (px, py, ptype) in gs.powerups:
        if (px, py) in visible_area:
            try:
                screen_y = hud_height + (py - offset_y)
                screen_x = px - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height):
                    if ptype == "health":
                        stdscr.addch(screen_y, screen_x, HEALTH_CHAR, curses.color_pair(8))
                    elif ptype == "ultrafire":
                        stdscr.addch(screen_y, screen_x, ULTRAFIRE_CHAR, curses.color_pair(9))
                    elif ptype == "shield":
                        stdscr.addch(screen_y, screen_x, SHIELD_CHAR, curses.color_pair(10))
                    elif ptype == "invincibility":
                        stdscr.addch(screen_y, screen_x, INVINCIBILITY_CHAR, curses.color_pair(15))
                    elif ptype == "speed":
                        stdscr.addch(screen_y, screen_x, SPEED_CHAR, curses.color_pair(16))
            except curses.error:
                pass
                
    if gs.exit and gs.exit in visible_area:
        ex, ey = gs.exit
        try:
            screen_y = hud_height + (ey - offset_y)
            screen_x = ex - offset_x
            if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height):
                stdscr.addch(screen_y, screen_x, EXIT_CHAR, curses.color_pair(7))
        except curses.error:
            pass
                
    for e in gs.enemies:
        if (e.x, e.y) in visible_area:
            try:
                screen_y = hud_height + (e.y - offset_y)
                screen_x = e.x - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height):
                    stdscr.addch(screen_y, screen_x, e.char, curses.color_pair(e.color_pair) | curses.A_BOLD)
            except curses.error:
                pass
                
    for b in gs.bullets:
        if (b.x, b.y) in visible_area:
            try:
                screen_y = hud_height + (b.y - offset_y)
                screen_x = b.x - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height):
                    color = 5 if not b.is_enemy_bullet else 14
                    stdscr.addch(screen_y, screen_x, b.char, curses.color_pair(color) | curses.A_BOLD)
            except curses.error:
                pass
                
    show_player = True
    if time.time() < gs.stunned_until:
        show_player = int(time.time() * 6) % 2 == 0
    elif gs.player.has_invincibility():
        show_player = int(time.time() * 10) % 2 == 0
        
    if (show_player and 
        (gs.player.x, gs.player.y) in visible_area):
        try:
            screen_y = hud_height + (gs.player.y - offset_y)
            screen_x = gs.player.x - offset_x
            if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height):
                color = curses.color_pair(3)
                if gs.player.has_shield_buff():
                    color = curses.color_pair(10)
                elif gs.player.has_invincibility():
                    color = curses.color_pair(15)
                elif gs.player.has_speed():
                    color = curses.color_pair(16)
                    
                stdscr.addch(screen_y, screen_x, PLAYER_CHAR, color | curses.A_BOLD)
        except curses.error:
            pass
            
    # HUD - OPTIMIZED with better truncation
    play_time = int(time.time() - gs.start_time)
    minutes = play_time // 60
    seconds = play_time % 60
    
    try:
        title = f"ESCAPE v0.6-beta - L{gs.level}"  # SHORTENED for performance
        if len(title) > max_x:
            title = title[:max_x]
        stdscr.addstr(0, 0, title, curses.color_pair(1) | curses.A_BOLD)
    except curses.error:
        pass
    
    try:
        health_bar = "♥" * gs.player.hp + "♡" * (gs.player.max_hp - gs.player.hp)
        shield_indicator = " [S]" if gs.player.has_shield_buff() else ""  # SHORTENED
        ammo_info = f"A:{gs.player.ammo}"  # SHORTENED
        
        line2 = f"HP:{health_bar}{shield_indicator} {ammo_info}"
        if len(line2) > max_x:
            line2 = line2[:max_x]
        stdscr.addstr(1, 0, line2, curses.color_pair(1))
    except curses.error:
        pass
    
    try:
        powerup_display = gs.player.active_powerup if gs.player.active_powerup else "None"
        powerup_text = f"P:{powerup_display}"  # SHORTENED
        score_text = f"S:{gs.player.score}"  # SHORTENED
        
        line3 = f"{powerup_text} {score_text}"
        if len(line3) > max_x:
            line3 = line3[:max_x]
        stdscr.addstr(2, 0, line3, curses.color_pair(1))
    except curses.error:
        pass
    
    try:
        time_text = f"T:{minutes:02d}:{seconds:02d}"  # SHORTENED
        enemies_text = f"E:{len(gs.enemies)}"  # SHORTENED
        seed_text = f"ID:{gs.seed[:4]}..." if len(gs.seed) > 4 else f"ID:{gs.seed}"  # SHORTENED
        
        line4 = f"{time_text} {enemies_text} {seed_text}"
        if len(line4) > max_x:
            line4 = line4[:max_x]
        stdscr.addstr(3, 0, line4, curses.color_pair(1))
    except curses.error:
        pass
    
    try:
        controls = "Arrows:Move WASD:Shoot P:Pause"
        if len(controls) > max_x:
            controls = controls[:max_x]
        stdscr.addstr(4, 0, controls, curses.color_pair(1))
    except curses.error:
        pass
        
    if gs.lore_message and (hud_height + view_h + 1) < max_y:
        try:
            lore_msg = f"> {gs.lore_message}"
            if len(lore_msg) > max_x:
                lore_msg = lore_msg[:max_x-4] + "..."
            stdscr.addstr(hud_height + view_h + 1, 0, lore_msg, curses.color_pair(1))
        except curses.error:
            pass
        
    stdscr.refresh()

def show_victory_screen(stdscr, gs):
    stdscr.nodelay(False)
    stdscr.erase()
    
    play_time = int(time.time() - gs.start_time)
    minutes = play_time // 60
    seconds = play_time % 60
    
    max_y, max_x = stdscr.getmaxyx()
    
    try:
        stdscr.addstr(2, 2, "███████ VICTORY! ███████", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(4, 2, "SYSTEM ESCAPED - TERMINAL RESTORED", curses.color_pair(1))
        stdscr.addstr(6, 2, f"Final Score: {gs.player.score}", curses.color_pair(1))
        stdscr.addstr(7, 2, f"Levels Completed: {gs.level}", curses.color_pair(1))
        stdscr.addstr(8, 2, f"Time: {minutes:02d}:{seconds:02d}", curses.color_pair(1))
        stdscr.addstr(10, 2, "Enemies Defeated:", curses.color_pair(1))
        stdscr.addstr(11, 4, f"Basic: {gs.player.enemies_killed['normal']}", curses.color_pair(1))
        stdscr.addstr(12, 4, f"Tanks: {gs.player.enemies_killed['tank']}", curses.color_pair(1))
        stdscr.addstr(13, 4, f"Snipers: {gs.player.enemies_killed['sniper']}", curses.color_pair(1))
        stdscr.addstr(15, 2, "Press any key to return to menu", curses.color_pair(1))
    except curses.error:
        pass
    stdscr.getch()

def show_game_over(stdscr, gs):
    stdscr.nodelay(False)
    stdscr.erase()
    
    play_time = int(time.time() - gs.start_time)
    minutes = play_time // 60
    seconds = play_time % 60
    
    try:
        stdscr.addstr(2, 2, "SIGNAL LOST - GAME OVER", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(4, 2, f"You reached level {gs.level}", curses.color_pair(1))
        stdscr.addstr(5, 2, f"Final Score: {gs.player.score}", curses.color_pair(1))
        stdscr.addstr(6, 2, f"Time: {minutes:02d}:{seconds:02d}", curses.color_pair(1))
        stdscr.addstr(8, 2, "Enemies Defeated:", curses.color_pair(1))
        stdscr.addstr(9, 4, f"Basic: {gs.player.enemies_killed['normal']}", curses.color_pair(1))
        stdscr.addstr(10, 4, f"Tanks: {gs.player.enemies_killed['tank']}", curses.color_pair(1))
        stdscr.addstr(11, 4, f"Snipers: {gs.player.enemies_killed['sniper']}", curses.color_pair(1))
        stdscr.addstr(13, 2, "Press any key to return to menu", curses.color_pair(1))
    except curses.error:
        pass
    stdscr.getch()

def show_level_complete(stdscr, gs):
    stdscr.nodelay(False)
    stdscr.erase()
    
    try:
        stdscr.addstr(2, 2, "LEVEL COMPLETE!", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(4, 2, f"Enemies defeated this level: {gs.enemies_killed_this_level}", curses.color_pair(1))
        stdscr.addstr(5, 2, f"Total score: {gs.player.score}", curses.color_pair(1))
        if gs.level % 2 == 0 and gs.player.max_hp < 5:
            stdscr.addstr(7, 2, "MAX HEALTH INCREASED!", curses.color_pair(8) | curses.A_BOLD)
        stdscr.addstr(9, 2, "Press any key to continue to next level", curses.color_pair(1))
    except curses.error:
        pass
    stdscr.getch()
    play_sound('level_up')

def menu(stdscr):
    curses.curs_set(0)
    options = ["Nueva partida", "Cargar partida", "Salir"]
    selected = 0
    
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        stdscr.attron(curses.color_pair(1))
        try:
            title = "███████ ESCAPE THE TERMINAL ███████"
            if len(title) > max_x:
                title = title[:max_x]
            
            stdscr.addstr(0, 0, title, curses.color_pair(1) | curses.A_BOLD)
            
            credit = "By: Dragon56YT - v0.6-beta"
            if 1 < max_y:
                stdscr.addstr(1, 0, credit, curses.color_pair(1))
        except curses.error:
            pass
        
        for i, opt in enumerate(options):
            if 3 + i < max_y:
                prefix = "> " if i == selected else "  "
                try:
                    stdscr.addstr(3 + i, 2, prefix + opt, curses.color_pair(1))
                except curses.error:
                    pass
        
        try:
            if 7 < max_y:
                stdscr.addstr(7, 2, "Use arrow keys and Enter", curses.color_pair(1))
        except curses.error:
            pass
            
        stdscr.attroff(curses.color_pair(1))
        stdscr.refresh()
        
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('w'), ord('W')):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S')):
            selected = (selected + 1) % len(options)
        elif key in (ord('\n'), ord('\r'), 10, 13):
            return options[selected]
        elif key == 27:
            if options[selected] == 'Salir':
                return 'Salir'
            else:
                continue

def prompt_seed(stdscr):
    curses.curs_set(1)
    curses.echo()
    stdscr.clear()
    
    max_y, max_x = stdscr.getmaxyx()
    
    try:
        stdscr.addstr(2, 2, "███████ NEW GAME ███████", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(4, 2, "Enter seed (leave blank for random): ", curses.color_pair(1))
        stdscr.addstr(6, 2, "Secret seeds: GOD, H4CK3R, SAFE", curses.color_pair(1))
        stdscr.addstr(8, 2, "Press ESC to return to main menu", curses.color_pair(1))
    except curses.error:
        pass
        
    stdscr.refresh()
    
    input_x = 40
    stdscr.move(4, input_x)
    
    try:
        max_input_len = min(20, max_x - input_x)
        input_str = ""
        
        if max_input_len > 0:
            while True:
                stdscr.move(4, input_x + len(input_str))
                ch = stdscr.getch()
                
                if ch == 27:
                    curses.curs_set(0)
                    curses.noecho()
                    return None
                elif ch in (10, 13):
                    break
                elif ch == curses.KEY_BACKSPACE or ch == 127 or ch == 8:
                    if len(input_str) > 0:
                        input_str = input_str[:-1]
                        stdscr.addch(4, input_x + len(input_str), ' ')
                        stdscr.move(4, input_x + len(input_str))
                elif len(input_str) < max_input_len and 32 <= ch <= 126:
                    input_str += chr(ch)
                    stdscr.addch(4, input_x + len(input_str) - 1, chr(ch))
    except Exception:
        input_str = ""
        
    curses.curs_set(0)
    curses.noecho()
    
    return input_str

def prompt_confirm_load(stdscr):
    curses.curs_set(0)
    while True:
        stdscr.erase()
        try:
            stdscr.addstr(2, 2, "███████ LOAD GAME ███████", curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(4, 2, "Cargar partida - presiona Enter para cargar o ESC para volver", curses.color_pair(1))
        except curses.error:
            pass
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (10, 13):
            return True
        if ch == 27:
            return False

def pause_menu(stdscr, gs):
    curses.curs_set(0)
    options = ["Continuar", "Guardar partida", "Cargar partida", "Salir al menu"]
    sel = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            stdscr.addstr(2, 2, "-- PAUSA --", curses.color_pair(1) | curses.A_BOLD)
            for i, o in enumerate(options):
                if 4 + i < max_y:
                    prefix = "> " if i == sel else "  "
                    stdscr.addstr(4 + i, 4, prefix + o, curses.color_pair(1))
            
            if 10 < max_y:
                stdscr.addstr(10, 4, "Flechas para navegar, Enter para seleccionar, ESC para continuar", curses.color_pair(1))
        except curses.error:
            pass
        
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (curses.KEY_UP, ord('w'), ord('W')):
            sel = (sel - 1) % len(options)
        elif ch in (curses.KEY_DOWN, ord('s'), ord('S')):
            sel = (sel + 1) % len(options)
        elif ch in (10, 13):
            choice = options[sel]
            if choice == 'Continuar':
                return 'continue'
            if choice == 'Guardar partida':
                if save_game(gs):
                    try:
                        stdscr.addstr(12, 4, "Partida guardada!", curses.color_pair(1))
                        stdscr.refresh()
                        time.sleep(1)
                    except curses.error:
                        pass
                return 'continue'
            if choice == 'Cargar partida':
                loaded = load_game()
                if loaded:
                    return ('load', loaded)
                else:
                    stdscr.erase()
                    try:
                        stdscr.addstr(4, 4, "No se encontró partida guardada.", curses.color_pair(1))
                        stdscr.addstr(6, 4, "Presiona cualquier tecla para continuar", curses.color_pair(1))
                    except curses.error:
                        pass
                    stdscr.getch()
                    continue
            if choice == 'Salir al menu':
                return 'menu'
        elif ch == 27:
            return 'continue'

def apply_damage_stun(gs):
    gs.stunned_until = time.time() + DAMAGE_STUN_DURATION

def run_game(stdscr, gs):
    stdscr.nodelay(True)
    last_time = time.time()
    tick = 0
    gs._last_key = None
    gs._next_repeat_time = 0.0

    # OPTIMIZATION: Frame rate limiting
    target_fps = 30
    frame_duration = 1.0 / target_fps

    while True:
        current_time = time.time()
        elapsed = current_time - last_time
        
        # OPTIMIZATION: Proper frame rate limiting
        if elapsed < frame_duration:
            time.sleep(frame_duration - elapsed)
            continue
            
        last_time = current_time
        tick += 1

        # OPTIMIZATION: Periodic game state optimization
        if tick % 60 == 0:  # Every ~2 seconds at 30 FPS
            gs.optimize_game_state()

        key = stdscr.getch()
        
        move_delta = None
        shoot_delta = None

        if key != -1:
            if current_time < gs.stunned_until:
                if key == ord('p') or key == 27:
                    res = pause_menu(stdscr, gs)
                    if res == 'menu':
                        stdscr.nodelay(False)
                        return
                    if isinstance(res, tuple) and res[0] == 'load':
                        gs = res[1]
                key = -1
            else:
                if key in MOVE_KEYS:
                    delta = MOVE_KEYS.get(key)
                    dx, dy = int(delta.real), int(delta.imag)
                    nowt = current_time

                    if gs._last_key != key:
                        move_delta = (dx, dy)
                        gs._last_key = key
                        gs._next_repeat_time = nowt + INITIAL_REPEAT_DELAY
                    else:
                        if nowt >= gs._next_repeat_time:
                            move_delta = (dx, dy)
                            gs._next_repeat_time = nowt + REPEAT_INTERVAL

                elif key in SHOOT_KEYS:
                    delta = SHOOT_KEYS[key]
                    sx, sy = int(delta.real), int(delta.imag)
                    shoot_delta = (sx, sy)
                    gs._last_key = None

                elif key == ord('p') or key == 27:
                    res = pause_menu(stdscr, gs)
                    if res == 'menu':
                        stdscr.nodelay(False)
                        return
                    if isinstance(res, tuple) and res[0] == 'load':
                        gs = res[1]
                else:
                    gs._last_key = None
        else:
            if gs._last_key is not None and current_time > gs._next_repeat_time + 0.5:
                gs._last_key = None

        if move_delta:
            steps = 2 if gs.player.has_speed() else 1
            for step in range(steps):
                if gs.player and gs.player.hp > 0 and gs.player.can_move():
                    move_player(gs, move_delta[0], move_delta[1])
                else:
                    break
                    
        if shoot_delta and gs.player.can_shoot():
            fire_bullet(gs, shoot_delta[0], shoot_delta[1])

        if current_time >= gs.stunned_until:
            step_bullets(gs)

        move_enemies(gs)

        if gs.exit and gs.player and (gs.player.x, gs.player.y) == gs.exit:
            gs.player.score += 1000 * gs.level
            gs.level += 1
            if gs.level > MAX_LEVEL:
                show_victory_screen(stdscr, gs)
                return
            show_level_complete(stdscr, gs)
            gs.new_level()

        if gs.player and gs.player.hp <= 0:
            show_game_over(stdscr, gs)
            return

        draw_game(stdscr, gs)

def main(stdscr):
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_YELLOW, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        curses.init_pair(7, curses.COLOR_MAGENTA, -1)
        curses.init_pair(8, curses.COLOR_GREEN, -1)
        curses.init_pair(9, curses.COLOR_YELLOW, -1)
        curses.init_pair(10, curses.COLOR_BLUE, -1)
        curses.init_pair(11, curses.COLOR_YELLOW, -1)
        curses.init_pair(12, curses.COLOR_MAGENTA, -1)
        curses.init_pair(13, curses.COLOR_CYAN, -1)
        curses.init_pair(14, curses.COLOR_RED, -1)
        curses.init_pair(15, curses.COLOR_WHITE, -1)
        curses.init_pair(16, curses.COLOR_MAGENTA, -1)
    except curses.error:
        pass

    while True:
        choice = menu(stdscr)
        if choice == 'Salir':
            break
        elif choice == 'Cargar partida':
            confirm = prompt_confirm_load(stdscr)
            if not confirm:
                continue
            loaded = load_game()
            if not loaded:
                stdscr.erase()
                try:
                    stdscr.addstr(2, 2, "No se encontró partida guardada.", curses.color_pair(1))
                    stdscr.addstr(4, 2, "Presiona cualquier tecla para continuar", curses.color_pair(1))
                except curses.error:
                    pass
                stdscr.getch()
                continue
            else:
                gs = loaded
                if gs.map is None or gs.player is None:
                    gs = GameState(level=1, seed=gs.seed)
                    gs.new_level()
                run_game(stdscr, gs)
        elif choice == 'Nueva partida':
            seed_input = prompt_seed(stdscr)
            if seed_input is None:
                continue
            seed = seed_input if seed_input != "" else None
            gs = GameState(level=1, seed=seed)
            gs.new_level()
            run_game(stdscr, gs)

if __name__ == '__main__':
    curses.wrapper(main)
