# Escape The Terminal

![Python](https://img.shields.io/badge/Python-3.6%2B%20(min)%20|%203.13%2B%20(recommended)-blue)
![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-red)
![Version](https://img.shields.io/badge/version-v0.10--beta-yellow)

**Escape the Terminal** es un roguelike de un solo archivo para la terminal, escrito en Python.  
Enfréntate a múltiples tipos de enemigos, recoge power-ups y munición, y alcanza la salida mientras avanzas por niveles generados proceduralmente.

---

## 🎮 Controles

| Acción            | Teclas              |
|------------------|---------------------|
| **Movimiento**    | Flechas (↑↓←→)      |
| **Disparar ↑**    | `W`                 |
| **Disparar ↓**    | `S`                 |
| **Disparar ←**    | `A`                 |
| **Disparar →**    | `D`                 |
| **Pausa/Menú**    | `P`                 |
| **Navegar menús** | Flechas + `Enter`   |

---

# 🚀 Cómo ejecutar
- Windows:
```bash
pip install windows-curses
````
```bash
python escape_terminal.py
````
- Linux/ macOS
```bash
python escape_terminal.py
````
## Compatibilidad

- Windows / Linux / macOS

- Compatible con Python 3.6+ mínimo

- Requiere terminal con soporte para colores y curses

- En windows es necesario tener instalado `windows-curses`
---
# ✨ Características Principales
- 3 tipos de enemigos con comportamientos únicos:

  - Básicos (E): Movimiento estándar

  - Tanques (T): 2 puntos de vida, más lentos

  - Francotiradores (S): Disparan a distancia

# 🔋 Sistema de Power-ups
- 4 tipos de power-ups con efectos temporales:

  - Salud (+): Restaura 1 punto de vida

  - Ráfaga (R): Disparo rápido por 10s

  - Escudo (S): Inmunidad temporal por 8s

  - Invencibilidad (I): Inmunidad total por 5s

# 📊 Progresión y Puntuación

  - Sistema de puntuación por enemigos eliminados

  - Bonus por completar niveles: 1000 × nivel

  - Estadísticas detalladas de bajas

  - Tiempo de juego mostrado

  - Vida máxima aumenta +1 cada 3 niveles

# 🗺️ Generación de Niveles
- Generación procedural con camino garantizado entre inicio y salida

    - 10 niveles con dificultad progresiva

    - Distancia mínima de aparición de enemigos

    - Verificación de alcanzabilidad de todos los elementos
---
# 🔮 Semillas Especiales
  - GOD → 999 HP (modo dios)

  - H4CK3R → +8 munición inicial

  - Sistema expandible para futuras seeds.
---
# 📦 Archivos
- escape_terminal.py — Juego principal en un solo archivo

- escape_terminal_save.json — Guardado automático
---
# 📄 Licencia

Escape the Terminal © 2025 by Dragon56YT is licensed under Creative Commons Attribution-NonCommercial 4.0 International. To view a copy of this license, visit https://creativecommons.org/licenses/by-nc/4.0/

- ✅ You may copy, modify, and distribute for **non-commercial purposes**.
- ✅ You must **attribute the original author** (Dragon56YT) in any copies or derivatives.
- ❌ You **cannot use this software commercially** without explicit permission.
- 📄 Keep the LICENSE.txt file with the project when redistributing or creating derivatives.

See the full license: https://creativecommons.org/licenses/by-nc/4.0/


# ✨ Créditos
## Desarrollo original: Dragon56YT
---

## ¡Alerta! Juego en desarrollo, puede contener errores y pude faltar contenido
