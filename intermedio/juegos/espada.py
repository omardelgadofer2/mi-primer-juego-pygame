import pygame
import config
import os
import math
from colisiones import (
    resolver_solidos,
    hay_suelo_debajo,
    hay_pared,
    limitar_abajo,
    desatarcar
)
RUTA_FUENTE = os.path.join(os.path.dirname(__file__), "assets", "fuente", "PressStart2P-Regular.ttf")
class Espada:
    def __init__(self, x, y):
        self.hitbox = pygame.Rect(x, y, config.ESPADA_HITBOX_ANCHO, config.ESPADA_HITBOX_ALTO)
        self.recogida = False
        self.vel_y = 0
        self.en_suelo = False
        self.ancho_mundo = config.ANCHO_VIRTUAL
        self.alto_mundo = config.ALTO_VIRTUAL
        self.solidos = []
        self.angulo = 0
        self.tiempo_visual = 0
        self.zona_interaccion = self.hitbox.inflate(*config.ESPADA_ZONA_INFLAR)
        self.fuente_ete = pygame.font.Font(RUTA_FUENTE, 18)
        self.es_arma = True
        self.daño = 1
        self.alcance = config.ESPADA_ALCANCE
        self.duracion_ataque = 0.35
        self.cooldown_ataque = 0.40
        

        ruta = os.path.join(config.RUTA_ASSETS, "items", "espada.png")
        self.textura = pygame.image.load(ruta).convert_alpha()
        self.textura_mundo = pygame.transform.smoothscale(
            self.textura,
            (
                config.ESPADA_TEXTURA_ANCHO,
                config.ESPADA_TEXTURA_ALTO
            )
        )
        self.textura_hud = pygame.transform.smoothscale(
            self.textura,
            (
                config.ESPADA_TEXTURA_HUD_ANCHO,
                config.ESPADA_TEXTURA_HUD_ALTO
            )
        )

        self.textura_blanca = self._crear_blanca(self.textura_mundo)

    @staticmethod
    def _crear_blanca(textura):
        blanca = textura.copy()

        for y in range(textura.get_height()):
            for x in range(textura.get_width()):
                pixel = textura.get_at((x, y))

                if pixel.a > 0:
                    blanca.set_at(
                        (x, y),
                        (255, 255, 255, pixel.a)
                    )

        return blanca
    
    def configurar_mundo(self, ancho, alto, solidos):
        self.ancho_mundo = ancho
        self.alto_mundo = alto
        self.solidos = solidos

    def update(self, dt):
        
        if self.recogida:
            return

        # Antes de mover: la hitbox todavía está donde quedó el frame
        # pasado. Antes se pasaba self.hitbox.bottom DESPUÉS de mover,
        # así que el filtro de aterrizaje de resolver_solidos nunca
        # rechazaba nada.
        bottom_previo = self.hitbox.bottom

        if not self.en_suelo:
            self.vel_y += config.GRAVEDAD * dt

            # Techo de caída: sin esto la gravedad se acumula sin
            # límite y atraviesa los tiles del fondo.
            if self.vel_y > config.VEL_CAIDA_MAXIMA:
                self.vel_y = config.VEL_CAIDA_MAXIMA

            self.hitbox.y += int(self.vel_y * dt)

        en_suelo, _, _ = resolver_solidos(
            self.hitbox,
            0,
            self.vel_y,
            self.solidos,
            bottom_previo
        )

        if not en_suelo and self.en_suelo:
            en_suelo = hay_suelo_debajo(
                self.hitbox,
                self.solidos
            )

        if en_suelo:
            self.vel_y = 0

        self.en_suelo = en_suelo

        if limitar_abajo(self.hitbox, self.solidos, self.alto_mundo):
            self.vel_y = 0
            self.en_suelo = True

        desatarcar(self.hitbox, self.solidos, 0.0, self.vel_y)
        # La zona de interacción sigue a la espada cuando cae.
        self.zona_interaccion = self.hitbox.inflate(*config.ESPADA_ZONA_INFLAR)

        if self.en_suelo:
            self.tiempo_visual += dt
            self.angulo = (self.angulo + 90 * dt) % 360

    def jugador_cerca(self, hitbox_jugador):
        if self.recogida:
            return False

        return self.zona_interaccion.colliderect(hitbox_jugador)

    def draw(self, surface, mostrar_ete=False):
        if self.recogida:
            return

        centro = (
            self.hitbox.centerx,
            self.hitbox.centery
        )
        if self.en_suelo and int(self.tiempo_visual * 2.5) % 2 == 0:
            imagen = self.textura_blanca
        else:
            imagen = self.textura_mundo.copy()

        if self.en_suelo:
            factor = math.cos(self.tiempo_visual * 2.0)

            ancho = max(
                1,
                int(self.textura_mundo.get_width() * abs(factor))
            )

            imagen = pygame.transform.scale(
                imagen,
                (ancho, self.textura_mundo.get_height())
            )

            if factor < 0:
                imagen = pygame.transform.flip(
                    imagen,
                    True,
                    False
                )

        surface.blit(
            imagen,
            imagen.get_rect(center=centro)
        )

        if mostrar_ete:
            caja_e = pygame.Rect(
                0,
                0,
                config.ESPADA_CAJON_E,
                config.ESPADA_CAJON_E
            )

            caja_e.center = (
                self.hitbox.centerx,
                self.hitbox.top - config.ESPADA_CAJON_E_OFFSET
            )

            pygame.draw.rect(
                surface,
                (30, 30, 30),
                caja_e
            )

            pygame.draw.rect(
                surface,
                (255, 255, 255),
                caja_e,
                2
            )

            texto = self.fuente_ete.render(
                "E",
                True,
                (255, 255, 255)
            )

            surface.blit(
                texto,
                texto.get_rect(center=caja_e.center)
            )
