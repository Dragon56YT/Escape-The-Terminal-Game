# Escape the Terminal

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-v0.3--alpha-orange)

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

```bash
python escape_terminal.py
````
## Compatibilidad

- Windows / Linux / macOS

- Compatible con Python 3.8+

- Requiere terminal con soporte para colores y curses
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
## Este proyecto es open-source bajo licencia MIT.

# ✨ Créditos
## Desarrollo original: Dragon56YT
---

## ¡Alerta! Juego en desarrollo, puede contener errores y pude faltar contenido
