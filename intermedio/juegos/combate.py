import pygame
import config
import os

# ============================================================
# PUNTO 1: Combate
# ============================================================
class SistemaCombate:
    # --------------------------------------------------------
    # PUNTO 1.1: Estado interno del sistema de combate
    # --------------------------------------------------------
    def __init__(self):
        # Estado del golpe: "idle" o "atacando".
        self.estado_ataque = "idle"
        self.tiempo_ataque = 0.0

        # Tiempo que falta para volver a permitir un ataque.
        self.cooldown = 0.0

        # Zona de daño temporal del arma.
        self.hitbox_ataque = None
        self.ya_golpeo = False

        # Dirección y variante visual del ataque actual.
        self.direccion_ataque = 1
        self.tipo_animacion = None
        self.secuencia_ataque = 1

    # --------------------------------------------------------
    # PUNTO 1.2: Arma equipada y permiso de ataque
    # --------------------------------------------------------
    def obtener_arma(self, jugador):
        arma = jugador.inventario.equipado

        if arma is None:
            return None

        if not getattr(arma, "es_arma", False):
            return None

        return arma

    def puede_atacar(self, jugador):
        arma = self.obtener_arma(jugador)

        if arma is None:
            return False

        if self.cooldown > 0:
            return False

        return True

    def factor_combo(self, jugador):
        nivel = min(
            jugador.golpes,
            config.COMBO_MAXIMO
        )

        progreso = nivel / config.COMBO_MAXIMO

        return 1.0 + (
            (config.FACTOR_COMBO_MAXIMO - 1.0)
            * (progreso ** config.CURVA_COMBO)
        )

    # --------------------------------------------------------
    # PUNTO 1.3: Actualización del ataque
    # --------------------------------------------------------
    def update(self, dt, keys, jugador, ataque_presionado, mouse_virtual_x, enemigos):
        # PUNTO 1.3.1: Reducir el cooldown del arma.
        self.cooldown = max(0, self.cooldown - dt)

        # PUNTO 1.3.2: Mantener activa la animación y la hitbox.
        if self.estado_ataque == "atacando":
            self.tiempo_ataque = max(0, self.tiempo_ataque - dt)
            arma = self.obtener_arma(jugador)

            # PUNTO 1.3.2.1: La hitbox sigue al jugador durante el golpe.
            if arma is not None:
                self.hitbox_ataque = self.crear_hitbox_ataque(
                    jugador,
                    arma
                )
            else:
                self.hitbox_ataque = None

            # PUNTO 1.3.2.2: Un solo impacto por ataque.
            if (
                self.hitbox_ataque is not None
                and not self.ya_golpeo
            ):
                for enemigo in enemigos:
                    if (
                        enemigo.vivo
                        and self.hitbox_ataque.colliderect(enemigo.hitbox)
                    ):
                        if arma is not None:
                            enemigo.recibir_daño(arma.daño)
                            jugador.golpes += 1
                            self.ya_golpeo = True

                        break

            # PUNTO 1.3.2.3: Terminar ataque y limpiar la zona de daño.
            if self.tiempo_ataque <= 0:
                self.estado_ataque = "idle"
                self.tipo_animacion = None
                jugador.terminar_animacion_ataque()
                self.hitbox_ataque = None

        # PUNTO 1.3.3: Detectar una nueva pulsación de ataque.
        if not ataque_presionado:
            return

        if not self.puede_atacar(jugador):
            return

        

        

        
        # PUNTO 1.3.4: Iniciar el ataque con los datos del arma.
        secuencia_actual = self.secuencia_ataque
        arma = self.obtener_arma(jugador)
        factor_combo = self.factor_combo(jugador)

        self.velocidad_ataque = min(config.VELOCIDAD_ATAQUE_MAXIMA, config.VELOCIDAD_ATAQUE_BASE * factor_combo)
        self.tiempo_ataque = max(config.ATAQUE_DURACION_MINIMA, arma.duracion_ataque / factor_combo)
        self.cooldown = max(config.ATAQUE_COOLDOWN_MINIMO, arma.cooldown_ataque / factor_combo)
        

        # PUNTO 1.3.4.1: Iniciar con los valores base del arma.
        self.estado_ataque = "atacando"
        self.tiempo_ataque = max(config.ATAQUE_DURACION_MINIMA, arma.duracion_ataque / factor_combo)
        self.cooldown = max(config.ATAQUE_COOLDOWN_MINIMO, arma.cooldown_ataque / factor_combo)
        self.ya_golpeo = False

        # PUNTO 1.3.5: Dirección híbrido (mouse quieto / A-D moviendo).
        if not jugador.en_movimiento:
            if mouse_virtual_x < jugador.hitbox.centerx:
                self.direccion_ataque = -1
            else:
                self.direccion_ataque = 1
        else:
            self.direccion_ataque = jugador.direccion

        # PUNTO 1.3.6: Crear la zona de daño inicial.
        self.hitbox_ataque = self.crear_hitbox_ataque(
            jugador,
            arma
        )

        # PUNTO 1.3.7: Elegir animación según el estado del jugador.
        # El ataque agachado mantiene una sola animación, sin secuencia.
        if jugador.estado in {"agachado", "agachado_caminando"}:
            self.tipo_animacion = "agachado"
            jugador.iniciar_animacion_ataque(
                self.tipo_animacion,
                self.direccion_ataque,
                secuencia_actual,
                self.velocidad_ataque
            )
        elif jugador.en_movimiento:
            self.tipo_animacion = "movimiento"
            jugador.iniciar_animacion_ataque(
                self.tipo_animacion,
                self.direccion_ataque,
                secuencia_actual,
                self.velocidad_ataque
            )
            # PUNTO 1.3.8: Alternar la variante para el próximo ataque.
            if secuencia_actual == 1:
                self.secuencia_ataque = 2
            else:
                self.secuencia_ataque = 1
        else:
            self.tipo_animacion = "quieto"
            jugador.iniciar_animacion_ataque(
                self.tipo_animacion,
                self.direccion_ataque,
                secuencia_actual,
                self.velocidad_ataque
            )

            # PUNTO 1.3.8: Alternar la variante para el próximo ataque.
            if secuencia_actual == 1:
                self.secuencia_ataque = 2
            else:
                self.secuencia_ataque = 1

    # --------------------------------------------------------
    # PUNTO 1.4: Crear la hitbox del ataque
    # --------------------------------------------------------
    def crear_hitbox_ataque(self, jugador, arma):
        # El alcance y la dirección vienen del objeto equipado.
        alcance = arma.alcance
        alto = int(jugador.hitbox.height * 0.6)
        margen = 8

        if self.direccion_ataque == 1:
            x = jugador.hitbox.right - margen
        else:
            x = jugador.hitbox.left - alcance + margen

        self.hitbox_ataque = pygame.Rect(
            x,
            jugador.hitbox.centery - alto // 2,
            alcance,
            alto
        )
        return self.hitbox_ataque