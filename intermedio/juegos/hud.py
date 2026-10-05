import pygame
import config
import os
import math

RUTA_FUENTE = os.path.join(os.path.dirname(__file__), "assets", "fuente", "PressStart2P-Regular.ttf")
_fuente = None
_fuentes = {}

def _get_fuente_tamano(tamano):
    global _fuentes

    if _fuentes is None:
        _fuentes = {}

    if tamano not in _fuentes:
        _fuentes[tamano] = pygame.font.Font(
            RUTA_FUENTE,
            tamano
        )

    return _fuentes[tamano]

def _color_arcoiris(tiempo):
    fase = (tiempo * config.COMBO_VELOCIDAD_ARCOIRIS) % 1.0

    color = pygame.Color(0, 0, 0)
    color.hsva = (int(fase * 360), 100, 100, 100)

    return color

def _get_fuente():
    global _fuente
    if _fuente is None:
        _fuente = pygame.font.Font(RUTA_FUENTE, 32)
    return _fuente
_sprite_dash_borde = None
# PUNTO 1.1.1: Sprite cache del borde de la barra de dash.
def _get_dash_borde():
    global _sprite_dash_borde

    if _sprite_dash_borde is None:
        base = os.path.join(config.RUTA_ASSETS, "barra")

        imagen = pygame.image.load(
            os.path.join(base, "barra_borde.png")
        ).convert_alpha()

        _sprite_dash_borde = pygame.transform.scale(imagen,( config.HUD_BARRA_DASH_ANCHO, config.HUD_BARRA_DASH_ALTO))

    return _sprite_dash_borde
_sprite_dash_relleno = None
# PUNTO 1.1.2: Sprite cache del relleno normal de la barra de dash.
def _get_dash_relleno():
    global _sprite_dash_relleno

    if _sprite_dash_relleno is None:
        base = os.path.join(config.RUTA_ASSETS, "barra")

        imagen = pygame.image.load(
            os.path.join(base, "barra_dash_llena.png")
        ).convert_alpha()

        # Recorta el espacio transparente de la imagen.
        recorte = imagen.get_bounding_rect()
        _sprite_dash_relleno = imagen.subsurface(
            recorte
        ).copy()

    return _sprite_dash_relleno
_sprite_dash_relleno_blanco = None
def _get_dash_relleno_blanco():
    global _sprite_dash_relleno_blanco

    if _sprite_dash_relleno_blanco is None:
        imagen = _get_dash_relleno()
        mascara = pygame.mask.from_surface(imagen)

        _sprite_dash_relleno_blanco = mascara.to_surface(
            setcolor=(255, 255, 255, 255),
            unsetcolor=(0, 0, 0, 0)
        )

    return _sprite_dash_relleno_blanco
_sprites_vida = None
def _get_vida():
    global _sprites_vida
    if _sprites_vida is None:
        base = os.path.join(os.path.dirname(__file__), "assets", "barra")
        def cargar(n):
            img = pygame.image.load(os.path.join(base, n)).convert_alpha()
            w, h = img.get_size()
            return pygame.transform.scale(
                img,
                (
                    w * config.HUD_ESCALA_VIDA,
                    h * config.HUD_ESCALA_VIDA
                )
            )
        _sprites_vida = [cargar("barra_vida_vacia.png"), cargar("barra_vida_1.png"),
                            cargar("barra_vida_2.png"), cargar("barra_vida_3.png"),
                            cargar("barra_vida_llena.png")]
        
    return _sprites_vida

# ============================================================
# PUNTO 1: HUD (dash + vida + contador)
# ============================================================
def _dibujar_contador_combo(surface, player):
        golpes = player.golpes

        # Nivel visual: 0, 1, 2 o 3 (a partir de 15 golpes).
        nivel = min(golpes // 5, 3)

        # El límite real del combo sigue siendo COMBO_MAXIMO.
        en_limite = golpes >= config.COMBO_MAXIMO

        tamano = (
            config.COMBO_TAMANO_BASE
            + nivel * config.COMBO_TAMANO_POR_NIVEL
        )

        if en_limite:
            tamano = config.COMBO_TAMANO_MAXIMO

        tiempo = pygame.time.get_ticks() / 1000.0

        if en_limite:
            color = _color_arcoiris(tiempo)
            move_x = int(math.sin(tiempo * 40) * config.COMBO_TEMBLOR)
            move_y = int(math.cos(tiempo * 37) * config.COMBO_TEMBLOR)
        else:
            color = config.COMBO_COLORES[nivel]
            move_x = 0
            move_y = 0

        texto = _get_fuente_tamano(tamano).render(
            f"GOLPES x{golpes}",
            True,
            color
        )

        surface.blit(
            texto,
            texto.get_rect(
                bottomleft=(
                    config.HUD_CONTADOR_X + move_x,
                    config.ALTO_VIRTUAL - config.HUD_CONTADOR_Y + move_y
                )
            )
        )
def draw_hud(surface, player):
    # PUNTO 1.2.1: Barra de dash: relleno, destello y borde.
    # --- PUNTO 1.1: Barra de dash (arriba) ---
    margen_x = config.HUD_BARRA_DASH_MARGEN_X
    margen_y = config.HUD_BARRA_DASH_MARGEN_Y
    barra_x = config.HUD_BARRA_DASH_X
    barra_y = config.HUD_BARRA_DASH_Y
    barra_ancho = config.HUD_BARRA_DASH_ANCHO
    barra_alto = config.HUD_BARRA_DASH_ALTO
    ancho_interior = barra_ancho - margen_x * 2
    alto_interior = barra_alto - margen_y * 2
    porcentaje = porcentaje = player.dash_bar_porcentaje
    ancho_actual = int(ancho_interior * porcentaje)
    if player.tiempo_destello > 0:
        imagen_relleno = _get_dash_relleno_blanco()
    else:
        imagen_relleno = _get_dash_relleno()
    if ancho_actual > 0:
        relleno_completo = pygame.transform.scale(
            imagen_relleno,
            (ancho_interior, alto_interior)
        )

        relleno_actual = relleno_completo.subsurface(
            (
                0,
                0,
                ancho_actual,
                alto_interior
            )
        ).copy()
        

        surface.blit(
            relleno_actual,
            (barra_x + margen_x, barra_y + margen_y)
        )

    surface.blit(
        _get_dash_borde(),
        (barra_x, barra_y)
    )
    


    # --- PUNTO 1.2: Vida del jugador (debajo del dash) ---
    nivel = max(0, min(4, -(-player.vida * 4 // config.JUGADOR_VIDA)))
    surface.blit(
        _get_vida()[nivel],
        (config.HUD_BARRA_VIDA_X, config.HUD_BARRA_VIDA_Y)
    )

     # PUNTO 1.2.2: Slot del arma equipada.
     # --- Slot del inventario ---
    slot = pygame.Rect(
        config.HUD_SLOT_X,
        config.ALTO_VIRTUAL - config.HUD_SLOT_Y,
        config.HUD_SLOT_LADO,
        config.HUD_SLOT_LADO
    )

    pygame.draw.rect(
        surface,
        (40, 40, 40),
        slot
    )

    pygame.draw.rect(
        surface,
        (220, 220, 220),
        slot,
        1
    )

    arma = player.inventario.equipado

    if arma is not None:
        icono = arma.textura_hud
        surface.blit(
            icono,
            icono.get_rect(center=slot.center)
        )

    # --- PUNTO 1.3: Contador de golpes (abajo a la izquierda) ---
    _dibujar_contador_combo(surface, player)
    

        