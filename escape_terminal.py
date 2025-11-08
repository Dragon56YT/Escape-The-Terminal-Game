"""
Escape the Terminal - single-file Python roguelike for the terminal

How to run:
  - Linux / macOS: python3 escape_terminal.py
  - Windows:  pip install windows-curses
             python escape_terminal.py

Controls (default):
  Movement: WASD or arrow keys
  Shoot: I (up), K (down), J (left), L (right)
  Save: p
  Quit to menu: q (in-game)
  Menu navigation: Up/Down arrows, Enter

This implementation improves robustness and correctness:
- Uses a dedicated RNG per GameState (no global reseeding)
- Safer save/load with validation and error handling
- Avoids KeyErrors and set remove errors using discard
- Drawing clamps to terminal size to avoid curses exceptions
- Fixes edge cases in enemy movement occupancy handling

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
    "EXIT NODE DETECTED"
]

WALL = '#'
FLOOR = '.'
PLAYER_CHAR = '@'
ENEMY_CHAR = 'e'
BULLET_CHAR = '*'
AMMO_CHAR = 'o'
EXIT_CHAR = '>'

MOVE_KEYS = {
    ord('w'):-1j, ord('W'):-1j,
    ord('s'):1j, ord('S'):1j,
    ord('a'):-1, ord('A'):-1,
    ord('d'):1, ord('D'):1
}
SHOOT_KEYS = {
    ord('i'):-1j, ord('I'):-1j,
    ord('k'):1j, ord('K'):1j,
    ord('j'):-1, ord('J'):-1,
    ord('l'):1, ord('L'):1
}

ARROW_KEYS = {
    curses.KEY_UP:-1j,
    curses.KEY_DOWN:1j,
    curses.KEY_LEFT:-1,
    curses.KEY_RIGHT:1
}


def to_xy(pos):
    return int(pos.real), int(pos.imag)


class GameMap:
    def __init__(self, width, height, walls=None):
        self.width = width
        self.height = height
        self.walls = set(walls) if walls else set()

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_wall(self, x, y):
        return (x, y) in self.walls

    def neighbors(self, x, y):
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if self.in_bounds(nx, ny) and not self.is_wall(nx, ny):
                yield nx, ny

    def to_grid(self):
        grid = [[FLOOR for _ in range(self.width)] for __ in range(self.height)]
        for (wx, wy) in self.walls:
            if 0 <= wy < self.height and 0 <= wx < self.width:
                grid[wy][wx] = WALL
        return grid

    def random_floor_positions(self):
        for y in range(self.height):
            for x in range(self.width):
                if not self.is_wall(x,y):
                    yield x,y

    def serialize(self):
        return {'width': self.width, 'height': self.height, 'walls': list(self.walls)}

    @staticmethod
    def deserialize(data):
        w = data.get('width')
        h = data.get('height')
        walls = [tuple(wi) for wi in data.get('walls', [])]
        return GameMap(w, h, walls=walls)


def ensure_path(width, height, wall_chance, rng, max_tries=300):
    for _ in range(max_tries):
        walls = set()
        for y in range(height):
            for x in range(width):
                if x==0 or y==0 or x==width-1 or y==height-1:
                    walls.add((x,y))
                else:
                    if rng.random() < wall_chance:
                        walls.add((x,y))
        sx, sy = 1, 1
        ex, ey = width-2, height-2
        walls.discard((sx,sy))
        walls.discard((ex,ey))
        gm = GameMap(width, height, walls=walls)
        if is_reachable(gm, (sx,sy), (ex,ey)):
            return gm, (sx,sy), (ex,ey)
    gm = GameMap(width, height, walls=set())
    return gm, (1,1), (width-2, height-2)


def is_reachable(gm, start, goal):
    sx, sy = start
    gx, gy = goal
    if gm.is_wall(sx,sy) or gm.is_wall(gx,gy):
        return False
    q = deque([ (sx,sy) ])
    seen = { (sx,sy) }
    while q:
        x,y = q.popleft()
        if (x,y) == (gx,gy):
            return True
        for nx, ny in gm.neighbors(x,y):
            if (nx,ny) not in seen:
                seen.add((nx,ny))
                q.append((nx,ny))
    return False


class Player:
    def __init__(self, x, y, hp=3, ammo=5):
        self.x = int(x)
        self.y = int(y)
        self.hp = int(hp)
        self.ammo = int(ammo)

    def pos(self):
        return (self.x, self.y)

    def serialize(self):
        return {'x': self.x, 'y': self.y, 'hp': self.hp, 'ammo': self.ammo}

    @staticmethod
    def deserialize(d):
        return Player(d['x'], d['y'], hp=d.get('hp',3), ammo=d.get('ammo',0))


class Enemy:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def pos(self):
        return (self.x, self.y)

    def serialize(self):
        return {'x': self.x, 'y': self.y}

    @staticmethod
    def deserialize(d):
        return Enemy(d['x'], d['y'])


class Bullet:
    def __init__(self, x, y, dx, dy):
        self.x = int(x)
        self.y = int(y)
        self.dx = int(dx)
        self.dy = int(dy)

    def pos(self):
        return (self.x, self.y)

    def step(self):
        self.x += self.dx
        self.y += self.dy

    def serialize(self):
        return {'x': self.x, 'y': self.y, 'dx': self.dx, 'dy': self.dy}

    @staticmethod
    def deserialize(d):
        return Bullet(d['x'], d['y'], d['dx'], d['dy'])


class GameState:
    def __init__(self, level=1, seed=None):
        self.level = int(level)
        self.seed = seed or str(random.randint(0, 10**9))
        self.rng = random.Random(self.seed)
        self.map = None
        self.player = None
        self.enemies = []
        self.bullets = []
        self.ammos = []
        self.exit = None
        self.lore_message = None
        self.special_effects = set()

    def new_level(self):
        base_w, base_h = 30, 16
        w = min(80, base_w + (self.level-1)*2)
        h = min(40, base_h + (self.level-1)*1)
        wall_chance = min(0.22 + (self.level-1)*0.01, 0.35)
        self.map, start, exitpos = ensure_path(w, h, wall_chance, self.rng)
        self.exit = exitpos
        self.player = Player(start[0], start[1], hp=3, ammo=5)
        self.apply_seed_effects_on_start()
        enemy_count = 3 + max(0, (self.level-1))
        if 'SAFE' in self.special_effects:
            enemy_count = max(1, enemy_count - 2)
        floor_positions = list(self.map.random_floor_positions())
        self.rng.shuffle(floor_positions)
        floor_positions = [p for p in floor_positions if p != start and p != exitpos]
        self.enemies = []
        for _ in range(enemy_count):
            if not floor_positions:
                break
            x,y = floor_positions.pop()
            self.enemies.append(Enemy(x,y))
        ammo_count = max(1, 2 + self.level//2)
        self.ammos = []
        for _ in range(ammo_count):
            if not floor_positions:
                break
            x,y = floor_positions.pop()
            self.ammos.append((int(x), int(y)))
        self.bullets = []
        self.lore_message = self.rng.choice(LORE_LINES)

    def apply_seed_effects_on_start(self):
        s = (self.seed or '').upper()
        if s == 'H4CK3R':
            self.player.ammo += 8
            self.special_effects.add('H4CK3R')
        if s == 'ADMIN':
            self.special_effects.add('ADMIN')
        if s == 'SAFE':
            self.special_effects.add('SAFE')
        if s == 'MATRIX':
            self.special_effects.add('MATRIX')
        if s == 'GOD':
            self.player.hp = 999
            self.special_effects.add('GOD')

    def serialize(self):
        return {
            'level': self.level,
            'seed': self.seed,
            'map': self.map.serialize() if self.map else None,
            'player': self.player.serialize() if self.player else None,
            'enemies': [e.serialize() for e in self.enemies],
            'bullets': [b.serialize() for b in self.bullets],
            'ammos': list(self.ammos),
            'exit': list(self.exit) if self.exit else None,
            'lore_message': self.lore_message,
            'special_effects': list(self.special_effects)
        }

    @staticmethod
    def deserialize(d):
        if not isinstance(d, dict):
            raise ValueError('Invalid save data')
        gs = GameState(level=d.get('level',1), seed=d.get('seed'))
        if d.get('map'):
            gs.map = GameMap.deserialize(d['map'])
        if d.get('player'):
            gs.player = Player.deserialize(d['player'])
        gs.enemies = [Enemy.deserialize(ed) for ed in d.get('enemies', [])]
        gs.bullets = [Bullet.deserialize(bd) for bd in d.get('bullets', [])]
        gs.ammos = [tuple(a) for a in d.get('ammos', [])]
        gs.exit = tuple(d['exit']) if d.get('exit') else None
        gs.lore_message = d.get('lore_message')
        gs.special_effects = set(d.get('special_effects', []))
        return gs


def save_game(gs):
    data = gs.serialize()
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception:
        return False


def load_game():
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
        gs = GameState.deserialize(data)
        return gs
    except Exception:
        return None


def move_player(gs, dx, dy):
    nx, ny = gs.player.x + int(dx), gs.player.y + int(dy)
    if not gs.map.in_bounds(nx, ny):
        return
    if gs.map.is_wall(nx, ny):
        return
    for e in list(gs.enemies):
        if (nx, ny) == (e.x, e.y):
            gs.player.hp -= 1
            gs.enemies.remove(e)
            return
    gs.player.x, gs.player.y = nx, ny
    if (nx, ny) in gs.ammos:
        try:
            gs.ammos.remove((nx, ny))
            gs.player.ammo += 3
        except ValueError:
            pass


def fire_bullet(gs, dx, dy):
    if gs.player.ammo <= 0:
        return
    gs.player.ammo -= 1
    b = Bullet(gs.player.x, gs.player.y, int(dx), int(dy))
    gs.bullets.append(b)


def step_bullets(gs):
    enemy_pos_map = { (e.x,e.y): e for e in gs.enemies }
    new_bullets = []
    for b in gs.bullets:
        b.step()
        if not gs.map.in_bounds(b.x, b.y):
            continue
        if gs.map.is_wall(b.x, b.y):
            continue
        if (b.x, b.y) in enemy_pos_map:
            e = enemy_pos_map[(b.x,b.y)]
            try:
                gs.enemies.remove(e)
            except ValueError:
                pass
            continue
        new_bullets.append(b)
    gs.bullets = new_bullets


def enemy_detects_player(e, gs, radius=6):
    dx = gs.player.x - e.x
    dy = gs.player.y - e.y
    return (dx*dx + dy*dy) <= radius*radius


def can_enemy_move_to(gs, nx, ny, occupied):
    if not gs.map.in_bounds(nx, ny):
        return False
    if gs.map.is_wall(nx, ny):
        return False
    if (nx, ny) in occupied:
        return False
    return True


def try_random_enemy_move(e, gs, occupied):
    dirs = [(1,0),(-1,0),(0,1),(0,-1),(0,0)]
    gs.rng.shuffle(dirs)
    for dx,dy in dirs:
        nx, ny = e.x+dx, e.y+dy
        if can_enemy_move_to(gs, nx, ny, occupied):
            if (nx, ny) != (e.x, e.y):
                occupied.discard((e.x, e.y))
                e.x, e.y = nx, ny
                occupied.add((e.x, e.y))
            return


def move_enemies(gs):
    occupied = set((e.x,e.y) for e in gs.enemies)
    for e in list(gs.enemies):
        detected = enemy_detects_player(e, gs, radius=6)
        if detected:
            dx = gs.player.x - e.x
            dy = gs.player.y - e.y
            sx = 0 if dx==0 else (1 if dx>0 else -1)
            sy = 0 if dy==0 else (1 if dy>0 else -1)
            choices = [(sx,0),(0,sy)]
            gs.rng.shuffle(choices)
            moved = False
            for dxm, dym in choices:
                nx, ny = e.x+dxm, e.y+dym
                if can_enemy_move_to(gs, nx, ny, occupied):
                    occupied.discard((e.x, e.y))
                    e.x, e.y = nx, ny
                    occupied.add((e.x, e.y))
                    moved = True
                    break
            if not moved:
                try_random_enemy_move(e, gs, occupied)
        else:
            try_random_enemy_move(e, gs, occupied)
        if (e.x, e.y) == (gs.player.x, gs.player.y):
            gs.player.hp -= 1
            try:
                gs.enemies.remove(e)
            except ValueError:
                pass


def draw_game(stdscr, gs, offset_y=2, offset_x=0):
    stdscr.erase()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()
    grid = gs.map.to_grid()
    view_h = min(gs.map.height, max_y - offset_y - 3)
    view_w = min(gs.map.width, max_x - offset_x - 1)
    for y in range(view_h):
        for x in range(view_w):
            try:
                ch = grid[y][x]
                stdscr.addch(offset_y + y, offset_x + x, ch)
            except curses.error:
                pass
    for (ax, ay) in gs.ammos:
        if 0 <= ay < view_h and 0 <= ax < view_w:
            try:
                stdscr.addch(offset_y + ay, offset_x + ax, AMMO_CHAR)
            except curses.error:
                pass
    if gs.exit:
        ex, ey = gs.exit
        if 0 <= ey < view_h and 0 <= ex < view_w:
            try:
                stdscr.addch(offset_y + ey, offset_x + ex, EXIT_CHAR)
            except curses.error:
                pass
    for e in gs.enemies:
        if 0 <= e.y < view_h and 0 <= e.x < view_w:
            try:
                stdscr.addch(offset_y + e.y, offset_x + e.x, ENEMY_CHAR)
            except curses.error:
                pass
    for b in gs.bullets:
        if 0 <= b.y < view_h and 0 <= b.x < view_w:
            try:
                stdscr.addch(offset_y + b.y, offset_x + b.x, BULLET_CHAR)
            except curses.error:
                pass
    if 0 <= gs.player.y < view_h and 0 <= gs.player.x < view_w:
        try:
            stdscr.addch(offset_y + gs.player.y, offset_x + gs.player.x, PLAYER_CHAR)
        except curses.error:
            pass
    hud = f"HP: {gs.player.hp}   AMMO: {gs.player.ammo}   LEVEL: {gs.level}   SEED: {gs.seed}"
    try:
        stdscr.addstr(0, 0, "ESCAPE THE TERMINAL")
        stdscr.addstr(1, 0, hud)
        if gs.lore_message:
            stdscr.addstr(offset_y + view_h + 1, 0, f"> {gs.lore_message}")
    except curses.error:
        pass
    stdscr.refresh()


def menu(stdscr):
    curses.curs_set(0)
    options = ["Nueva partida", "Cargar partida", "Salir"]
    selected = 0
    while True:
        stdscr.erase()
        stdscr.attron(curses.color_pair(1))
        try:
            stdscr.addstr(0, 0, "███████ ESCAPE THE TERMINAL ███████")
        except curses.error:
            pass
        for i, opt in enumerate(options):
            prefix = "> " if i == selected else "  "
            try:
                stdscr.addstr(2 + i, 2, prefix + opt)
            except curses.error:
                pass
        stdscr.attroff(curses.color_pair(1))
        stdscr.refresh()
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('w')):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('s')):
            selected = (selected + 1) % len(options)
        elif key in (ord('\n'), ord('\r'), 10, 13):
            return options[selected]


def prompt_seed(stdscr):
    curses.echo()
    stdscr.addstr(6, 2, "Enter seed (or leave blank for random): ")
    stdscr.refresh()
    try:
        s = stdscr.getstr(6, 36, 32).decode('utf-8')
    except Exception:
        s = ''
    curses.noecho()
    return s.strip() or None


def run_game(stdscr, gs):
    stdscr.nodelay(True)
    last_time = time.time()
    tick = 0
    while True:
        now = time.time()
        elapsed = now - last_time
        if elapsed < 0.03:
            time.sleep(0.005)
            continue
        last_time = now
        tick += 1
        try:
            key = stdscr.getch()
        except Exception:
            key = -1
        if key != -1:
            if key in MOVE_KEYS or key in ARROW_KEYS:
                delta = MOVE_KEYS.get(key) if key in MOVE_KEYS else ARROW_KEYS.get(key)
                dx, dy = int(delta.real), int(delta.imag)
                move_player(gs, dx, dy)
            elif key in SHOOT_KEYS:
                delta = SHOOT_KEYS[key]
                dx, dy = int(delta.real), int(delta.imag)
                fire_bullet(gs, dx, dy)
            elif key == ord('p'):
                save_game(gs)
            elif key == ord('q'):
                stdscr.nodelay(False)
                return
            elif key == ord('='):
                gs.level += 1
                gs.new_level()
        step_bullets(gs)
        move_interval = 6
        if 'ADMIN' in gs.special_effects:
            move_interval = max(2, move_interval - 2)
        if tick % move_interval == 0:
            move_enemies(gs)
        if gs.exit and (gs.player.x, gs.player.y) == gs.exit:
            gs.level += 1
            gs.new_level()
        if gs.player.hp <= 0:
            stdscr.nodelay(False)
            stdscr.erase()
            try:
                stdscr.addstr(2, 2, "SIGNAL LOST - GAME OVER")
                stdscr.addstr(4, 2, f"You reached level {gs.level}")
                stdscr.addstr(6, 2, "Press any key to return to menu")
            except curses.error:
                pass
            stdscr.getch()
            return
        draw_game(stdscr, gs)


def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    while True:
        choice = menu(stdscr)
        if choice == 'Salir' or choice == 'Exit':
            break
        elif choice == 'Cargar partida' or choice == 'Load game':
            loaded = load_game()
            if not loaded:
                stdscr.erase()
                try:
                    stdscr.addstr(2,2, "No saved game found.")
                    stdscr.addstr(4,2, "Press any key to continue")
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
            stdscr.erase()
            try:
                stdscr.addstr(2,2, "Starting new game")
            except curses.error:
                pass
            seed = prompt_seed(stdscr)
            gs = GameState(level=1, seed=seed)
            gs.new_level()
            run_game(stdscr, gs)


if __name__ == '__main__':
    curses.wrapper(main)
