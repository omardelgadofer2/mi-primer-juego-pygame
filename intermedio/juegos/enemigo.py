import os

import pygame

import config

from colisiones import (
    resolver_solidos,
    hay_suelo_debajo,
    limitar_abajo,
    desatarcar
)


# ============================================================
# PUNTO 1.7: ENEMIGO (físicas + IA + las seis animaciones)
# ============================================================
class Enemigo:
    # --------------------------------------------------------
    # PUNTO 1.7.1: Estado inicial
    # --------------------------------------------------------
    def __init__(self, x, y):
        self.hitbox = pygame.Rect(
            x,
            y,
            config.ANCHO_HITBOX_ENEMIGO,
            config.ALTO_HITBOX_ENEMIGO
        )
        self.hitbox.bottom = y

        # --- Física ---
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.en_suelo = True
        self.ancho_mundo = config.ANCHO_VIRTUAL
        self.alto_mundo = config.ALTO_VIRTUAL
        self.solidos = []

        # --- Vida ---
        self.vida = config.ENEMIGO_VIDA
        self.vivo = True
        self.flash = 0

        # PUNTO 1.7.1.1: Muerte. "vivo" dice si recibe daño y empuja al
        # jugador; "muriendo" dice si todavía se dibuja, para que se
        # vea la animación de muerte antes de desaparecer.
        self.muriendo = False
        self.tiempo_muerte = 0.0

        # PUNTO 1.7.1.2: Estado de la IA.
        self.estado = "idle"
        self.estado_anterior = "idle"
        self.direccion = 1
        self.activo = False       # lo eligió el gestor como perseguidor
        self.memoria = 0.0        # sigue Builds aunque el jugador desaparezca
        self.alerta = 0.0         # gesto de "te vi" (Combat Idle)

        # PUNTO 1.7.1.3: Temporizadores del ataque y del salto.
        self.ataque_tiempo = 0.0
        self.ataque_espera = 0.0
        self.ataque_hecho = False
        self.salto_espera = 0.0

        # PUNTO 1.7.1.4: Animación.
        self.frame_index = 0.0
        self.frame_actual = None

        # PUNTO 1.7.1.5: Barra de vida.
        base = os.path.join(config.RUTA_ASSETS, "barra")

        def cargar(nombre):
            img = pygame.image.load(os.path.join(base, nombre)).convert_alpha()
            w, h = img.get_size()
            return pygame.transform.scale(img, (w * 0.5, h * 0.5))

        self.barra_borde = cargar("barra_borde.png")
        self.barra_llena = cargar("barra_llena.png")
        self.barra_5 = cargar("barra_5golpes.png")
        self.barra_4 = cargar("barra_4golpes.png")
        self.barra_3 = cargar("barra_3golpes.png")
        self.barra_2 = cargar("barra_2golpes.png")
        self.barra_1 = cargar("barra_1golpe.png")

        self.cargar_animaciones()

    # --------------------------------------------------------
    # PUNTO 1.7.2: Las seis animaciones
    # --------------------------------------------------------
    def cargar_animaciones(self):
        """
        Carga los seis juegos de fotogramas de la carpeta.

        Cada archivo trae al personaje ya dibujado dentro de un lienzo
        de 48x48 (no hay que cortar tiras), así que se cargan enteros
        y se escalan con ESCALA_ENEMIGO.
        """
        base = os.path.join(config.RUTA_ASSETS, "enemigo_bandido")

        def tira(prefijo, cantidad, invertida=False):
            frames = []

            for i in range(cantidad):
                imagen = pygame.image.load(
                    os.path.join(base, f"{prefijo}_{i}.png")
                ).convert_alpha()

                imagen = pygame.transform.scale(
                    imagen,
                    (
                        imagen.get_width() * config.ESCALA_ENEMIGO,
                        imagen.get_height() * config.ESCALA_ENEMIGO
                    )
                )

                if invertida:
                    imagen = pygame.transform.flip(imagen, True, False)

                frames.append(imagen)

            return frames

        # PUNTO 1.7.2.1: Los seis juegos de fotogramas.
        #
        # OJO: el pack de arte tiene DOS convenciones. Idle, Run y
        # Jump vienen dibujados mirando a la DERECHA, pero Attack y
        # Combat Idle vienen mirando a la IZQUIERDA (se comprobó
        # fotograma a fotograma: el pelo largo cae del lado
        # contrario en el 100% de sus fotogramas).
        #
        # Aquí se invierten las que hagan falta para que TODAS
        # miren a la derecha. A partir de aquí el juego solo tiene
        # que espejar cuando el enemigo mira a la izquierda.
        self.frames_idle = tira("LightBandit_Idle", 4)
        self.frames_run = tira("LightBandit_Run", 8)
        self.frames_jump = tira("LightBandit_Jump", 1)
        self.frames_death = tira("LightBandit_Death", 1)
        self.frames_attack = tira("LightBandit_Attack", 8, invertida=True)
        self.frames_combat_idle = tira(
            "LightBandit_Combat Idle",
            4,
            invertida=True
        )

        # PUNTO 1.7.2.2: Qué fotogramas usar en cada estado.
        self.animaciones = {
            "idle": self.frames_idle,
            "combat_idle": self.frames_combat_idle,
            "correr": self.frames_run,
            "atacar": self.frames_attack,
            "saltar": self.frames_jump,
            "muerte": self.frames_death,
        }

        # PUNTO 1.7.2.3: Los estados que solo se reproducen una vez
        # (el resto vuelve al primer fotograma al terminar).
        self.animaciones_una_vez = {"atacar", "muerte"}

        # PUNTO 1.7.2.4: Versión roja de cada fotograma para el
        # destello de daño, y versión espejada para mirar a la
        # izquierda. Se calculan una sola vez al cargar, no en cada
        # fotograma, y se agrupan en tablas para que "animar" solo
        # tenga que elegir una.
        self.sprites_normal = {"der": {}, "izq": {}}
        self.sprites_rojo = {"der": {}, "izq": {}}

        for nombre, frames in self.animaciones.items():
            for lado in ("der", "izq"):
                normales = []
                rojos = []

                for frame in frames:
                    # El destello rojo sale de la máscara, así que
                    # respeta la silueta exacta del fotograma.
                    mascara = pygame.mask.from_surface(frame)

                    rojo = mascara.to_surface(
                        setcolor=(255, 0, 0, 255),
                        unsetcolor=(0, 0, 0, 0)
                    )

                    if lado == "izq":
                        frame = pygame.transform.flip(frame, True, False)
                        rojo = pygame.transform.flip(rojo, True, False)

                    normales.append(frame)
                    rojos.append(rojo)

                self.sprites_normal[lado][nombre] = normales
                self.sprites_rojo[lado][nombre] = rojos

    # --------------------------------------------------------
    # PUNTO 1.7.3: Consulta al mundo
    # --------------------------------------------------------
    def configurar_mundo(self, ancho, alto, solidos):
        self.ancho_mundo = ancho
        self.alto_mundo = alto
        self.solidos = solidos

    def caja_vision(self):
        """
        El campo de visión: un rectángulo pegado al enemigo hacia donde
        mira. El ancho sale hacia delante y la altura sube por encima
        de la cabeza.
        """
        ancho = config.ENEMIGO_VISION_ANCHO
        alto = config.ENEMIGO_VISION_ALTO

        if self.direccion == 1:
            x = self.hitbox.right - 4
        else:
            x = self.hitbox.left - ancho + 4

        return pygame.Rect(
            x,
            self.hitbox.bottom - alto - 10,
            ancho,
            alto
        )

    def ve_a(self, jugador):
        """¿El jugador ha entrado en el campo de visión?"""
        if self.muriendo or not self.vivo or jugador is None:
            return False

        return self.caja_vision().colliderect(jugador.hitbox)

    def distancia_jugador(self, jugador):
        return abs(jugador.hitbox.centerx - self.hitbox.centerx)

    def caja_ataque(self):
        """La zona de daño de la espada, delante del enemigo."""
        alcance = config.ENEMIGO_ATAQUE_ALCANCE
        alto = config.ENEMIGO_ATAQUE_ALTO
        margen = 4

        if self.direccion == 1:
            x = self.hitbox.right - margen
        else:
            x = self.hitbox.left - alcance + margen

        return pygame.Rect(
            x,
            self.hitbox.centery - alto // 2,
            alcance,
            alto
        )

    def hay_suelo_delante(self):
        """
        ¿Hay suelo un paso por delante? Evita que el enemigo se meta de
        cabeza al pozo mientras persigue al jugador.
        """
        sonda = pygame.Rect(0, 0, self.hitbox.width, self.hitbox.height)

        sonda.midbottom = (
            self.hitbox.centerx
            + self.direccion * (self.hitbox.width // 2 + 4),
            self.hitbox.bottom + 6
        )

        return hay_suelo_debajo(sonda, self.solidos, margen=4)

    def altura_salto(self):
        """Hasta dónde sube el enemigo con un salto (en píxeles)."""
        velocidad = -config.ENEMIGO_SALTO_VELOCIDAD

        return velocidad * velocidad / (2 * config.GRAVEDAD)

    def altura_obstaculo(self):
        """
        Cuánto tiene que subir el enemigo para pasar lo que tiene
        delante. 0 si no hay nada.

        Solo cuentan los sólidos APOYADOS a su altura (su borde
        inferior está a la altura de los pies, o un poco por debajo).
        Si se contaran todos, una plataforma flotante que está 160 px
        más arriba se tomaría por un obstáculo y el enemigo se
        quedaría parado sin motivo.
        """
        suelo = self.hitbox.bottom
        maximo = suelo + 40
        minimo = suelo - self.altura_salto()

        columna = pygame.Rect(0, 0, self.hitbox.width, self.alto_mundo)

        columna.midbottom = (
            self.hitbox.centerx
            + self.direccion * (self.hitbox.width // 2 + 4),
            suelo
        )

        subida = 0

        for solido in self.solidos:
            if not columna.colliderect(solido):
                continue

            if not (minimo <= solido.bottom <= maximo):
                continue

            # El sólido más alto de todos es el que marca el tope.
            cuanta = suelo - solido.top

            if cuanta > subida:
                subida = cuanta

        return subida

    def obstaculo_saltable(self):
        """
        ¿Hay un obstáculo delante que el enemigo pueda saltar?

        Hace falta la comprobación de altura porque en el mapa hay
        muros de 4 tiles (128 px) y el salto del enemigo solo sube
        67 px. Sin esto se ponía a saltar eternamente contra el muro
        sin avanzar, y eso se veía como que andaba al revés.
        """
        altura = self.altura_obstaculo()

        if altura <= 0:
            return False

        return altura <= self.altura_salto() * 0.8

    # --------------------------------------------------------
    # PUNTO 1.7.4: Daño, muerte y empuje
    # --------------------------------------------------------
    def recibir_daño(self, cant, empuje_x=0, empuje_y=None):
        if not self.vivo:
            return

        self.vida -= cant
        self.flash = 0.1

        # PUNTO 1.7.4.1: Al recibir un golpe se activa aunque estuviera
        # en Idle: el jugador ya no puede acercarse a escondidas.
        self.activar()

        if self.vida <= 0:
            self.morir()
            return

        self.vel_x = empuje_x

        if empuje_y is None:
            self.en_suelo = False
        else:
            self.vel_y = empuje_y
            self.en_suelo = False

    def morir(self):
        self.vida = 0
        self.vivo = False
        self.muriendo = True
        self.tiempo_muerte = config.ENEMIGO_TIEMPO_MUERTE
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.activo = False
        self.alerta = 0.0
        self.ataque_tiempo = 0.0

    # --------------------------------------------------------
    # PUNTO 1.7.5: Activar y desactivar (lo llama el gestor)
    # --------------------------------------------------------
    def activar(self):
        if not self.vivo or self.muriendo:
            return

        # PUNTO 1.7.5.1: Solo hace el gesto de "te vi" la primera vez.
        if not self.activo:
            self.alerta = config.ENEMIGO_ALERTA_DURACION

        self.activo = True
        self.memoria = config.ENEMIGO_MEMORIA

    def desactivar(self):
        self.activo = False
        self.memoria = 0.0

    # --------------------------------------------------------
    # PUNTO 1.7.6: La IA (máquina de estados)
    # --------------------------------------------------------
    def pensar(self, dt, jugador):
        """
        Decide el estado y la velocidad horizontal.

        La prioridad es: muerte > ataque en curso > reposo > alerta >
        aire > saltar > atacar > perseguir.
        """
        self.ataque_espera = max(0.0, self.ataque_espera - dt)
        self.salto_espera = max(0.0, self.salto_espera - dt)

        # 0. El jugador está muerto: no hay nada que perseguir ni a
        # quien golpear. Se vuelve al reposo.
        if jugador is None or jugador.vida <= 0:
            self.estado = "idle"
            self.frenar(dt)
            return

        # 1. Muerte: se queda quieto donde lo tumbaron.
        if self.muriendo:
            self.estado = "muerte"
            self.frenar(dt)
            return

        # 2. Ataque en curso: no se mueve, solo golpea.
        if self.ataque_tiempo > 0:
            self.ataque_tiempo -= dt

            # PUNTO 1.7.6.1: El daño entra en un momento concreto de
            # la animación, no en el frame en que empieza.
            if not self.ataque_hecho:
                transcurrido = (
                    config.ENEMIGO_ATAQUE_DURACION - self.ataque_tiempo
                )

                if transcurrido >= config.ENEMIGO_ATAQUE_CONTACTO:
                    self.aplicar_dano(jugador)
                    self.ataque_hecho = True

            if self.ataque_tiempo <= 0:
                self.ataque_tiempo = 0.0
                self.ataque_espera = config.ENEMIGO_ATAQUE_ESPERA

            self.estado = "atacar"
            self.frenar(dt)
            return

        # 3. Reposo: no le toca estar alerta (el gestor lo dijo).
        if not self.activo:
            self.estado = "idle"
            self.frenar(dt)
            return

        # PUNTO 1.7.6.2: Orienta hacia el jugador.
        distancia = self.distancia_jugador(jugador)
        self.direccion = (
            1 if jugador.hitbox.centerx >= self.hitbox.centerx else -1
        )

        # 4. Gesto de alerta: levanta la espada (Combat Idle).
        if self.alerta > 0:
            self.alerta -= dt
            self.estado = "combat_idle"
            self.frenar(dt)
            return

        # 5. En el aire: animación de salto.
        if not self.en_suelo:
            self.estado = "saltar"
            return

        desnivel = self.hitbox.bottom - jugador.hitbox.bottom
        alcance_ataque = config.ENEMIGO_ATAQUE_DISTANCIA

        # 6. ¿Toca atacar?
        if (
            distancia <= alcance_ataque
            and abs(desnivel) <= config.ENEMIGO_ATAQUE_ALCANCE_ALTO
            and self.ataque_espera <= 0
        ):
            self.iniciar_ataque()
            self.estado = "atacar"
            return

        # 7. ¿Toca saltar?
        if self.salto_espera <= 0:
            # El jugador está mucho más arriba que un salto suyo.
            jugador_mas_arriba = (
                jugador.hitbox.bottom
                < self.hitbox.bottom - config.ENEMIGO_SALTO_ALTURA
            )

            if jugador_mas_arriba:
                # Solo salta si tiene suelo donde aterrizar: si está al
                # borde de un precipicio, es mejor no meterse.
                if self.hay_suelo_delante():
                    self.saltar()
                    self.estado = "saltar"
                    return

            # O hay un escalón delante que pueda salvar. Si el muro es
            # más alto que su salto, no lo intenta (se quedaría
            # saltando para siempre sin pasar).
            if self.obstaculo_saltable() and self.hay_suelo_delante():
                self.saltar()
                self.estado = "saltar"
                return

            # Hay algo delante pero no lo puede saltar: se queda en
            # guardia en vez de empujar el muro.
            if self.altura_obstaculo() > 0:
                self.estado = "combat_idle"
                self.frenar(dt)
                return

        # 8. Persecución.
        if distancia > alcance_ataque * 0.55:
            self.estado = "correr"
            self.vel_x = self.direccion * config.ENEMIGO_VELOCIDAD
        else:
            # Ya está en posición: guardia con la espada en alto.
            self.estado = "combat_idle"
            self.frenar(dt)
    def frenar(self, dt):
        """Ralentiza con fricción en vez de frenar en seco."""
        paso = config.ENEMIGO_FRICCION * dt

        if self.vel_x > 0:
            self.vel_x = max(0.0, self.vel_x - paso)
        elif self.vel_x < 0:
            self.vel_x = min(0.0, self.vel_x + paso)

    def iniciar_ataque(self):
        self.ataque_tiempo = config.ENEMIGO_ATAQUE_DURACION
        self.ataque_hecho = False
        self.frame_index = 0.0
        self.estado = "atacar"
        self.estado_anterior = "atacar"

    def aplicar_dano(self, jugador):
        """El filo toca al jugador."""
        if jugador is None or jugador.vida <= 0:
            return

        if self.caja_ataque().colliderect(jugador.hitbox):
            jugador.recibir_daño(config.ENEMIGO_DANO)

    def saltar(self):
        self.vel_y = config.ENEMIGO_SALTO_VELOCIDAD
        self.en_suelo = False
        self.salto_espera = config.ENEMIGO_SALTO_ESPERA

    # --------------------------------------------------------
    # PUNTO 1.7.7: Física (gravedad + suelo + límites)
    # --------------------------------------------------------
    def fisica(self, dt):
        # Antes de mover, la hitbox todavía está donde quedó el frame
        # pasado. Sin esto la colisión no sabe si el enemigo venía de
        # arriba (aterrizaje) o de lado.
        bottom_previo = self.hitbox.bottom

        self.vel_y += config.GRAVEDAD * dt

        if self.vel_y > config.VEL_CAIDA_MAXIMA:
            self.vel_y = config.VEL_CAIDA_MAXIMA

        self.hitbox.x += int(self.vel_x * dt)
        self.hitbox.y += int(self.vel_y * dt)

        en_suelo, bloqueo_x, bloqueo_arriba = resolver_solidos(
            self.hitbox,
            self.vel_x,
            self.vel_y,
            self.solidos,
            bottom_previo
        )

        if not en_suelo and self.en_suelo:
            en_suelo = hay_suelo_debajo(self.hitbox, self.solidos)

        if bloqueo_x:
            self.vel_x = 0.0

        if bloqueo_arriba:
            self.vel_y = 0.0

        self.en_suelo = en_suelo

        if en_suelo:
            self.vel_y = 0.0

        if self.hitbox.left < 0:
            self.hitbox.left = 0
            self.vel_x = 0

        if self.hitbox.right > self.ancho_mundo:
            self.hitbox.right = self.ancho_mundo
            self.vel_x = 0

        if limitar_abajo(self.hitbox, self.solidos, self.alto_mundo):
            self.vel_y = 0
            self.en_suelo = True

        desatarcar(self.hitbox, self.solidos, self.vel_x, self.vel_y)

    # --------------------------------------------------------
    # PUNTO 1.7.8: Update
    # --------------------------------------------------------
    def update(self, dt, jugador=None):
        """
        Un frame completo: primero la IA decide, después la física,
        y al final el reloj de la animación.

        Se puede llamar con jugador=None, en cuyo caso el enemigo se
        queda en reposo (útil para pruebas).
        """
        # PUNTO 1.7.8.1: Enfriamiento del destello rojo.
        if self.flash > 0:
            self.flash -= dt

        # PUNTO 1.7.8.2: El tiempo que recuerda al jugador.
        #
        # Mientras lo siga VIENDO se renueva siempre. Antes solo se
        # contaba hacia atrás desde que se activó, así que a los
        # ENEMIGO_MEMORIA segundos (2.5) abandonaba la persecución
        # aunque el jugador siguiera justo delante: se paraba a
        # medio camino y se quedaba en Idle.
        if self.activo:
            if jugador is not None and self.ve_a(jugador):
                self.memoria = config.ENEMIGO_MEMORIA
            elif self.memoria > 0:
                self.memoria -= dt

                # Si se le olvidó del todo, vuelve a estar en reposo.
                if self.memoria <= 0:
                    self.desactivar()

        # PUNTO 1.7.8.3: Decidir.
        if self.activo and jugador is not None:
            self.pensar(dt, jugador)
        else:
            self.estado = "muerte" if self.muriendo else "idle"
            self.frenar(dt)
        # PUNTO 1.7.8.4: Mover el cuerpo. Los que están muriendo caen
        # hasta el suelo y se quedan.
        if self.vivo or self.muriendo:
            self.fisica(dt)

        # PUNTO 1.7.8.5: Tiempo visible de la animación de muerte.
        if self.muriendo:
            self.tiempo_muerte -= dt

            if self.tiempo_muerte <= 0:
                self.muriendo = False

        # PUNTO 1.7.8.6: Avanzar la animación.
        self.animar(dt)

    # --------------------------------------------------------
    # PUNTO 1.7.9: Animación
    # --------------------------------------------------------
    def animar(self, dt):
        # Al cambiar de estado el reloj vuelve a cero, como en el
        # jugador, para que la animación empiece siempre por el
        # principio.
        if self.estado != self.estado_anterior:
            self.frame_index = 0.0
            self.estado_anterior = self.estado

        frames = self.animaciones[self.estado]

        # PUNTO 1.7.9.1: El ataque va a su propia velocidad. A
        # ENEMIGO_ANIM_FPS (8) sus 8 fotogramas tardarían 1 segundo
        # entero y el ataque solo dura ENEMIGO_ATAQUE_DURACION (0.44),
        # así que se cortaba en el fotograma 3 y nunca se veía el
        # corte de la espada. Aquí la velocidad se calcula para que
        # la animación quepa JUSTO en lo que dura el golpe.
        if self.estado == "atacar":
            fps = len(frames) / config.ENEMIGO_ATAQUE_DURACION
        else:
            fps = config.ENEMIGO_ANIM_FPS

        self.frame_index += dt * fps

        if self.estado in self.animaciones_una_vez:
            # Se queda en el último fotograma en vez de volver al
            # principio: un ataque no se repite solo.
            indice = min(int(self.frame_index), len(frames) - 1)
        else:
            indice = int(self.frame_index) % len(frames)

        lado = "izq" if self.direccion == -1 else "der"

        # PUNTO 1.7.9.1: El destello rojo sustituye al sprite normal
        # durante 0.1 s, sin cambiar nada más.
        if self.flash > 0:
            self.frame_actual = self.sprites_rojo[lado][self.estado][indice]
        else:
            self.frame_actual = self.sprites_normal[lado][self.estado][indice]

    # --------------------------------------------------------
    # PUNTO 1.7.10: Dibujar
    # --------------------------------------------------------
    def draw(self, surface, dt):
        if self.frame_actual is None:
            return

        # PUNTO 1.7.10.1: animar() ya dejó el sprite correcto (normal
        # o rojo) en self.frame_actual, así que aquí no hay que elegir.
        frame = self.frame_actual

        caja_visible = frame.get_bounding_rect()

        desplazamiento_x = (
            caja_visible.centerx - frame.get_width() / 2
        )
        desplazamiento_y = (
            frame.get_height() - caja_visible.bottom
        )

        rect = frame.get_rect(
            midbottom=(
                self.hitbox.centerx - desplazamiento_x,
                self.hitbox.bottom + desplazamiento_y
            )
        )

        surface.blit(frame, rect)

        # PUNTO 1.7.10.2: La barra de vida solo si sigue vivo. Al morir
        # desaparece, porque ya no queda nada que medir.
        if not self.vivo:
            return

        bx = self.hitbox.centerx - self.barra_llena.get_width() // 2
        by = self.hitbox.y - self.barra_llena.get_height() - 8

        nivel = max(
            0,
            min(6, -(-self.vida * 6 // config.ENEMIGO_VIDA))
        )

        sprites = [
            self.barra_borde,
            self.barra_1,
            self.barra_2,
            self.barra_3,
            self.barra_4,
            self.barra_5,
            self.barra_llena,
        ]

        surface.blit(sprites[nivel], (bx, by))
