import os
# ============================================================
# PUNTO 1: CONFIG (solo constantes, nada de estado)
# ============================================================

# --- PUNTO 1.1: Mundo ---
ANCHO_VIRTUAL, ALTO_VIRTUAL = 800, 450
ESCALA_PERSONAJES = 0.50
ANCHO_HITBOX = int(48 * ESCALA_PERSONAJES)
ALTO_HITBOX = int(76 * ESCALA_PERSONAJES)
ESCALA_JUGADOR = 2 * ESCALA_PERSONAJES





# --- PUNTO 1.2: Movimiento horizontal ---
VEL_CAMINAR = int(260 * ESCALA_PERSONAJES)
VEL_CORRER = int(470 * ESCALA_PERSONAJES)
ACELERACION = int(2500 * ESCALA_PERSONAJES)
FRICCION = int(3200 * ESCALA_PERSONAJES)
ENEMIGO_EMPUJE = 600

# --- PUNTO 1.3: Movimiento vertical ---
GRAVEDAD = int(2500 * ESCALA_PERSONAJES)
FUERZA_SALTO = -int(950 * ESCALA_PERSONAJES)
CONTROL_AEREO = 0.6
MULT_CAIDA = 1.0

# Techo de la velocidad de caída. Sin esto la gravedad se acumula sin
# límite: cayendo por el pozo el jugador llegaba a 5896 px/s (98 px en un
# solo frame), se comía los tiles al aterrizar y era incontrolable.
VEL_CAIDA_MAXIMA = int(1200 * ESCALA_PERSONAJES)

COYOTE_DURACION = 0.2
VEL_MOVIMIENTO_MINIMO = int(10 * ESCALA_PERSONAJES)
VEL_CAIDA_WALLSLIDE = int(150 * ESCALA_PERSONAJES)

# --- PUNTO 1.4: Dash ---
VEL_DASH = int(1400 * ESCALA_PERSONAJES)
DASH_DURACION = 0.20
DASH_ESPERA = 3.0
DASH_INVULNERABLE = 0.12
DASH_BAR_CAIDA = 0.30


# --- PUNTO 1.5: Precisión de salto ---
JUMP_BUFFER_DURACION = 0.12

# --- PUNTO 1.7: Vida y contador ---
JUGADOR_VIDA = 6
DAÑO_CONTACTO = 1
ENEMIGO_VIDA = 9

# --- PUNTO 1.8: RUTAS
RUTA_RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_ASSETS = os.path.join(RUTA_RAIZ, "assets")

#---enemigo---
ESCALA_ENEMIGO = 2 * ESCALA_PERSONAJES
ANCHO_HITBOX_ENEMIGO = int(52 * ESCALA_PERSONAJES)
ALTO_HITBOX_ENEMIGO = int(76 * ESCALA_PERSONAJES)

# --- PUNTO 1.7.1: Enemigo: movimiento ---
# Velocidad con la que persigue al jugador. Va por debajo de
# VEL_CAMINAR (130) para que el jugador pueda huir corriendo (235).
ENEMIGO_VELOCIDAD = int(190 * ESCALA_PERSONAJES)
ENEMIGO_ACCELERACION = int(900 * ESCALA_PERSONAJES)
ENEMIGO_FRICCION = int(1400 * ESCALA_PERSONAJES)

# --- PUNTO 1.7.2: Enemigo: campo de visión ---
# Es un rectángulo pegado al enemigo, hacia donde mira. Si el jugador
# entra, el enemigo deja el Idle, levanta la espada (Combat Idle) y
# lo persigue.
ENEMIGO_VISION_ANCHO = int(260 * ESCALA_PERSONAJES)
ENEMIGO_VISION_ALTO = int(90 * ESCALA_PERSONAJES)

# Cuántos enemigos pueden estar alerta a la vez. Con los 11 enemigos
# del mapa, sin este tope todos embisten juntos y el juego es
# imposible. Entran los más cercanos al jugador.
ENEMIGO_ACTIVOS_MAXIMO = 3

# Segundos que sigue persiguiendo aunque el jugador salga del campo
# de visión (para que no se le "olvide" en el borde de la pantalla).
ENEMIGO_MEMORIA = 2.5

# Duración del gesto de alerta (Combat Idle) al detectar al jugador.
ENEMIGO_ALERTA_DURACION = 0.30

# --- PUNTO 1.7.3: Enemigo: ataque ---
# OJO: tiene que ser MAYOR que el ancho del jugador (24) más el del
# enemigo (26), porque la colisión física los mantiene pegados. Con
# 26 el enemigo llegaba a 25-27 px de distancia y a veces el jugador
# quedaba justo fuera y nunca recibía un golpe.
ENEMIGO_ATAQUE_DISTANCIA = int(72 * ESCALA_PERSONAJES)
ENEMIGO_ATAQUE_ALCANCE = int(30 * ESCALA_PERSONAJES)
ENEMIGO_ATAQUE_ALTO = int(30 * ESCALA_PERSONAJES)
ENEMIGO_ATAQUE_DURACION = 0.44
# Momento de la animación en el que el filo hace contacto.
ENEMIGO_ATAQUE_CONTACTO = 0.20
ENEMIGO_ATAQUE_ESPERA = 1.0
ENEMIGO_DANO = 1
# Diferencia de altura máxima para que el golpe alcance. Si el
# jugador está mucho más arriba, el enemigo prefiere saltar.
ENEMIGO_ATAQUE_ALCANCE_ALTO = int(44 * ESCALA_PERSONAJES)

# --- PUNTO 1.7.4: Enemigo: salto ---
ENEMIGO_SALTO_VELOCIDAD = -int(820 * ESCALA_PERSONAJES)
# Solo salta si el jugador está al menos esto más arriba.
ENEMIGO_SALTO_ALTURA = int(56 * ESCALA_PERSONAJES)
ENEMIGO_SALTO_ESPERA = 0.5
# Distancia por delante para comprobar si hay un obstáculo.
ENEMIGO_OBSTACULO_DISTANCIA = int(26 * ESCALA_PERSONAJES)

# --- PUNTO 1.7.5: Enemigo: muerte y animación ---
# Tiempo que se ve la animación de muerte antes de desaparecer.
ENEMIGO_TIEMPO_MUERTE = 1.1
# Fotogramas por segundo de cada animación.
ENEMIGO_ANIM_FPS = 8
# El ataque es una excepción: sus 8 fotogramas tienen que caber
# dentro de ENEMIGO_ATAQUE_DURACION. Si no, a 8 fps solo se alcanza
# a ver el principio (levantar la espada) y nunca el corte.
# enemigo.py calcula la velocidad que hace falta para que quepa.

# --- PUNTO 1.7.6: Reaparición del jugador ---
# Segundos que se ve la animación de muerte antes de reaparecer.
REAPARICION_ESPERA = 1.8

#--- combate ---
COMBO_MAXIMO = 15
VELOCIDAD_ATAQUE_BASE = 18.0
VELOCIDAD_ATAQUE_MAXIMA = 42.0
FACTOR_COMBO_MAXIMO = 4.0
CURVA_COMBO = 4.0
ATAQUE_COOLDOWN_MINIMO = 0.08
ATAQUE_DURACION_MINIMA = 0.14

#----Contador de combo -----
COMBO_TAMANO_BASE = 13
COMBO_TAMANO_POR_NIVEL = 8
COMBO_TAMANO_MAXIMO = 24

COMBO_COLORES = [
    (255, 255, 255),
    (120, 255, 120),
    (120, 200, 255),
    (255, 220, 80),
]

COMBO_TEMBLOR = 4
COMBO_VELOCIDAD_ARCOIRIS = 5

COLOR_FONDO_MAPA = (120, 190, 220)

#--- PUNTO 1.9: Arma (espada) ---
ESPADA_TEXTURA_ANCHO = int(39 * ESCALA_PERSONAJES)
ESPADA_TEXTURA_ALTO = int(37 * ESCALA_PERSONAJES)

ESPADA_TEXTURA_HUD_ANCHO = 26
ESPADA_TEXTURA_HUD_ALTO = 25

ESPADA_HITBOX_ANCHO = int(24 * ESCALA_PERSONAJES)
ESPADA_HITBOX_ALTO = int(28 * ESCALA_PERSONAJES)

ESPADA_ALCANCE = int(70 * ESCALA_PERSONAJES)
ESPADA_ZONA_INFLAR = (int(90 * ESCALA_PERSONAJES), int(60 * ESCALA_PERSONAJES))

ESPADA_CAJON_E = 26
ESPADA_CAJON_E_OFFSET = 26

# --- PUNTO 1.10: HUD ---
HUD_BARRA_DASH_X = 4
HUD_BARRA_DASH_Y = 0
HUD_BARRA_DASH_ANCHO = 111
HUD_BARRA_DASH_ALTO = 30
HUD_BARRA_DASH_MARGEN_X = 9
HUD_BARRA_DASH_MARGEN_Y = 5

HUD_BARRA_VIDA_X = 0
HUD_BARRA_VIDA_Y = 26
HUD_ESCALA_VIDA = 2

HUD_SLOT_X = 63
HUD_SLOT_Y = 88
HUD_SLOT_LADO = 38

HUD_CONTADOR_X = 17
HUD_CONTADOR_Y = 17

# --- PUNTO 1.11: Agua ---
AGUA_FACTOR_VELOCIDAD = 0.45
AGUA_FACTOR_GRAVEDAD = 0.30
AGUA_FACTOR_SALTO = 0.55

AGUA_VEL_CAIDA = int(140 * ESCALA_PERSONAJES)
AGUA_VEL_NADO = int(200 * ESCALA_PERSONAJES)