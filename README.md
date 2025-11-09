\# Escape the Terminal

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)

![License](https://img.shields.io/badge/license-MIT-green)

\*\*Escape the Terminal\*\* es un roguelike de un solo archivo para la terminal, escrito en Python. Enfréntate a enemigos, recoge munición y alcanza la salida mientras avanzas por niveles generados proceduralmente.

\---

\## 🎮 Controles

- \*\*Movimiento:\*\* `WASD` o flechas
- \*\*Disparar:\*\*
- Arriba: `I`
- Abajo: `K`
- Izquierda: `J`
- Derecha: `L`
- \*\*Guardar partida:\*\* `P`
- \*\*Salir al menú:\*\* `Q` (en el juego)
- \*\*Menú:\*\* flechas `↑↓` + `Enter`

\---

\## 🚀 Cómo ejecutar

\### Linux / macOS

\```bash

python3 escape\_terminal.py

Windows

pip install windows-curses

python escape\_terminal.py


Nota: En Windows, curses no está incluido por defecto, por eso se requiere windows-curses.

🆕 Características

Generación procedural de niveles con garantía de camino entre inicio y salida.

Enemigos con detección de jugador y movimiento inteligente.

Proyectiles que interactúan con enemigos y paredes.

Semilla (seed) personalizable para efectos especiales:

H4CK3R: munición extra.

ADMIN: enemigos más rápidos.

SAFE: menos enemigos iniciales.

MATRIX: efecto visual/temático.

GOD: HP del jugador extremadamente alto.

HUD con HP, munición, nivel y seed actual.

Mensajes de lore aleatorios por nivel.

Guardado y carga de partidas seguros en JSON.


📦 Archivos Generados

escape\_terminal.py – juego principal en un solo archivo.

escape\_terminal\_save.json – archivo de guardado automático (creado al guardar).

📄 Licencia

Este proyecto es open-source y puede modificarse libremente.

✨ Créditos

Desarrollo original por Dragon56
