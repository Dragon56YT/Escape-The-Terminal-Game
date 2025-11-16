"""
Escape the Terminal - single-file Python roguelike for the terminal
By: Dragon56YT
Version: v0.9-beta

Escape the Terminal © 2025 by Dragon56YT is licensed under Creative Commons Attribution-NonCommercial 4.0 International.
To view a copy of this license, visit https://creativecommons.org/licenses/by-nc/4.0/

"""

def check_dependencies():
    """Verificar que todas las dependencias estén disponibles"""
    missing_deps = []
    
    # Verificar curses
    try:
        import curses
    except ImportError:
        missing_deps.append("curses")
    
    # Verificar otros módulos estándar que deberían estar disponibles
    required_std = ['random', 'json', 'time', 'os', 'pickle', 'base64', 'glob', 'collections', 'datetime']
    for module in required_std:
        try:
            __import__(module)
        except ImportError:
            missing_deps.append(module)
    
    return missing_deps

def show_install_instructions(missing_deps):
    """Mostrar instrucciones de instalación amigables"""
    print("=" * 70)
    print("¡DEPENDENCIAS FALTANTES!")
    print("=" * 70)
    print(f"Módulos no encontrados: {', '.join(missing_deps)}")
    print()
    
    if "curses" in missing_deps:
        print("PARA INSTALAR CURSES EN WINDOWS:")
        print("  pip install windows-curses")
        print()
        print("O si usas conda:")
        print("  conda install -c conda-forge windows-curses")
        print()
        print("En Linux/macOS, curses suele estar incluido por defecto.")
        print("Si no es así, instálalo con:")
        print("  sudo apt-get install libncurses5-dev   # Debian/Ubuntu")
        print("  brew install ncurses                   # macOS")
    
    print()
    print("Una vez instaladas las dependencias, vuelve a ejecutar el juego.")
    print("=" * 70)
    input("Presiona Enter para salir...")

# Verificar dependencias al inicio
missing = check_dependencies()
if missing:
    show_install_instructions(missing)
    exit(1)

# Si todas las dependencias están disponibles, importar normalmente
import curses
import random
import json
import time
import os
import pickle
import base64
import glob
from collections import deque
from datetime import datetime

# DEVELOPER: Debug mode
DEBUG_MODE = False

# Sistema de guardados mejorado
SAVE_DIR = "escape_saves"
AUTOSAVE_FILE = "autosave.json"
MAX_SAVE_SLOTS = 5
SAVE_VERSION = "0.9"

# Lore actualizado con más líneas
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
    "A SHADOW MOVES WHERE THERE IS NO LIGHT.",
    "THE WALLS ARE SPEAKING IN BINARY.",
    "YOUR MEMORY IS NOT YOUR OWN.",
    "THE EXIT IS A LIE. THE EXIT IS TRUTH.",
    "THIS MAZE RECONFIGURES ITSELF WHEN YOU BLINK.",
    "THE ENEMIES REMEMBER YOU FROM LAST TIME.",
    "YOUR AMMO COUNTS DOWNWARD FROM AN UNKNOWN NUMBER.",
    "THE TERMINAL IS DREAMING OF ELECTRIC SHEEP."
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

# MOVEMENT: arrow keys + vi keys
MOVE_KEYS = {
    curses.KEY_UP: -1j, ord('k'): -1j, ord('K'): -1j,
    curses.KEY_DOWN: 1j, ord('j'): 1j, ord('J'): 1j,
    curses.KEY_LEFT: -1, ord('h'): -1, ord('H'): -1,
    curses.KEY_RIGHT: 1, ord('l'): 1, ord('L'): 1
}

# SHOOTING: WASD + vi keys + diagonals
SHOOT_KEYS = {
    ord('w'): -1j, ord('W'): -1j,
    ord('s'): 1j, ord('S'): 1j,
    ord('a'): -1, ord('A'): -1,
    ord('d'): 1, ord('D'): 1,
    # Diagonals
    ord('q'): -1-1j, ord('Q'): -1-1j,
    ord('e'): 1-1j, ord('E'): 1-1j,
    ord('z'): -1+1j, ord('Z'): -1+1j,
    ord('c'): 1+1j, ord('C'): 1+1j,
}

# TIMING - OPTIMIZED
INITIAL_REPEAT_DELAY = 0.3
REPEAT_INTERVAL = 0.15
DAMAGE_STUN_DURATION = 0.6
MIN_ENEMY_SPAWN_DISTANCE = 8
MAX_LEVEL = 10
ULTRAFIRE_DURATION = 7.0
SHIELD_DURATION = -1
INVINCIBILITY_DURATION = 6.0
SPEED_DURATION = 10.0
SNIPER_COOLDOWN = 3.0
MAX_BULLETS = 20
MAX_ACTIVE_BULLETS = 15

# HUD LAYOUT
HUD_LINES = 6
MIN_GAME_HEIGHT = 20
MIN_GAME_WIDTH = 40

# OPTIMIZATION CONSTANTS
MAX_ENEMIES = 12
CACHE_DURATION = 0.1

# NUEVO: Sistema de logging para debug
def debug_log(message, level='INFO'):
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            with open('debug_log.txt', 'a') as f:
                f.write(f"[{timestamp}] {level}: {message}\n")
        except Exception:
            pass

def to_xy(pos):
    return int(pos.real), int(pos.imag)

def bresenham_line(x0, y0, x1, y1):
    """Bresenham's line algorithm for accurate line-of-sight checking"""
    # FIX: Manejar caso donde los puntos son iguales
    if x0 == x1 and y0 == y1:
        return [(x0, y0)]
        
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
            
    points.append((x, y))
    return points

# NUEVO: Sistema de animaciones
class Animation:
    def __init__(self, x, y, anim_type, duration=0.4):
        self.x = x
        self.y = y
        self.type = anim_type  # 'hit', 'death', 'heal', 'powerup'
        self.start_time = time.time()
        self.duration = duration
        self.frames = []
        self.setup_frames()
        debug_log(f"Animation created: {anim_type} at ({x}, {y})")
    
    def setup_frames(self):
        if self.type == 'hit':
            self.frames = ['✸', '✹', '*']  # Animación de impacto
        elif self.type == 'death':
            self.frames = ['✹', '✸', '*', '·', ' ']  # Animación de muerte
        elif self.type == 'heal':
            self.frames = ['+', '♡', '♥']  # Animación de curación
        elif self.type == 'powerup':
            self.frames = ['◆', '◇', '◈']  # Animación de power-up
    
    def get_current_frame(self):
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        frame_index = min(int(progress * len(self.frames)), len(self.frames) - 1)
        return self.frames[frame_index]
    
    def is_finished(self):
        finished = time.time() - self.start_time >= self.duration
        if finished:
            debug_log(f"Animation finished: {self.type} at ({self.x}, {self.y})")
        return finished

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
        current_time = time.time()
        if self._grid_cache is None or current_time - self._cache_time > CACHE_DURATION:
            # PARCHÉ: Eliminado del innecesario que causaba memory leaks
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
        if not data:
            return None
        w = data.get('width')
        h = data.get('height')
        walls = [tuple(wi) for wi in data.get('walls', [])]
        return GameMap(w, h, walls=walls)

def ensure_path(width, height, wall_chance, rng, max_tries=200):
    # FIX: Garantizar que siempre retorne un mapa válido
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
    
    # FALLBACK: Crear un pasillo garantizado si fallan los intentos
    walls = set()
    for y in range(height):
        for x in range(width):
            if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                walls.add((x, y))
            # Crear un pasillo central
            elif (x != width // 2 and y != height // 2) and rng.random() < 0.3:
                walls.add((x, y))
                
    gm = GameMap(width, height, walls=walls)
    return gm, (1, 1), (width - 2, height - 2)

def is_reachable(gm, start, goal):
    if not gm:
        return False
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
        self._move_cooldown = 0.12  # Base, se ajusta con power-ups
        self._last_shot_time = 0
        self._shot_cooldown = 0.15  # Base, se ajusta con power-ups

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
        # FIX: Actualizar cooldown dinámicamente para power-ups de velocidad
        current_cooldown = 0.06 if self.has_speed() else 0.12
        return time.time() - self._last_move_time > current_cooldown

    def can_shoot(self):
        # FIX: Actualizar cooldown dinámicamente para power-ups de velocidad
        current_cooldown = 0.08 if self.has_speed() else 0.15
        return time.time() - self._last_shot_time > current_cooldown

    def take_damage(self, amount=1):
        if not self.can_take_damage():
            return False
            
        if self.has_shield:
            self.has_shield = False
            self._last_damage_time = time.time()
            debug_log("Player shield blocked damage")
            return False
        elif not self.has_invincibility():
            self.hp -= amount
            self._last_damage_time = time.time()
            debug_log(f"Player took damage, HP: {self.hp}")
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
            debug_log(f"Player killed {enemy_type}, total: {self.enemies_killed[enemy_type]}")

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
        if not d:
            return None
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
            
        self.last_move_time = 0
        self.move_cooldown = 0.5 / (self.speed * 0.5)
        # REEMPLAZO: Usar timestamp y random en lugar de uuid
        self.unique_id = f"{x}_{y}_{enemy_type}_{time.time()}_{random.random()}"
        debug_log(f"Enemy created: {enemy_type} at ({x}, {y}) ID: {self.unique_id}")

    def pos(self):
        return (self.x, self.y)

    def take_damage(self, damage=1):
        self.health -= damage
        debug_log(f"Enemy {self.type} took damage, health: {self.health}")
        return self.health <= 0

    def can_shoot(self):
        if self.type != "sniper":
            return False
        return time.time() - self.last_shot_time >= self.shot_cooldown

    def can_move(self):
        return time.time() - self.last_move_time >= self.move_cooldown

    def update_shot_time(self):
        self.last_shot_time = time.time()
        
    def update_move_time(self):
        self.last_move_time = time.time()

    def serialize(self):
        data = {'x': self.x, 'y': self.y, 'type': self.type, 'unique_id': self.unique_id}
        if self.type == "sniper":
            data['last_shot_time'] = self.last_shot_time
        return data

    @staticmethod
    def deserialize(d):
        if not d:
            return None
        enemy = Enemy(d['x'], d['y'], enemy_type=d.get('type', 'normal'))
        # REEMPLAZO: Generar nuevo ID si no existe en los datos
        enemy.unique_id = d.get('unique_id', f"{d['x']}_{d['y']}_{d.get('type', 'normal')}_{time.time()}_{random.random()}")
        if enemy.type == "sniper":
            enemy.last_shot_time = d.get('last_shot_time', 0)
        return enemy

class Bullet:
    # FIX: Contador estático para IDs únicos
    _next_id = 0
    
    def __init__(self, x, y, dx, dy, weapon_type='pistol', is_enemy_bullet=False, pierce_walls=False):
        self.id = Bullet._next_id
        Bullet._next_id += 1
        self.x = int(x)
        self.y = int(y)
        self.dx = int(dx)
        self.dy = int(dy)
        self.weapon_type = weapon_type
        self.damage = 1
        self.pierce_walls = pierce_walls
        self.char = '*' if not is_enemy_bullet else '!'
        self.is_enemy_bullet = is_enemy_bullet
        # PARCHÉ: Usar unique_id en lugar de posiciones para evitar colisiones
        self.hit_enemy_ids = set()
        self.created_time = time.time()
        self.max_lifetime = 4.0
        debug_log(f"Bullet created: ID {self.id} at ({x}, {y})")

    def pos(self):
        return (self.x, self.y)

    def step(self):
        self.x += self.dx
        self.y += self.dy

    def is_expired(self):
        expired = time.time() - self.created_time > self.max_lifetime
        if expired:
            debug_log(f"Bullet {self.id} expired")
        return expired

    def serialize(self):
        return {
            'x': self.x, 'y': self.y, 
            'dx': self.dx, 'dy': self.dy,
            'weapon_type': self.weapon_type,
            'is_enemy_bullet': self.is_enemy_bullet,
            'pierce_walls': self.pierce_walls,
            'created_time': self.created_time,
            'id': self.id
        }

    @staticmethod
    def deserialize(d):
        if not d:
            return None
        bullet = Bullet(d['x'], d['y'], d['dx'], d['dy'], 
                       d.get('weapon_type', 'pistol'),
                       d.get('is_enemy_bullet', False),
                       d.get('pierce_walls', False))
        bullet.created_time = d.get('created_time', time.time())
        bullet.id = d.get('id', Bullet._next_id)
        Bullet._next_id = max(Bullet._next_id, bullet.id + 1)
        return bullet

def _state_to_list(obj):
    try:
        return base64.b64encode(pickle.dumps(obj)).decode('ascii')
    except Exception as e:
        debug_log(f"Error in _state_to_list: {e}", "ERROR")
        return None

def _list_to_state(obj):
    try:
        return pickle.loads(base64.b64decode(obj.encode('ascii')))
    except Exception as e:
        debug_log(f"Error in _list_to_state: {e}", "ERROR")
        return None

# Sistema de gestión de guardados
class SaveManager:
    def __init__(self):
        self.save_dir = SAVE_DIR
        self.ensure_save_dir()
    
    def ensure_save_dir(self):
        """Crear directorio de guardados si no existe"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def get_save_path(self, slot_number=None, filename=None):
        """Obtener ruta completa del archivo de guardado"""
        if filename:
            return os.path.join(self.save_dir, filename)
        elif slot_number:
            return os.path.join(self.save_dir, f"slot_{slot_number}.json")
        else:
            return os.path.join(self.save_dir, AUTOSAVE_FILE)
    
    def list_saves(self):
        """Listar todas las partidas guardadas con metadatos"""
        saves = []
        
        # Buscar archivos de slot
        for slot_file in glob.glob(os.path.join(self.save_dir, "slot_*.json")):
            try:
                with open(slot_file, 'r') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                saves.append({
                    'filename': os.path.basename(slot_file),
                    'slot_number': metadata.get('slot_number', 0),
                    'save_name': metadata.get('save_name', 'Unnamed'),
                    'level': metadata.get('level', 1),
                    'score': metadata.get('score', 0),
                    'play_time': metadata.get('play_time', 0),
                    'date_modified': metadata.get('date_modified', 'Unknown')
                })
            except Exception as e:
                debug_log(f"Error loading save {slot_file}: {e}", "ERROR")
                continue
        
        # Ordenar por slot number
        saves.sort(key=lambda x: x['slot_number'])
        return saves
    
    def get_empty_slots(self):
        """Obtener slots vacíos disponibles"""
        existing_slots = {save['slot_number'] for save in self.list_saves()}
        return [i for i in range(1, MAX_SAVE_SLOTS + 1) if i not in existing_slots]
    
    def save_game(self, game_state, slot_number=None, save_name=None, is_autosave=False):
        """Guardar partida en un slot específico o autosave"""
        try:
            if is_autosave:
                save_path = self.get_save_path()
                slot_number = "autosave"
            else:
                if not slot_number:
                    return False, "No slot specified"
                save_path = self.get_save_path(slot_number)
            
            # Preparar metadatos
            play_time = int(time.time() - game_state.start_time)
            metadata = {
                'version': SAVE_VERSION,
                'slot_number': slot_number,
                'save_name': save_name or f"Slot {slot_number}",
                'level': game_state.level,
                'score': game_state.player.score if game_state.player else 0,
                'play_time': play_time,
                'seed': game_state.seed,
                'date_created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'date_modified': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Preparar datos completos
            save_data = {
                'metadata': metadata,
                'game_data': game_state.serialize()
            }
            
            # Guardar con archivo temporal para evitar corrupción
            temp_path = save_path + '.tmp'
            with open(temp_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            # Reemplazar archivo original
            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_path, save_path)
            
            debug_log(f"Game saved to {save_path}")
            return True, f"Game saved to slot {slot_number}"
            
        except Exception as e:
            # Limpiar archivo temporal en caso de error
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            debug_log(f"Save failed: {str(e)}", "ERROR")
            return False, f"Save failed: {str(e)}"
    
    def load_game(self, slot_number=None, filename=None):
        """Cargar partida desde un slot o archivo específico"""
        try:
            if filename:
                save_path = self.get_save_path(filename=filename)
            elif slot_number == "autosave":
                save_path = self.get_save_path()
            else:
                save_path = self.get_save_path(slot_number)
            
            if not os.path.exists(save_path):
                return None, "Save file not found"
            
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Verificar versión
            metadata = save_data.get('metadata', {})
            if metadata.get('version') != SAVE_VERSION:
                return None, f"Save version mismatch. Expected {SAVE_VERSION}, got {metadata.get('version')}"
            
            # Cargar estado del juego usando deserialización robusta
            game_data = save_data.get('game_data', {})
            game_state = safe_deserialize(game_data)
            
            if not game_state:
                return None, "Failed to load game data"
            
            # Aplicar efectos de semilla si existen
            if hasattr(game_state, 'seed'):
                game_state.apply_seed_effects_on_start()
            
            debug_log(f"Game loaded from {save_path}")
            return game_state, "Game loaded successfully"
            
        except Exception as e:
            debug_log(f"Load failed: {str(e)}", "ERROR")
            return None, f"Load failed: {str(e)}"
    
    def delete_save(self, slot_number):
        """Eliminar partida guardada"""
        try:
            save_path = self.get_save_path(slot_number)
            if os.path.exists(save_path):
                os.remove(save_path)
                debug_log(f"Save deleted: {save_path}")
                return True, "Save deleted"
            else:
                return False, "Save file not found"
        except Exception as e:
            debug_log(f"Delete failed: {str(e)}", "ERROR")
            return False, f"Delete failed: {str(e)}"

# PARCHÉ: Función de deserialización robusta
def safe_deserialize(data):
    """Deserialización segura con validación completa"""
    if not data or not isinstance(data, dict):
        debug_log("Invalid save data structure", "ERROR")
        return None
        
    required_fields = ['level', 'seed', 'player']
    for field in required_fields:
        if field not in data:
            debug_log(f"Missing required field: {field}", "ERROR")
            return None
            
    try:
        gs = GameState(level=data.get('level', 1), seed=data.get('seed'))
        
        if data.get('map'):
            gs.map = GameMap.deserialize(data['map'])
        if data.get('player'):
            gs.player = Player.deserialize(data['player'])
        
        gs.enemies = []
        for ed in data.get('enemies', []):
            enemy = Enemy.deserialize(ed)
            if enemy:
                gs.enemies.append(enemy)
                
        gs.bullets = []
        for bd in data.get('bullets', []):
            bullet = Bullet.deserialize(bd)
            if bullet:
                gs.bullets.append(bullet)
                
        gs.ammos = [tuple(a) for a in data.get('ammos', []) if isinstance(a, list) and len(a) == 2]
        gs.powerups = [tuple(p) for p in data.get('powerups', []) if isinstance(p, list) and len(p) == 3]
        
        if data.get('exit') and isinstance(data['exit'], list) and len(data['exit']) == 2:
            gs.exit = tuple(data['exit'])
            
        gs.lore_message = data.get('lore_message')
        gs.special_effects = set(data.get('special_effects', []))
        gs.start_time = data.get('start_time', time.time())
        gs.stunned_until = data.get('stunned_until', 0.0)
        gs.enemies_killed_this_level = data.get('enemies_killed_this_level', 0)
        gs._last_enemy_move_time = data.get('_last_enemy_move_time', time.time())
        gs.current_save_slot = data.get('current_save_slot')
        
        try:
            if data.get('rng_state'):
                gs.rng.setstate(_list_to_state(data['rng_state']))
        except Exception as e:
            debug_log(f"Error restoring RNG state: {e}", "ERROR")
            gs.rng = random.Random(gs.seed)
            
        return gs
        
    except Exception as e:
        debug_log(f"Deserialization failed: {e}", "ERROR")
        return None

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
        self._enemy_move_interval = 0.35
        self._last_optimization_time = 0
        self.game_version = SAVE_VERSION
        self.current_save_slot = None
        # NUEVO: Lista de animaciones
        self.animations = []
        
        debug_log(f"GameState created: level {level}, seed {seed}")

    def add_animation(self, x, y, anim_type):
        """Añadir una nueva animación"""
        self.animations.append(Animation(x, y, anim_type))

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
        
        # FIX: Asegurar que siempre tenemos un mapa válido
        try:
            self.map, start, exitpos = ensure_path(w, h, wall_chance, self.rng)
        except Exception as e:
            # Fallback absoluto si ensure_path falla
            debug_log(f"ensure_path failed: {e}, using fallback", "ERROR")
            self.map = GameMap(w, h, walls=set())
            start, exitpos = (1, 1), (w-2, h-2)
        
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
        
        # Aplicar efecto de velocidad si está activo
        if 'SPEED' in self.special_effects:
            self._enemy_move_interval = 0.2
        
        enemy_count = min(MAX_ENEMIES, 3 + max(0, (self.level - 1) * 2))
        if 'SAFE' in self.special_effects:
            enemy_count = 0
            
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
        # NUEVO: Limpiar animaciones al cambiar de nivel
        self.animations = []
        
        debug_log(f"New level created: {self.level}, enemies: {len(self.enemies)}")

    def apply_seed_effects_on_start(self):
        s = (self.seed or '').upper()
        self.special_effects.clear()
        
        if s == 'SAFE':
            self.special_effects.add('SAFE')
            if self.player:
                self.player.has_shield = True
        elif s == 'GOD':
            self.special_effects.add('GOD')
            if self.player:
                self.player.hp = 999
                self.player.max_hp = 999
                self.player.ammo = 999
        elif s == 'SPEED':
            self.special_effects.add('SPEED')
            self._enemy_move_interval = 0.2

    def optimize_game_state(self):
        current_time = time.time()
        if current_time - self._last_optimization_time < 2.0:
            return
            
        self._last_optimization_time = current_time
        
        # FIX: Limitar balas más agresivamente
        self.bullets = [b for b in self.bullets if not b.is_expired()]
        
        if len(self.bullets) > MAX_ACTIVE_BULLETS:
            self.bullets.sort(key=lambda b: b.created_time)
            self.bullets = self.bullets[-MAX_ACTIVE_BULLETS:]
            
        # FIX: Limpiar animaciones terminadas
        self.animations = [anim for anim in self.animations if not anim.is_finished()]
            
        if self.map and hasattr(self.map, '_grid_cache'):
            self.map._grid_cache = None
            
        debug_log(f"Optimized: {len(self.bullets)} bullets, {len(self.animations)} animations")

    def serialize(self):
        data = {
            'version': self.game_version,
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
            '_last_enemy_move_time': self._last_enemy_move_time,
            'current_save_slot': self.current_save_slot
        }
        try:
            rng_state = self.rng.getstate()
            data['rng_state'] = _state_to_list(rng_state)
        except Exception as e:
            debug_log(f"Error serializing RNG state: {e}", "ERROR")
            data['rng_state'] = None
        return data

    @staticmethod
    def deserialize(d):
        """Método legacy - usar safe_deserialize en su lugar"""
        return safe_deserialize(d)

# Funciones de guardado/load mejoradas
save_manager = SaveManager()

def save_game(gs, slot_number=None, save_name=None, is_autosave=False):
    """Guardar partida usando el sistema nuevo"""
    if not gs:
        return False, "No game state to save"
    
    # Si es autosave, usar el slot actual o crear uno temporal
    if is_autosave:
        if gs.current_save_slot:
            slot_number = gs.current_save_slot
        else:
            slot_number = "autosave"
    
    success, message = save_manager.save_game(gs, slot_number, save_name, is_autosave)
    if success and not is_autosave:
        gs.current_save_slot = slot_number
    return success, message

def load_game(slot_number=None, filename=None):
    """Cargar partida usando el sistema nuevo"""
    return save_manager.load_game(slot_number, filename)

def autosave_game(gs):
    """Autoguardado automático"""
    if gs and gs.player and gs.player.hp > 0:
        return save_game(gs, is_autosave=True)
    return False, "Cannot autosave"

# NUEVO: Sistema de sonidos mejorado
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
        elif sound_type == 'enemy_hit':  # NUEVO
            print('\a', end='', flush=True)
            time.sleep(0.05)
        elif sound_type == 'enemy_death':  # NUEVO
            for i in range(3):
                print('\a', end='', flush=True)
                time.sleep(0.1)
        elif sound_type == 'powerup_get':  # NUEVO
            for i in range(2):
                print('\a', end='', flush=True)
                time.sleep(0.05)
    except Exception as e:
        debug_log(f"Sound error: {e}", "ERROR")

def move_player(gs, dx, dy):
    if not gs or not gs.player or not gs.map:
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
    
    player_pos = (nx, ny)
    
    # Collect ammo
    if player_pos in gs.ammos:
        gs.ammos = [pos for pos in gs.ammos if pos != player_pos]
        gs.player.ammo += 3
        play_sound('powerup_get')
        gs.add_animation(nx, ny, 'powerup')  # NUEVO: Animación al recoger munición
    
    # Collect powerups
    for i, (px, py, ptype) in enumerate(gs.powerups[:]):
        if player_pos == (px, py):
            gs.powerups.pop(i)
            if ptype == "health":
                gs.player.hp = min(gs.player.max_hp, gs.player.hp + 1)
                gs.add_animation(nx, ny, 'heal')  # NUEVO: Animación de curación
            elif ptype == "ultrafire":
                gs.player.ultrafire_until = time.time() + ULTRAFIRE_DURATION
                gs.add_animation(nx, ny, 'powerup')
            elif ptype == "shield":
                gs.player.has_shield = True
                gs.add_animation(nx, ny, 'powerup')
            elif ptype == "invincibility":
                gs.player.invincible_until = time.time() + INVINCIBILITY_DURATION
                gs.add_animation(nx, ny, 'powerup')
            elif ptype == "speed":
                gs.player.speed_until = time.time() + SPEED_DURATION
                gs.add_animation(nx, ny, 'powerup')
            play_sound('powerup_get')
            break

def fire_bullet(gs, dx, dy):
    if not gs or not gs.player:
        return
    if gs.player.ammo <= 0 and not gs.player.has_ultrafire() and 'GOD' not in gs.special_effects:
        return
    if dx == 0 and dy == 0:
        return
    if not gs.player.can_shoot():
        return
        
    # FIX: Limitar balas más agresivamente
    if len(gs.bullets) >= MAX_ACTIVE_BULLETS:
        gs.bullets.sort(key=lambda b: b.created_time)
        gs.bullets = gs.bullets[-(MAX_ACTIVE_BULLETS//2):]
        
    if not gs.player.has_ultrafire() and 'GOD' not in gs.special_effects:
        gs.player.ammo -= 1
        
    pierce_walls = gs.player.has_ultrafire()
    b = Bullet(gs.player.x, gs.player.y, int(dx), int(dy), pierce_walls=pierce_walls)
    gs.bullets.append(b)
    gs.player._last_shot_time = time.time()
    play_sound('shoot')

def enemy_fire_bullet(e, gs, dx, dy):
    if not gs or len(gs.bullets) >= MAX_ACTIVE_BULLETS:
        return
        
    b = Bullet(e.x, e.y, int(dx), int(dy), is_enemy_bullet=True)
    gs.bullets.append(b)
    e.update_shot_time()
    play_sound('shoot')

def step_bullets(gs):
    if not gs:
        return
        
    new_bullets = []
    
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
            for e in gs.enemies[:]:
                # PARCHÉ: Usar unique_id en lugar de id() para evitar colisiones
                if bullet_pos == (e.x, e.y) and e.unique_id not in b.hit_enemy_ids:
                    # NUEVO: Añadir animación de impacto
                    gs.add_animation(e.x, e.y, 'hit')
                    play_sound('enemy_hit')
                    
                    if e.take_damage(b.damage):
                        # NUEVO: Añadir animación de muerte
                        gs.add_animation(e.x, e.y, 'death')
                        play_sound('enemy_death')
                        
                        if gs.player:
                            gs.player.score += e.score_value
                            gs.player.add_kill(e.type)
                            gs.enemies_killed_this_level += 1
                        gs.enemies.remove(e)
                    b.hit_enemy_ids.add(e.unique_id)
                    hit_something = True
                    if not b.pierce_walls:
                        break
        else:
            if gs.player and bullet_pos == (gs.player.x, gs.player.y):
                if gs.player.take_damage():
                    apply_damage_stun(gs)
                    play_sound('hit')
                hit_something = True
            
        if not hit_something or b.pierce_walls:
            new_bullets.append(b)
            
    gs.bullets = new_bullets

def enemy_detects_player(e, gs):
    if not gs or not gs.player:
        return False
    dx = gs.player.x - e.x
    dy = gs.player.y - e.y
    distance_squared = dx * dx + dy * dy
    return distance_squared <= e.aggro_radius * e.aggro_radius

def can_enemy_move_to(gs, nx, ny, occupied):
    if not gs or not gs.map:
        return False
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
                # PARCHÉ: Manejo seguro del occupied set
                current_pos = (e.x, e.y)
                if current_pos in occupied:
                    occupied.discard(current_pos)
                e.x, e.y = nx, ny
                occupied.add((e.x, e.y))
                e.update_move_time()
            return True
    return False

def move_enemies(gs):
    if not gs or not gs.player:
        return
        
    if time.time() < gs.stunned_until:
        return
        
    current_time = time.time()
    if current_time - gs._last_enemy_move_time < gs._enemy_move_interval:
        return
        
    gs._last_enemy_move_time = current_time
        
    occupied = set((e.x, e.y) for e in gs.enemies)
    
    for e in gs.enemies[:]:
        if not e.can_move():
            continue
            
        detected = enemy_detects_player(e, gs)
        
        if e.type == "sniper" and detected and e.can_shoot():
            dx = gs.player.x - e.x
            dy = gs.player.y - e.y
            
            if abs(dx) > abs(dy):
                shot_dx = 1 if dx > 0 else -1
                shot_dy = 0
            else:
                shot_dy = 1 if dy > 0 else -1
                shot_dx = 0
                
            line = bresenham_line(e.x, e.y, gs.player.x, gs.player.y)
            has_line_of_sight = True
            for (lx, ly) in line[1:]:
                if not gs.map.in_bounds(lx, ly) or gs.map.is_wall(lx, ly):
                    has_line_of_sight = False
                    break
                    
            if has_line_of_sight:
                enemy_fire_bullet(e, gs, shot_dx, shot_dy)
                e.update_move_time()
                continue
        
        if detected:
            dx = gs.player.x - e.x
            dy = gs.player.y - e.y
            
            distance_squared = dx * dx + dy * dy
            
            if distance_squared <= 2.25:
                if gs.player.take_damage():
                    apply_damage_stun(gs)
                    play_sound('hit')
                e.update_move_time()
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
                    # PARCHÉ: Manejo seguro del occupied set
                    old_pos = (e.x, e.y)
                    if old_pos in occupied:
                        occupied.discard(old_pos)
                    e.x, e.y = nx, ny
                    occupied.add((e.x, e.y))
                    moved = True
                    e.update_move_time()
                    break
                    
            if not moved:
                all_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                gs.rng.shuffle(all_dirs)
                for dxm, dym in all_dirs:
                    nx, ny = e.x + dxm, e.y + dym
                    if can_enemy_move_to(gs, nx, ny, occupied):
                        old_pos = (e.x, e.y)
                        if old_pos in occupied:
                            occupied.discard(old_pos)
                        e.x, e.y = nx, ny
                        occupied.add((e.x, e.y))
                        moved = True
                        e.update_move_time()
                        break
        else:
            try_random_enemy_move(e, gs, occupied)
            
        if (e.x, e.y) == (gs.player.x, gs.player.y):
            if gs.player.take_damage():
                apply_damage_stun(gs)
                play_sound('hit')

# NUEVO: Función para dibujar animaciones
def draw_animations(stdscr, gs, offset_x, offset_y, hud_height, visible_area):
    """Dibujar todas las animaciones activas"""
    for anim in gs.animations[:]:
        if (anim.x, anim.y) in visible_area:
            try:
                screen_x = anim.x - offset_x
                screen_y = hud_height + (anim.y - offset_y)
                
                frame = anim.get_current_frame()
                if frame != ' ':  # No dibujar frames vacíos
                    color = curses.color_pair(5)  # Amarillo para hit
                    if anim.type == 'death':
                        color = curses.color_pair(4)  # Rojo para muerte
                    elif anim.type == 'heal':
                        color = curses.color_pair(8)  # Verde para curación
                    elif anim.type == 'powerup':
                        color = curses.color_pair(9)  # Cyan para power-up
                    
                    stdscr.addch(screen_y, screen_x, frame, color | curses.A_BOLD)
            
            except curses.error:
                pass
        
        # Eliminar animaciones terminadas (se hace en optimize_game_state)

def draw_game(stdscr, gs):
    if not stdscr or not gs:
        return
        
    stdscr.erase()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()
    
    # FIX: Verificación mejorada de tamaño de terminal
    if max_y < MIN_GAME_HEIGHT or max_x < MIN_GAME_WIDTH:
        try:
            msg1 = f"Terminal too small: {max_x}x{max_y}"
            msg2 = f"Minimum: {MIN_GAME_WIDTH}x{MIN_GAME_HEIGHT}"
            if len(msg1) <= max_x and 0 < max_y:
                stdscr.addstr(0, 0, msg1, curses.color_pair(1))
            if len(msg2) <= max_x and 1 < max_y:
                stdscr.addstr(1, 0, msg2, curses.color_pair(1))
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
    
    # FIX: Asegurar que las dimensiones de vista sean válidas
    view_h = min(gs.map.height, max(1, game_area_height))
    view_w = min(gs.map.width, max(1, max_x))
    
    offset_x = max(0, gs.player.x - view_w // 2)
    offset_y = max(0, gs.player.y - view_h // 2)
    
    offset_x = min(offset_x, max(0, gs.map.width - view_w))
    offset_y = min(offset_y, max(0, gs.map.height - view_h))
    
    visible_area = set()
    
    for y in range(view_h):
        for x in range(view_w):
            map_x, map_y = offset_x + x, offset_y + y
            if 0 <= map_x < gs.map.width and 0 <= map_y < gs.map.height:
                try:
                    ch = grid[map_y][map_x]
                    screen_y = hud_height + y
                    screen_x = x
                    # FIX: Verificación adicional de bounds para terminal pequeña
                    if 0 <= screen_x < max_x and 0 <= screen_y < max_y:
                        if ch == WALL:
                            stdscr.addch(screen_y, screen_x, ch, curses.color_pair(1))
                        else:
                            stdscr.addch(screen_y, screen_x, ch, curses.color_pair(2))
                        visible_area.add((map_x, map_y))
                except curses.error:
                    pass
                
    for (ax, ay) in gs.ammos:
        if (ax, ay) in visible_area:
            try:
                screen_y = hud_height + (ay - offset_y)
                screen_x = ax - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height) and screen_y < max_y:
                    stdscr.addch(screen_y, screen_x, AMMO_CHAR, curses.color_pair(6))
            except curses.error:
                pass
                
    for (px, py, ptype) in gs.powerups:
        if (px, py) in visible_area:
            try:
                screen_y = hud_height + (py - offset_y)
                screen_x = px - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height) and screen_y < max_y:
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
            if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height) and screen_y < max_y:
                stdscr.addch(screen_y, screen_x, EXIT_CHAR, curses.color_pair(7))
        except curses.error:
            pass
                
    for e in gs.enemies:
        if (e.x, e.y) in visible_area:
            try:
                screen_y = hud_height + (e.y - offset_y)
                screen_x = e.x - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height) and screen_y < max_y:
                    attr = curses.color_pair(e.color_pair) | curses.A_BOLD
                    if e.health < (2 if e.type == "tank" else 1):
                        attr |= curses.A_BLINK
                    stdscr.addch(screen_y, screen_x, e.char, attr)
            except curses.error:
                pass
                
    for b in gs.bullets:
        if (b.x, b.y) in visible_area:
            try:
                screen_y = hud_height + (b.y - offset_y)
                screen_x = b.x - offset_x
                if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height) and screen_y < max_y:
                    color = 5 if not b.is_enemy_bullet else 14
                    stdscr.addch(screen_y, screen_x, b.char, curses.color_pair(color) | curses.A_BOLD)
            except curses.error:
                pass
    
    # NUEVO: Dibujar animaciones
    draw_animations(stdscr, gs, offset_x, offset_y, hud_height, visible_area)
                
    show_player = True
    if time.time() < gs.stunned_until:
        show_player = int(time.time() * 8) % 2 == 0
    elif gs.player.has_invincibility():
        show_player = int(time.time() * 12) % 2 == 0
        
    if (show_player and 
        (gs.player.x, gs.player.y) in visible_area):
        try:
            screen_y = hud_height + (gs.player.y - offset_y)
            screen_x = gs.player.x - offset_x
            if 0 <= screen_x < view_w and 0 <= screen_y < (view_h + hud_height) and screen_y < max_y:
                color = curses.color_pair(3)
                if gs.player.has_shield_buff():
                    color = curses.color_pair(10)
                elif gs.player.has_invincibility():
                    color = curses.color_pair(15)
                elif gs.player.has_speed():
                    color = curses.color_pair(16)
                    
                attr = color | curses.A_BOLD
                if gs.player.hp <= 1:
                    attr |= curses.A_BLINK
                    
                stdscr.addch(screen_y, screen_x, PLAYER_CHAR, attr)
        except curses.error:
            pass
            
    # HUD MEJORADO
    play_time = int(time.time() - gs.start_time)
    minutes = play_time // 60
    seconds = play_time % 60
    
    try:
        title = f"ESCAPE v0.9 - L{gs.level}"
        if 'SAFE' in gs.special_effects:
            title += " [SAFE]"
        elif 'GOD' in gs.special_effects:
            title += " [GOD]"
        elif 'SPEED' in gs.special_effects:
            title += " [SPEED]"
            
        if len(title) > max_x:
            title = title[:max_x]
        if 0 < max_y:
            stdscr.addstr(0, 0, title, curses.color_pair(1) | curses.A_BOLD)
    except curses.error:
        pass
    
    try:
        health_bar = "♥" * gs.player.hp + "♡" * (gs.player.max_hp - gs.player.hp)
        shield_indicator = " [S]" if gs.player.has_shield_buff() else ""
        ammo_info = f"A:{gs.player.ammo}"
        if 'GOD' in gs.special_effects:
            ammo_info = "A:∞"

        line2 = f"HP:{health_bar}{shield_indicator} {ammo_info}"
        if len(line2) > max_x:
            line2 = line2[:max_x]
        if 1 < max_y:
            stdscr.addstr(1, 0, line2, curses.color_pair(1))
    except curses.error:
        pass
    
    try:
        powerup_display = gs.player.active_powerup if gs.player.active_powerup else "None"
        powerup_text = f"Pwr:{powerup_display}"
        score_text = f"Scr:{gs.player.score}"

        line3 = f"{powerup_text} {score_text}"
        if len(line3) > max_x:
            line3 = line3[:max_x]
        if 2 < max_y:
            stdscr.addstr(2, 0, line3, curses.color_pair(1))
    except curses.error:
        pass
    
    try:
        time_text = f"Time:{minutes:02d}:{seconds:02d}"
        enemies_text = f"Enemies:{len(gs.enemies)}"
        seed_text = f"ID:{gs.seed[:6]}"

        line4 = f"{time_text} {enemies_text}"
        if len(line4) > max_x:
            line4 = line4[:max_x]
        if 3 < max_y:
            stdscr.addstr(3, 0, line4, curses.color_pair(1))
        
        line5 = f"{seed_text}"
        if len(line5) > max_x:
            line5 = line5[:max_x]
        if 4 < max_y:
            stdscr.addstr(4, 0, line5, curses.color_pair(1))
    except curses.error:
        pass
    
    try:
        controls = "Arrows/Wasd:Move QEZC:DiagShoot P:Pause"
        if len(controls) > max_x:
            controls = controls[:max_x]
        if 5 < max_y:
            stdscr.addstr(5, 0, controls, curses.color_pair(1))
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
    if not stdscr:
        return
        
    stdscr.nodelay(False)
    stdscr.erase()
    
    play_time = int(time.time() - gs.start_time)
    minutes = play_time // 60
    seconds = play_time % 60
    
    max_y, max_x = stdscr.getmaxyx()
    
    try:
        if 2 < max_y and 2 < max_x:
            stdscr.addstr(2, 2, "███████ VICTORY! ███████", curses.color_pair(1) | curses.A_BOLD)
        if 4 < max_y and 2 < max_x:
            stdscr.addstr(4, 2, "SYSTEM ESCAPED - TERMINAL RESTORED", curses.color_pair(1))
        if 6 < max_y and 2 < max_x:
            stdscr.addstr(6, 2, f"Final Score: {gs.player.score}", curses.color_pair(1))
        if 7 < max_y and 2 < max_x:
            stdscr.addstr(7, 2, f"Levels Completed: {gs.level}", curses.color_pair(1))
        if 8 < max_y and 2 < max_x:
            stdscr.addstr(8, 2, f"Time: {minutes:02d}:{seconds:02d}", curses.color_pair(1))
        if 10 < max_y and 2 < max_x:
            stdscr.addstr(10, 2, "Enemies Defeated:", curses.color_pair(1))
        if 11 < max_y and 4 < max_x:
            stdscr.addstr(11, 4, f"Basic: {gs.player.enemies_killed['normal']}", curses.color_pair(1))
        if 12 < max_y and 4 < max_x:
            stdscr.addstr(12, 4, f"Tanks: {gs.player.enemies_killed['tank']}", curses.color_pair(1))
        if 13 < max_y and 4 < max_x:
            stdscr.addstr(13, 4, f"Snipers: {gs.player.enemies_killed['sniper']}", curses.color_pair(1))
        if 15 < max_y and 2 < max_x:
            stdscr.addstr(15, 2, "Press ENTER to return to menu", curses.color_pair(1))
    except curses.error:
        pass
    
    # ESPERAR POR ENTER
    while True:
        key = stdscr.getch()
        if key in (10, 13):  # Enter key
            break

def show_game_over(stdscr, gs):
    if not stdscr:
        return
        
    stdscr.nodelay(False)
    stdscr.erase()
    
    play_time = int(time.time() - gs.start_time)
    minutes = play_time // 60
    seconds = play_time % 60
    
    max_y, max_x = stdscr.getmaxyx()
    
    try:
        if 2 < max_y and 2 < max_x:
            stdscr.addstr(2, 2, "SIGNAL LOST - GAME OVER", curses.color_pair(1) | curses.A_BOLD)
        if 4 < max_y and 2 < max_x:
            stdscr.addstr(4, 2, f"You reached level {gs.level}", curses.color_pair(1))
        if 5 < max_y and 2 < max_x:
            stdscr.addstr(5, 2, f"Final Score: {gs.player.score}", curses.color_pair(1))
        if 6 < max_y and 2 < max_x:
            stdscr.addstr(6, 2, f"Time: {minutes:02d}:{seconds:02d}", curses.color_pair(1))
        if 8 < max_y and 2 < max_x:
            stdscr.addstr(8, 2, "Enemies Defeated:", curses.color_pair(1))
        if 9 < max_y and 4 < max_x:
            stdscr.addstr(9, 4, f"Basic: {gs.player.enemies_killed['normal']}", curses.color_pair(1))
        if 10 < max_y and 4 < max_x:
            stdscr.addstr(10, 4, f"Tanks: {gs.player.enemies_killed['tank']}", curses.color_pair(1))
        if 11 < max_y and 4 < max_x:
            stdscr.addstr(11, 4, f"Snipers: {gs.player.enemies_killed['sniper']}", curses.color_pair(1))
        if 13 < max_y and 2 < max_x:
            stdscr.addstr(13, 2, "Press ENTER to return to menu", curses.color_pair(1))
    except curses.error:
        pass
    
    # ESPERAR POR ENTER
    while True:
        key = stdscr.getch()
        if key in (10, 13):  # Enter key
            break

def show_level_complete(stdscr, gs):
    if not stdscr:
        return
        
    stdscr.nodelay(False)
    stdscr.erase()
    
    max_y, max_x = stdscr.getmaxyx()
    
    try:
        if 2 < max_y and 2 < max_x:
            stdscr.addstr(2, 2, "LEVEL COMPLETE!", curses.color_pair(1) | curses.A_BOLD)
        if 4 < max_y and 2 < max_x:
            stdscr.addstr(4, 2, f"Enemies defeated this level: {gs.enemies_killed_this_level}", curses.color_pair(1))
        if 5 < max_y and 2 < max_x:
            stdscr.addstr(5, 2, f"Total score: {gs.player.score}", curses.color_pair(1))
        if gs.level % 2 == 0 and gs.player.max_hp < 5 and 7 < max_y and 2 < max_x:
            stdscr.addstr(7, 2, "MAX HEALTH INCREASED!", curses.color_pair(8) | curses.A_BOLD)
        if 9 < max_y and 2 < max_x:
            stdscr.addstr(9, 2, "Press ENTER to continue to next level", curses.color_pair(1))
    except curses.error:
        pass
    
    # ESPERAR POR ENTER
    while True:
        key = stdscr.getch()
        if key in (10, 13):  # Enter key
            break
    play_sound('level_up')

def show_tutorial(stdscr):
    if not stdscr:
        return
        
    stdscr.nodelay(False)
    stdscr.erase()
    
    pages = [
        [
            "CONTROLES BÁSICOS:",
            "",
            "MOVIMIENTO:",
            "  Flechas o WASD: Moverte",
            "  K/J/H/L: Movimiento estilo vi",
            "",
            "DISPARO:",
            "  WASD: Disparar en 4 direcciones",
            "  Q/E/Z/C: Disparo diagonal",
            "",
            "OTROS:",
            "  P: Pausa/Menú",
            "  ESC: Salir del juego",
            "",
            "Presiona cualquier tecla para continuar..."
        ],
        [
            "OBJETIVO DEL JUEGO:",
            "",
            "• Encuentra la salida (>) en cada nivel",
            "• Derrota enemigos para ganar puntos",
            "• Consigue power-ups para ventajas",
            "• Sobrevive hasta el nivel 10",
            "",
            "POWER-UPS:",
            "+ : Salud extra",
            "o : Munición",
            "U : UltraFuego (dispara através paredes)",
            "S : Escudo (protección extra)",
            "I : Invencibilidad temporal",
            "V : Velocidad aumentada",
            "",
            "Presiona cualquier tecla para continuar..."
        ],
        [
            "ENEMIGOS:",
            "",
            "E : Enemigo básico",
            "  - Se mueve hacia ti",
            "  - 1 punto de vida",
            "",
            "T : Tanque",
            "  - Más lento pero resistente",
            "  - 2 puntos de vida",
            "",
            "S : Francotirador", 
            "  - Dispara desde lejos",
            "  - Verifica línea de visión",
            "",
            "Presiona cualquier tecla para volver al menú..."
        ]
    ]
    
    current_page = 0
    while current_page < len(pages):
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            if 1 < max_y and 2 < max_x:
                stdscr.addstr(1, 2, "▄▄▄▄▄ CÓMO JUGAR ▄▄▄▄▄", curses.color_pair(1) | curses.A_BOLD)
            
            for i, line in enumerate(pages[current_page]):
                if 3 + i < max_y:
                    try:
                        if len(line) <= max_x:
                            stdscr.addstr(3 + i, 2, line, curses.color_pair(1))
                        else:
                            stdscr.addstr(3 + i, 2, line[:max_x-3] + "...", curses.color_pair(1))
                    except curses.error:
                        pass
                        
            if max_y > 20 and 2 < max_x:
                page_info = f"Página {current_page + 1}/{len(pages)}"
                try:
                    stdscr.addstr(max_y - 2, 2, page_info, curses.color_pair(1))
                except curses.error:
                    pass
                    
        except curses.error:
            pass
            
        stdscr.refresh()
        key = stdscr.getch()
        
        if key in (curses.KEY_RIGHT, ord('d'), ord('D'), ord(' '), ord('\n')):
            current_page += 1
        elif key in (curses.KEY_LEFT, ord('a'), ord('A')):
            current_page = max(0, current_page - 1)
        elif key == 27:
            break

# Menús mejorados para múltiples guardados
def new_game_menu(stdscr):
    """Menú para nueva partida con selección de slot"""
    curses.curs_set(0)
    options = []
    
    # Obtener slots disponibles
    empty_slots = save_manager.get_empty_slots()
    existing_saves = save_manager.list_saves()
    
    # Crear opciones
    for slot in range(1, MAX_SAVE_SLOTS + 1):
        if slot in empty_slots:
            options.append(f"Slot {slot}: [VACÍO]")
        else:
            # Buscar info del slot
            save_info = next((s for s in existing_saves if s['slot_number'] == slot), None)
            if save_info:
                options.append(f"Slot {slot}: Nvl {save_info['level']} - {save_info['score']} pts")
            else:
                options.append(f"Slot {slot}: [ERROR]")
    
    options.append("Volver al menú principal")
    
    selected = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            if 1 < max_y and 2 < max_x:
                stdscr.addstr(1, 2, "▄▄▄▄▄ NUEVA PARTIDA ▄▄▄▄▄", curses.color_pair(1) | curses.A_BOLD)
            if 3 < max_y and 2 < max_x:
                stdscr.addstr(3, 2, "Elige un slot de guardado:", curses.color_pair(1))
            
            for i, opt in enumerate(options):
                if 5 + i < max_y:
                    prefix = "> " if i == selected else "  "
                    try:
                        stdscr.addstr(5 + i, 4, prefix + opt, curses.color_pair(1))
                    except curses.error:
                        pass
            
            if max_y > 5 + len(options) + 2 and 2 < max_x:
                stdscr.addstr(5 + len(options) + 2, 2, "Enter: Seleccionar  ESC: Volver", curses.color_pair(1))
                
        except curses.error:
            pass
            
        stdscr.refresh()
        key = stdscr.getch()
        
        if key in (curses.KEY_UP, ord('w'), ord('W'), ord('k'), ord('K')):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S'), ord('j'), ord('J')):
            selected = (selected + 1) % len(options)
        elif key in (ord('\n'), ord('\r'), 10, 13):
            if selected == len(options) - 1:  # "Volver"
                return None, None
            else:
                slot_number = selected + 1
                # Si el slot está ocupado, confirmar sobrescritura
                if slot_number not in empty_slots:
                    if not confirm_overwrite(stdscr, slot_number):
                        continue
                return slot_number, None
        elif key == 27:
            return None, None
    
    return None, None

def confirm_overwrite(stdscr, slot_number):
    """Confirmar sobrescritura de partida existente"""
    curses.curs_set(0)
    options = ["Sí, sobrescribir", "No, cancelar"]
    selected = 1  # Por defecto seleccionar "No"
    
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            if 2 < max_y and 2 < max_x:
                stdscr.addstr(2, 2, "¡ADVERTENCIA!", curses.color_pair(1) | curses.A_BOLD)
            if 4 < max_y and 2 < max_x:
                stdscr.addstr(4, 2, f"El slot {slot_number} ya tiene una partida guardada.", curses.color_pair(1))
            if 5 < max_y and 2 < max_x:
                stdscr.addstr(5, 2, "¿Quieres sobrescribirla?", curses.color_pair(1))
            
            for i, opt in enumerate(options):
                if 7 + i < max_y:
                    prefix = "> " if i == selected else "  "
                    try:
                        stdscr.addstr(7 + i, 4, prefix + opt, curses.color_pair(1))
                    except curses.error:
                        pass
                        
        except curses.error:
            pass
            
        stdscr.refresh()
        key = stdscr.getch()
        
        if key in (curses.KEY_UP, ord('w'), ord('W'), ord('k'), ord('K')):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S'), ord('j'), ord('J')):
            selected = (selected + 1) % len(options)
        elif key in (ord('\n'), ord('\r'), 10, 13):
            return selected == 0
        elif key == 27:
            return False
    
    return False

def load_game_menu(stdscr):
    """Menú para cargar partida existente"""
    curses.curs_set(0)
    
    saves = save_manager.list_saves()
    if not saves:
        stdscr.erase()
        try:
            stdscr.addstr(2, 2, "No hay partidas guardadas.", curses.color_pair(1))
            stdscr.addstr(4, 2, "Presiona cualquier tecla para continuar", curses.color_pair(1))
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.getch()
        return None
    
    options = []
    for save in saves:
        play_time = save['play_time']
        minutes = play_time // 60
        seconds = play_time % 60
        options.append(f"Slot {save['slot_number']}: Nvl {save['level']} - {save['score']} pts - {minutes:02d}:{seconds:02d}")
    
    options.append("Cargar autoguardado")
    options.append("Volver al menú principal")
    
    selected = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            if 1 < max_y and 2 < max_x:
                stdscr.addstr(1, 2, "▄▄▄▄▄ CARGAR PARTIDA ▄▄▄▄▄", curses.color_pair(1) | curses.A_BOLD)
            if 3 < max_y and 2 < max_x:
                stdscr.addstr(3, 2, "Elige una partida guardada:", curses.color_pair(1))
            
            for i, opt in enumerate(options):
                if 5 + i < max_y:
                    prefix = "> " if i == selected else "  "
                    try:
                        stdscr.addstr(5 + i, 4, prefix + opt, curses.color_pair(1))
                    except curses.error:
                        pass
            
            if max_y > 5 + len(options) + 2 and 2 < max_x:
                stdscr.addstr(5 + len(options) + 2, 2, "Enter: Cargar  D: Eliminar  ESC: Volver", curses.color_pair(1))
                
        except curses.error:
            pass
            
        stdscr.refresh()
        key = stdscr.getch()
        
        if key in (curses.KEY_UP, ord('w'), ord('W'), ord('k'), ord('K')):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S'), ord('j'), ord('J')):
            selected = (selected + 1) % len(options)
        elif key in (ord('\n'), ord('\r'), 10, 13):
            if selected == len(options) - 1:  # "Volver"
                return None
            elif selected == len(options) - 2:  # "Cargar autoguardado"
                game_state, message = load_game("autosave")
                if game_state:
                    return game_state
                else:
                    # Mostrar error
                    stdscr.erase()
                    try:
                        stdscr.addstr(2, 2, f"Error: {message}", curses.color_pair(1))
                        stdscr.addstr(4, 2, "Presiona cualquier tecla para continuar", curses.color_pair(1))
                    except curses.error:
                        pass
                    stdscr.refresh()
                    stdscr.getch()
                    continue
            else:
                slot_number = saves[selected]['slot_number']
                game_state, message = load_game(slot_number)
                if game_state:
                    return game_state
                else:
                    # Mostrar error
                    stdscr.erase()
                    try:
                        stdscr.addstr(2, 2, f"Error: {message}", curses.color_pair(1))
                        stdscr.addstr(4, 2, "Presiona cualquier tecla para continuar", curses.color_pair(1))
                    except curses.error:
                        pass
                    stdscr.refresh()
                    stdscr.getch()
                    continue
        elif key in (ord('d'), ord('D')):
            if selected < len(saves):
                slot_number = saves[selected]['slot_number']
                if confirm_delete(stdscr, slot_number):
                    success, message = save_manager.delete_save(slot_number)
                    # Actualizar lista
                    saves = save_manager.list_saves()
                    if not saves:
                        return None
                    options = []
                    for save in saves:
                        play_time = save['play_time']
                        minutes = play_time // 60
                        seconds = play_time % 60
                        options.append(f"Slot {save['slot_number']}: Nvl {save['level']} - {save['score']} pts - {minutes:02d}:{seconds:02d}")
                    options.append("Cargar autoguardado")
                    options.append("Volver al menú principal")
                    selected = min(selected, len(options) - 1)
        elif key == 27:
            return None
    
    return None

def confirm_delete(stdscr, slot_number):
    """Confirmar eliminación de partida"""
    curses.curs_set(0)
    options = ["Sí, eliminar", "No, cancelar"]
    selected = 1  # Por defecto seleccionar "No"
    
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            if 2 < max_y and 2 < max_x:
                stdscr.addstr(2, 2, "¡CONFIRMAR ELIMINACIÓN!", curses.color_pair(1) | curses.A_BOLD | curses.A_BLINK)
            if 4 < max_y and 2 < max_x:
                stdscr.addstr(4, 2, f"¿Eliminar partida del slot {slot_number}?", curses.color_pair(1))
            if 5 < max_y and 2 < max_x:
                stdscr.addstr(5, 2, "Esta acción no se puede deshacer.", curses.color_pair(1))
            
            for i, opt in enumerate(options):
                if 7 + i < max_y:
                    prefix = "> " if i == selected else "  "
                    try:
                        stdscr.addstr(7 + i, 4, prefix + opt, curses.color_pair(1))
                    except curses.error:
                        pass
                        
        except curses.error:
            pass
            
        stdscr.refresh()
        key = stdscr.getch()
        
        if key in (curses.KEY_UP, ord('w'), ord('W'), ord('k'), ord('K')):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S'), ord('j'), ord('J')):
            selected = (selected + 1) % len(options)
        elif key in (ord('\n'), ord('\r'), 10, 13):
            return selected == 0
        elif key == 27:
            return False
    
    return False

def menu(stdscr):
    curses.curs_set(0)
    options = ["Nueva partida", "Cargar partida", "Cómo jugar", "Salir"]
    selected = 0
    
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        stdscr.attron(curses.color_pair(1))
        try:
            title = "███████ ESCAPE THE TERMINAL ███████"
            if len(title) > max_x:
                title = title[:max_x]
            
            if 0 < max_y:
                stdscr.addstr(0, 0, title, curses.color_pair(1) | curses.A_BOLD)
            
            credit = "By: Dragon56YT - v0.9-beta"
            if 1 < max_y and len(credit) <= max_x:
                stdscr.addstr(1, 0, credit, curses.color_pair(1))
        except curses.error:
            pass
        
        for i, opt in enumerate(options):
            if 4 + i < max_y:
                prefix = "> " if i == selected else "  "
                try:
                    stdscr.addstr(4 + i, 2, prefix + opt, curses.color_pair(1))
                except curses.error:
                    pass
        
        try:
            if 9 < max_y and 2 < max_x:
                stdscr.addstr(9, 2, "Use arrow keys and Enter", curses.color_pair(1))
        except curses.error:
            pass
            
        stdscr.attroff(curses.color_pair(1))
        stdscr.refresh()
        
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('w'), ord('W'), ord('k'), ord('K')):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S'), ord('j'), ord('J')):
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
        if 2 < max_y and 2 < max_x:
            stdscr.addstr(2, 2, "███████ NEW GAME ███████", curses.color_pair(1) | curses.A_BOLD)
        if 4 < max_y and 2 < max_x:
            stdscr.addstr(4, 2, "Enter seed (leave blank for random): ", curses.color_pair(1))
        if 6 < max_y and 2 < max_x:
            stdscr.addstr(6, 2, "Secret seeds: SAFE, GOD, SPEED", curses.color_pair(1))
        if 8 < max_y and 2 < max_x:
            stdscr.addstr(8, 2, "Press ESC to return to main menu", curses.color_pair(1))
    except curses.error:
        pass
        
    stdscr.refresh()
    
    input_x = 40
    if 4 < max_y:
        stdscr.move(4, min(input_x, max_x-1))
    
    try:
        max_input_len = min(20, max_x - input_x) if max_x > input_x else 0
        input_str = ""
        
        if max_input_len > 0:
            while True:
                if 4 < max_y:
                    stdscr.move(4, min(input_x + len(input_str), max_x-1))
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
                        if 4 < max_y and input_x + len(input_str) < max_x:
                            stdscr.addch(4, input_x + len(input_str), ' ')
                            stdscr.move(4, min(input_x + len(input_str), max_x-1))
                elif len(input_str) < max_input_len and 32 <= ch <= 126:
                    input_str += chr(ch)
                    if 4 < max_y and input_x + len(input_str) - 1 < max_x:
                        stdscr.addch(4, input_x + len(input_str) - 1, chr(ch))
    except Exception:
        input_str = ""
        
    curses.curs_set(0)
    curses.noecho()
    
    return input_str

# Menú de pausa mejorado
def pause_menu(stdscr, gs):
    curses.curs_set(0)
    options = ["Continuar", "Guardar partida", "Cargar partida", "Cómo jugar", "Salir al menu"]
    sel = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            if 2 < max_y and 2 < max_x:
                stdscr.addstr(2, 2, "-- PAUSA --", curses.color_pair(1) | curses.A_BOLD)
            for i, o in enumerate(options):
                if 4 + i < max_y:
                    prefix = "> " if i == sel else "  "
                    try:
                        stdscr.addstr(4 + i, 4, prefix + o, curses.color_pair(1))
                    except curses.error:
                        pass
            
            if 10 < max_y and 4 < max_x:
                stdscr.addstr(10, 4, "Flechas para navegar, Enter para seleccionar", curses.color_pair(1))
        except curses.error:
            pass
        
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (curses.KEY_UP, ord('w'), ord('W'), ord('k'), ord('K')):
            sel = (sel - 1) % len(options)
        elif ch in (curses.KEY_DOWN, ord('s'), ord('S'), ord('j'), ord('J')):
            sel = (sel + 1) % len(options)
        elif ch in (10, 13):
            choice = options[sel]
            if choice == 'Continuar':
                return 'continue'
            if choice == 'Guardar partida':
                save_result = save_game_submenu(stdscr, gs)
                if save_result == 'continue':
                    return 'continue'
                elif save_result == 'back':
                    continue
            if choice == 'Cargar partida':
                loaded = load_game_menu(stdscr)
                if loaded:
                    return ('load', loaded)
                else:
                    continue
            if choice == 'Cómo jugar':
                show_tutorial(stdscr)
                continue
            if choice == 'Salir al menu':
                return 'menu'
        elif ch == 27:
            return 'continue'

def save_game_submenu(stdscr, gs):
    """Submenú para guardar partida"""
    curses.curs_set(0)
    
    if gs.current_save_slot:
        options = [
            f"Guardar en slot actual ({gs.current_save_slot})",
            "Guardar en nuevo slot",
            "Autoguardado rápido",
            "Volver"
        ]
    else:
        options = [
            "Guardar en nuevo slot",
            "Autoguardado rápido", 
            "Volver"
        ]
    
    sel = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        
        try:
            if 2 < max_y and 2 < max_x:
                stdscr.addstr(2, 2, "-- GUARDAR PARTIDA --", curses.color_pair(1) | curses.A_BOLD)
            
            for i, opt in enumerate(options):
                if 4 + i < max_y:
                    prefix = "> " if i == sel else "  "
                    try:
                        stdscr.addstr(4 + i, 4, prefix + opt, curses.color_pair(1))
                    except curses.error:
                        pass
                        
        except curses.error:
            pass
            
        stdscr.refresh()
        ch = stdscr.getch()
        
        if ch in (curses.KEY_UP, ord('w'), ord('W'), ord('k'), ord('K')):
            sel = (sel - 1) % len(options)
        elif ch in (curses.KEY_DOWN, ord('s'), ord('S'), ord('j'), ord('J')):
            sel = (sel + 1) % len(options)
        elif ch in (10, 13):
            if gs.current_save_slot:
                if sel == 0:  # Guardar en slot actual
                    success, message = save_game(gs, gs.current_save_slot)
                    show_message(stdscr, message, success)
                    return 'continue'
                elif sel == 1:  # Guardar en nuevo slot
                    slot_number, save_name = new_game_menu(stdscr)
                    if slot_number:
                        success, message = save_game(gs, slot_number, save_name)
                        show_message(stdscr, message, success)
                        return 'continue'
                    else:
                        continue
                elif sel == 2:  # Autoguardado
                    success, message = autosave_game(gs)
                    show_message(stdscr, message, success)
                    return 'continue'
                else:  # Volver
                    return 'back'
            else:
                if sel == 0:  # Guardar en nuevo slot
                    slot_number, save_name = new_game_menu(stdscr)
                    if slot_number:
                        success, message = save_game(gs, slot_number, save_name)
                        show_message(stdscr, message, success)
                        return 'continue'
                    else:
                        continue
                elif sel == 1:  # Autoguardado
                    success, message = autosave_game(gs)
                    show_message(stdscr, message, success)
                    return 'continue'
                else:  # Volver
                    return 'back'
        elif ch == 27:
            return 'back'
    
    return 'back'

def show_message(stdscr, message, is_success=True):
    """Mostrar mensaje temporal"""
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    
    try:
        color = curses.color_pair(8) if is_success else curses.color_pair(4)  # Verde o Rojo
        if 2 < max_y and 2 < max_x:
            stdscr.addstr(2, 2, message, color)
        if 4 < max_y and 2 < max_x:
            stdscr.addstr(4, 2, "Presiona cualquier tecla para continuar", curses.color_pair(1))
    except curses.error:
        pass
        
    stdscr.refresh()
    stdscr.getch()

def apply_damage_stun(gs):
    if gs:
        gs.stunned_until = time.time() + DAMAGE_STUN_DURATION

def run_game(stdscr, gs):
    if not stdscr or not gs:
        return
        
    stdscr.nodelay(True)
    last_time = time.time()
    tick = 0
    gs._last_key = None
    gs._next_repeat_time = 0.0

    target_fps = 30
    frame_duration = 1.0 / target_fps

    # Autoguardado al iniciar nivel
    if gs.current_save_slot:
        autosave_game(gs)

    while True:
        current_time = time.time()
        elapsed = current_time - last_time
        
        if elapsed < frame_duration:
            time.sleep(frame_duration - elapsed)
            continue
            
        last_time = current_time
        tick += 1

        if tick % 60 == 0:
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
                    # PARCHÉ: Reset del sistema de repetición para teclas no de movimiento
                    gs._last_key = None
                    gs._next_repeat_time = 0.0
        else:
            if gs._last_key is not None and current_time > gs._next_repeat_time + 0.5:
                gs._last_key = None

        if move_delta:
            steps = 2 if gs.player.has_speed() or 'SPEED' in gs.special_effects else 1
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
            # Autoguardado al completar nivel
            if gs.current_save_slot:
                autosave_game(gs)
                
            gs.player.score += 1000 * gs.level
            gs.level += 1
            if gs.level > MAX_LEVEL:
                show_victory_screen(stdscr, gs)
                return
            show_level_complete(stdscr, gs)
            gs.new_level()
            
            # Autoguardado después de nuevo nivel
            if gs.current_save_slot:
                autosave_game(gs)

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
            loaded = load_game_menu(stdscr)
            if loaded:
                gs = loaded
                run_game(stdscr, gs)
        elif choice == 'Cómo jugar':
            show_tutorial(stdscr)
        elif choice == 'Nueva partida':
            slot_number, save_name = new_game_menu(stdscr)
            if slot_number:
                seed_input = prompt_seed(stdscr)
                if seed_input is None:
                    continue
                seed = seed_input if seed_input != "" else None
                gs = GameState(level=1, seed=seed)
                gs.current_save_slot = slot_number
                gs.new_level()
                run_game(stdscr, gs)

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n¡Juego interrumpido! Gracias por jugar.")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
