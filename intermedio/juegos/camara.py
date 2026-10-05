import pygame
import config


class Camara:
    # --------------------------------------------------------
    # PUNTO 2.4: Cámara que sigue al jugador
    # --------------------------------------------------------
    def __init__(self, mapa):
        self.ancho_vista = config.ANCHO_VIRTUAL
        self.alto_vista = config.ALTO_VIRTUAL

        self.ancho_mapa = mapa.ancho
        self.alto_mapa = mapa.alto

        self.x = 0
        self.y = self.alto_mapa - self.alto_vista

    # --------------------------------------------------------
    # PUNTO 2.4.1: Centrar la vista en el jugador
    # --------------------------------------------------------
    def seguir(self, jugador):
        self.x = (
            jugador.hitbox.centerx
            - self.ancho_vista // 2
        )

        self.y = (
            jugador.hitbox.centery
            - self.alto_vista // 2
        )

        self.limitar()

    # --------------------------------------------------------
    # PUNTO 2.4.2: No salirse de los límites del mapa
    # --------------------------------------------------------
    def limitar(self):
        self.x = max(
            0,
            min(self.x, self.ancho_mapa - self.ancho_vista)
        )

        if self.alto_mapa < self.alto_vista:
            # El mapa es más bajo que la vista: se pega al piso.
            self.y = self.alto_mapa - self.alto_vista
        else:
            self.y = max(
                0,
                min(self.y, self.alto_mapa - self.alto_vista)
            )

    # --------------------------------------------------------
    # PUNTO 2.4.3: Parte del mapa que se ve.
    # --------------------------------------------------------
    def area(self):
        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.ancho_vista,
            self.alto_vista
        )