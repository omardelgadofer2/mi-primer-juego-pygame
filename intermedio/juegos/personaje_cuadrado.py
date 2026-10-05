import pygame
import config
import os
from inventario import Inventario
from colisiones import resolver_solidos, hay_suelo_debajo, hay_pared
from colisiones import desatarcar, limitar_abajo

# ============================================================
# PUNTO 1: JUGADOR CUADRADO (lógica + dibujo del personaje)
# ============================================================
class Player:
    # --------------------------------------------------------
    # PUNTO 1.1: Estado inicial
    # --------------------------------------------------------
    def __init__(self):
        # Posición y tamaño visual
        self.pos = pygame.Vector2(config.ANCHO_VIRTUAL / 2, config.ALTO_VIRTUAL / 2)
        self.ancho = config.ANCHO_HITBOX
        self.alto = config.ALTO_HITBOX
        # Hitbox (PUNTO 2: colisión separada del visual)
        self.hitbox = pygame.Rect(self.pos.x,
        self.pos.y,
        config.ANCHO_HITBOX,
        config.ALTO_HITBOX)
        # Física vertical
        self.vel_y = 0
        self.coyote = 0
        # movimiento horizontal
        self.vel_x = 0
        self.en_suelo = False
        # Límites del mundo (los define el mapa, no la ventana).
        self.ancho_mundo = config.ANCHO_VIRTUAL
        self.alto_mundo = config.ALTO_VIRTUAL
        self.solidos = []
        # Dash
        self.dash_tiempo = 0
        self.dash_cooldown = 0
        self.dash_dir = pygame.Vector2(0, 0)
        self.dash_invulnerable = 0.0
        # Efectos
        self.estela = []
        self.tiempo_clon = 0
        self.intervalo_clon = 0.12
        # Salto de precisión
        self.jump_buffer = 0
        self.solto_w = False
        # HUD (destello de recarga)
        self.tiempo_destello = 0
        self.ya_destello = True
        # Estado de movimiento
        self.en_movimiento = False
        self.corriendo = False
        # Paredes (PUNTO 3: wall-slide)
        self.en_pared_izq = False
        self.en_pared_der = False
        # Vida y contador (PUNTO 4: combate)
        self.vida = config.JUGADOR_VIDA
        self.golpes = 0
        self.direccion = 1
        self.en_wallslide = False
        self.walljump_armed = False
        self.w_was_pressed = False
        self.wall_jump_cooldown = 0.0
        # PUNTO 1.4: Estado visual del ataque (lo controla combate.py).
        self.inventario = Inventario(cantidad_slots=1)
        self.ataque_secuencia = 1
        self.ataque_tipo = None
        self.ataque_direccion = self.direccion
        self.ataque_frame_index = 0.0
        self.dash_bar_porcentaje = 1.0
        self.dash_bar_drenaje = 0.0
        self.agua = []
        self.en_agua = False
        self.estaba_en_agua = False

        ruta_jugador = os.path.join(config.RUTA_ASSETS, "jugador")

        # 2. Cargamos las dos tiras de imágenes completas en la memoria RAM
        self.anim_correr = pygame.image.load(os.path.join(ruta_jugador, "_run.png")).convert_alpha()
        self.anim_saltar = pygame.image.load(os.path.join(ruta_jugador, "_jump.png")).convert_alpha()
        self.anim_entre_salto_caida = pygame.image.load(os.path.join(ruta_jugador, "_jumpfallinbetween.png")).convert_alpha()
        self.anim_caer = pygame.image.load(os.path.join(ruta_jugador, "_fall.png")).convert_alpha()
        self.anim_quieto= pygame.image.load(os.path.join(ruta_jugador, "_idle.png")).convert_alpha()
        self.anim_agachado = pygame.image.load(os.path.join(ruta_jugador, "_crouch.png")).convert_alpha()
        self.anim_dash = pygame.image.load(os.path.join(ruta_jugador, "_dash.png")).convert_alpha()
        self.anim_caminar_agachado = pygame.image.load(os.path.join(ruta_jugador, "_crouchwalk.png")).convert_alpha()
        self.anim_transcicion_agachado = pygame.image.load(os.path.join(ruta_jugador, "_crouchtransition.png")).convert_alpha()
        self.anim_full_agachado = pygame.image.load(os.path.join(ruta_jugador, "_crouchfull.png")).convert_alpha()
        self.anim_death = pygame.image.load(os.path.join(ruta_jugador, "_death.png")).convert_alpha()
        self.anim_death_quieto= pygame.image.load(os.path.join(ruta_jugador, "_deathnomovement.png")).convert_alpha()
        self.anim_darse_vuelta = pygame.image.load(os.path.join(ruta_jugador, "_turnaround.png")).convert_alpha()
        self.anim_wallslide = pygame.image.load(os.path.join(ruta_jugador, "_wallslide.png")).convert_alpha()    
        self.anim_ataque_movimiento = pygame.image.load(os.path.join(ruta_jugador, "_attack.png")).convert_alpha()
        self.anim_ataque_quieto = pygame.image.load(os.path.join(ruta_jugador, "_attacknomovement.png")).convert_alpha()
        self.anim_ataque_agachado = pygame.image.load(os.path.join(ruta_jugador, "_crouchattack.png")).convert_alpha()
        self.anim_ataque_movimiento_2 = pygame.image.load(os.path.join(ruta_jugador, "_attack2.png")).convert_alpha()
        self.anim_ataque_quieto_2 = pygame.image.load(os.path.join(ruta_jugador, "_attack2nomovement.png")).convert_alpha()

        # 3. Las variables de control del proyector de cine
        self.estado = "quieto"   
        self.estado_anterior = self.estado
        self.vel_y_anterior = self.vel_y
        self.tiempo_entre_salto_caida = 0.0
        self.muerte_movimiento = False
        self.animaciones_una_vez = {
            "agachado_transicion",
            "entre",
            "muerte",
            "muerte_quieto",
        }
        self.frame_index = 0.0       # El reloj de los fotogramas empieza en 0
        self.ancho_fotograma = 120   # La medida exacta del lienzo de tu nuevo personaje (120x80)
        
        def cortar(tira, ancho, escala=config.ESCALA_JUGADOR):
            frames = []
            for i in range(tira.get_width() // ancho):
                f = tira.subsurface((i * ancho, 0, ancho, tira.get_height()))
                frames.append(pygame.transform.scale(f, (ancho * escala, tira.get_height() * escala)))
            return frames

        self.frames_quieto = cortar(self.anim_quieto, 120)
        self.frames_correr = cortar(self.anim_correr, 120)
        self.frames_saltar = cortar(self.anim_saltar, 120)
        self.frames_anim_entre_salto_caida = cortar(self.anim_entre_salto_caida, 120)
        self.frames_caer = cortar(self.anim_caer, 120)
        self.frames_agachado = cortar(self.anim_agachado, 120)
        self.frames_dash = cortar(self.anim_dash, 120)
        self.frames_caminar_agachado = cortar(self.anim_caminar_agachado, 120)
        self.frames_transcicion_agachado = cortar(self.anim_transcicion_agachado, 120)
        self.frames_full_agachado = cortar(self.anim_full_agachado, 120)
        self.frames_death = cortar(self.anim_death, 120)
        self.frames_death_quieto = cortar(self.anim_death_quieto, 120)
        self.frames_darse_vuelta = cortar(self.anim_darse_vuelta, 120)
        self.frames_wallslide = cortar(self.anim_wallslide, 120)
        self.frame_actual = self.frames_quieto[0].copy()
        self.frames_ataque_movimiento = cortar(self.anim_ataque_movimiento,120)
        self.frames_ataque_quieto = cortar(self.anim_ataque_quieto,120)
        self.frames_ataque_agachado = cortar(self.anim_ataque_agachado,120)
        self.frames_ataque_movimiento_2 = cortar(self.anim_ataque_movimiento_2,120)
        self.frames_ataque_quieto_2 = cortar(self.anim_ataque_quieto_2,120)
    # --------------------------------------------------------
    # PUNTO 1.2: Física (se llama cada frame desde main)
    # --------------------------------------------------------
    # --------------------------------------------------------
    # PUNTO 1.4.1: Entrada/salida de la animación de ataque
    # --------------------------------------------------------
    def configurar_mundo(self, ancho, alto, solidos,  liquidos=None):
                self.ancho_mundo = ancho
                self.alto_mundo = alto
                self.solidos = solidos
                self.agua = liquidos if liquidos is not None else []
    def iniciar_animacion_ataque(self, tipo, direccion, secuencia, velocidad=config.VELOCIDAD_ATAQUE_BASE):
            self.ataque_tipo = tipo
            self.ataque_direccion = direccion
            self.ataque_secuencia = secuencia
            self.ataque_velocidad = velocidad
            self.ataque_frame_index = 0.0
            
    
    def terminar_animacion_ataque(self):
        self.ataque_tipo = None
        self.ataque_frame_index = 0.0

    def update(self, dt, keys):
        vector_direccion = pygame.Vector2(0, 0)

        # ----- PUNTO 1.2.1: Temporizadores -----
        if self.dash_tiempo > 0:
            self.dash_tiempo -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.tiempo_destello > 0:
            self.tiempo_destello -= dt
        if self.jump_buffer > 0:
            self.jump_buffer -= dt
        if self.coyote > 0:
            self.coyote -= dt
        if self.tiempo_entre_salto_caida > 0:
            self.tiempo_entre_salto_caida -= dt
        if self.wall_jump_cooldown > 0:
            self.wall_jump_cooldown -= dt
        if self.dash_invulnerable > 0:
            self.dash_invulnerable -= dt
        if self.dash_bar_drenaje > 0:
            self.dash_bar_drenaje = max(0, self.dash_bar_drenaje - dt) 
            self.dash_bar_porcentaje = (self.dash_bar_drenaje / config.DASH_BAR_CAIDA)
        else:
            self.dash_bar_porcentaje = max(0.0, min(1.0, 1.0 - self.dash_cooldown / config.DASH_ESPERA))
        # ----- PUNTO 1.2.2: Destello de barra recargada -----
        if self.dash_cooldown <= 0 and not self.ya_destello:
            self.tiempo_destello = 0.15
            self.ya_destello = True
        if self.dash_tiempo > 0:
            self.ya_destello = False

        # Detectar una nueva pulsación de W para el salto desde la pared.
        w_actual = keys[pygame.K_w]
        w_just_pressed = w_actual and not self.w_was_pressed
        self.w_was_pressed = w_actual

        # PUNTO 3.1: Wall-jump, siempre en dirección OPUESTA a la
        # pared. En una esquina (dos paredes a la vez) se cancela,
        # porque si no elegiría una dirección y metería al jugador
        # dentro de la otra pared.
        if (
            w_just_pressed
            and not self.en_suelo
            and self.wall_jump_cooldown <= 0
            and (self.en_pared_izq or self.en_pared_der)
        ):
            if self.en_pared_izq and not self.en_pared_der:
                self.vel_x = config.VEL_CAMINAR
                self.direccion = 1
            elif self.en_pared_der and not self.en_pared_izq:
                self.vel_x = -config.VEL_CAMINAR
                self.direccion = -1
            else:
                # Esquina: no se wall-jumpea.
                self.wall_jump_cooldown = 0.15
                w_just_pressed = False

        if (
            w_just_pressed
            and not self.en_suelo
            and self.wall_jump_cooldown <= 0
            and (self.en_pared_izq or self.en_pared_der)
        ):
            if self.en_pared_izq:
                self.vel_x = config.VEL_CAMINAR
                self.direccion = 1
            elif self.en_pared_der:
                self.vel_x = -config.VEL_CAMINAR
                self.direccion = -1
            self.vel_y = config.FUERZA_SALTO
            self.en_suelo = False
            self.solto_w = False
            self.coyote = 0
            self.jump_buffer = 0
            self.en_wallslide = False
            self.walljump_armed = False
            self.wall_jump_cooldown = 0.15

        # Bloquear A/D desde el primer contacto con la pared.
        self.en_wallslide = (
            self.dash_tiempo <= 0
            and not self.en_suelo
            and self.vel_y > 0
            and w_actual
            and (self.en_pared_izq or self.en_pared_der)
        )

        # ----- PUNTO 1.2.3: MODO DASH -----
        if self.dash_tiempo > 0:
            self.vel_x = self.dash_dir.x * config.VEL_CORRER
            self.pos += self.dash_dir * config.VEL_DASH * dt

            self.tiempo_clon -= dt
            if self.tiempo_clon <= 0:
                if self.dash_dir.y < 0:
                    frames_estela = self.frames_saltar
                else:
                    frames_estela = self.frames_correr

                indice_estela = int(self.frame_index) % len(frames_estela)
                frame_estela = frames_estela[indice_estela]
                if self.direccion == -1:
                    frame_estela = pygame.transform.flip(frame_estela, True, False)

                self.estela.append({
                    "pos": pygame.Vector2(self.pos.x, self.pos.y),
                    "ancho": self.ancho,
                    "alto": self.alto,
                    "frame": frame_estela.copy(),
                    "vida": 1
                })
                self.tiempo_clon = self.intervalo_clon
            self.en_movimiento = True
        # ----- PUNTO 1.2.4: MODO NORMAL -----
        else:
            if self.ya_destello and self.dash_cooldown > 0:
                self.ya_destello = False

            # --- Velocidad base (caminar / correr) ---
            velocidad_actual = config.VEL_CORRER if keys[pygame.K_LSHIFT] else config.VEL_CAMINAR
            if self.en_agua:
                velocidad_actual *= config.AGUA_FACTOR_VELOCIDAD
            self.corriendo = bool(keys[pygame.K_LSHIFT])

            # --- Agachado (redimensiona hitbox, pies anclados) ---
            esta_agachado = keys[pygame.K_s] and self.en_suelo

            if esta_agachado:
                velocidad_actual *= 0.4
                fondo = self.hitbox.bottom
                self.hitbox.w = int(config.ANCHO_HITBOX * 1.3)
                self.hitbox.h = int(config.ALTO_HITBOX * 0.5)
                self.hitbox.bottom = fondo
            else:
                fondo = self.hitbox.bottom
                self.hitbox.size = (config.ANCHO_HITBOX, config.ALTO_HITBOX)
                self.hitbox.bottom = fondo

            self.ancho, self.alto = self.hitbox.size
            self.pos.x, self.pos.y = float(self.hitbox.x), float(self.hitbox.y)

            
            # --- Movimiento horizontal (A / D) ---
            objetivo = 0
            if self.en_wallslide:
                # Mientras W está mantenido, A/D no rompen el wall-slide.
                objetivo = 0
            elif self.wall_jump_cooldown <= 0:
                if keys[pygame.K_a]:
                    objetivo -= velocidad_actual
                    vector_direccion.x -= 1
                    self.direccion = -1
                if keys[pygame.K_d]:
                    objetivo += velocidad_actual
                    vector_direccion.x += 1
                    self.direccion = 1
            else:
                # Durante el impulso inicial no se anulan los controles.
                objetivo = self.vel_x

            if objetivo != 0:
                if self.en_suelo:
                    paso = config.ACELERACION * dt
                else:
                    paso = config.ACELERACION * config.CONTROL_AEREO *  dt
            elif self.en_suelo:
                paso = config.FRICCION * dt
            else:
                paso = 0  

            if self.vel_x < objetivo:
                self.vel_x = min(self.vel_x + paso, objetivo)
            elif self.vel_x > objetivo:
                self.vel_x = max(self.vel_x - paso, objetivo)

            self.pos.x += self.vel_x * dt
            self.en_movimiento = abs(self.vel_x) > config.VEL_MOVIMIENTO_MINIMO
            

            # --- Gravedad + wall-slide (caída lenta pegado a pared) ---
            if self.en_agua:
                self.vel_y += config.GRAVEDAD * config.AGUA_FACTOR_GRAVEDAD * dt

                # En el agua el hundimiento es lento.
                if self.vel_y > config.AGUA_VEL_CAIDA:
                    self.vel_y = config.AGUA_VEL_CAIDA

                # Mantener W para nadar hacia arriba.
                if keys[pygame.K_w]:
                    self.vel_y = -config.AGUA_VEL_NADO
            else:
                self.vel_y += config.GRAVEDAD * dt

                # Techo de caída: sin esto la gravedad se acumula sin
                # límite y el jugador cae a miles de px/s.
                if self.vel_y > config.VEL_CAIDA_MAXIMA:
                    self.vel_y = config.VEL_CAIDA_MAXIMA

            self.pos.y += self.vel_y * dt
            if keys[pygame.K_s] and not self.en_suelo:
                self.vel_y += config.GRAVEDAD * config.MULT_CAIDA * dt
            pegado_izq = self.en_pared_izq and keys[pygame.K_w]
            pegado_der = self.en_pared_der and keys[pygame.K_w]
            if (
                not self.en_suelo
                and (pegado_izq or pegado_der)
                and self.vel_y > config.VEL_CAIDA_WALLSLIDE
            ):
                self.vel_y = config.VEL_CAIDA_WALLSLIDE

            # --- Salto variable (cortar al soltar W) ---
            if (
                not keys[pygame.K_w]
                and self.vel_y < 0
                and not self.solto_w
                and self.wall_jump_cooldown <= 0
            ):
                self.vel_y *= 0.8
                self.solto_w = True
                self.coyote = 0

            # --- Salto directo + bunny-hop (W sostenida) ---
            if (
                keys[pygame.K_w]
                and (self.en_suelo or self.coyote > 0)
                and not esta_agachado
                and not self.en_wallslide
            ):
                self.vel_y = config.FUERZA_SALTO * (
                    config.AGUA_FACTOR_SALTO if self.en_agua else 1.0
                )
                self.pos.y += self.vel_y * dt
                self.en_suelo = False
                self.solto_w = False
                self.coyote = 0

            # --- Jump buffer (salto anticipado en aire) ---
            if (
                keys[pygame.K_w]
                and not self.en_suelo
                and not self.en_wallslide
                and self.wall_jump_cooldown <= 0
            ):
                if self.jump_buffer <= 0 and not self.solto_w:
                    self.jump_buffer = config.JUMP_BUFFER_DURACION

            un_requisito_para_saltar = self.jump_buffer > 0

            if un_requisito_para_saltar and self.en_suelo and not esta_agachado:
                self.vel_y = config.FUERZA_SALTO * (
                    config.AGUA_FACTOR_SALTO if self.en_agua else 1.0
                )
                self.pos.y += self.vel_y * dt
                self.en_suelo = False
                self.solto_w = False
                self.coyote = 0
                desatarcar(self.hitbox, self.solidos, self.vel_x, self.vel_y)
                self.jump_buffer = 0

            # --- Activar dash (ESPACIO) ---
            if keys[pygame.K_SPACE] and self.dash_cooldown <= 0:
                # W/S añaden la componente vertical aunque también se pulse A/D.
                if keys[pygame.K_w]:
                    vector_direccion.y -= 1
                elif keys[pygame.K_s]:
                    vector_direccion.y += 1

                if vector_direccion.length_squared() > 0:
                    self.dash_dir = vector_direccion.normalize().copy()
                    self.dash_tiempo = config.DASH_DURACION
                    self.dash_cooldown = config.DASH_ESPERA
                    self.dash_bar_drenaje = config.DASH_BAR_CAIDA
                    self.dash_bar_porcentaje = 1.0
                    self.dash_invulnerable = config.DASH_INVULNERABLE
                    self.vel_y = 0
    
        # ----- PUNTO 1.2.5: Límites del nivel (los manda la hitbox) -----
        bottom_previo = self.hitbox.bottom
        self.hitbox.topleft = (self.pos.x, self.pos.y)

        # PUNTO 9.2: Frenar contra los sólidos.
        #
        # OJO: aquí NO se llama a desatarcar, y es importante. Si se
        # hiciera antes de resolver, sacaría al jugador del terreno
        # antes de que resolver_solidos pudiera marcar en_suelo, y se
        # quedaría "en_suelo = False" aunque estuviera parado: no
        # podría saltar nunca.
        en_suelo, bloqueo_x, bloqueo_arriba = resolver_solidos(
            self.hitbox,
            self.vel_x,
            self.vel_y,
            self.solidos,
            bottom_previo
        )

        if not en_suelo and self.en_suelo:
            en_suelo = hay_suelo_debajo(
                self.hitbox,
                self.solidos
            )

        if bloqueo_x:
            self.vel_x = 0.0

        if bloqueo_arriba:
            self.vel_y = 0.0

        self.en_suelo = en_suelo
        desatarcar(self.hitbox, self.solidos, self.vel_x, self.vel_y)

        if en_suelo:
            self.vel_y = 0.0
            self.solto_w = False
            self.coyote = config.COYOTE_DURACION

        # PUNTO 9.2.1: Bordes del mapa (no hay tiles ahí).
        if self.hitbox.left < 0:
            self.hitbox.left = 0
            if self.vel_x < 0:
                self.vel_x = 0

        if self.hitbox.right > self.ancho_mundo:
            self.hitbox.right = self.ancho_mundo
            if self.vel_x > 0:
                self.vel_x = 0

        if self.hitbox.top < 0:
            self.hitbox.top = 0
            self.vel_y = 0

        if limitar_abajo(self.hitbox, self.solidos, self.alto_mundo):
            self.vel_y = 0
            self.en_suelo = True

        # La posición obedece a la hitbox
        self.pos.x = float(self.hitbox.x)
        self.pos.y = float(self.hitbox.y)
        self.en_agua = self.hitbox.collidelist(self.agua) != -1
        if (
            not self.en_agua
            and self.estaba_en_agua
            and keys[pygame.K_w]
            and not self.en_suelo
        ):
            self.vel_y = config.FUERZA_SALTO * config.AGUA_FACTOR_SALTO

        self.estaba_en_agua = self.en_agua

        # PUNTO 9.2.2: Paredes: tiles sólidos o borde del mapa.
        self.en_pared_izq = (
            self.hitbox.left <= 0
            or hay_pared(self.hitbox, self.solidos, "izq")
        )

        self.en_pared_der = (
            self.hitbox.right >= self.ancho_mundo
            or hay_pared(self.hitbox, self.solidos, "der")
        )

        # ----- Estado de animación (después de la física) -----
        esta_agachado = keys[pygame.K_s] and self.en_suelo
        wallslide_actual = (
            not self.en_suelo
            and self.vel_y > 0
            and keys[pygame.K_w]
            and (
                self.en_pared_izq
                or self.en_pared_der
            )
        )

        if wallslide_actual:
            self.en_wallslide = True
            self.walljump_armed = True
            self.jump_buffer = 0
            if self.en_pared_izq:
                self.direccion = -1
            elif self.en_pared_der:
                self.direccion = 1
        else:
            self.en_wallslide = False
            if self.en_suelo or not (self.en_pared_izq or self.en_pared_der):
                self.walljump_armed = False

        # --- Detectar el punto más alto del salto ---
        if (
            self.dash_tiempo <= 0
            and not self.en_suelo
            and self.vel_y_anterior < 0
            and self.vel_y >= 0
        ):
            self.tiempo_entre_salto_caida = 0.12
        self.vel_y_anterior = self.vel_y

        # --- Recordar qué variante de muerte corresponde ---
        if self.vida <= 0 and self.estado_anterior not in {"muerte", "muerte_quieto"}:
            self.muerte_movimiento = abs(self.vel_x) > config.VEL_MOVIMIENTO_MINIMO

        # --- Prioridad de estados ---
        if self.vida <= 0:
            self.estado = "muerte" if self.muerte_movimiento else "muerte_quieto"
        elif self.dash_tiempo > 0:
            self.estado = "dash"
        elif wallslide_actual:
            self.estado = "wallslide"
        elif not self.en_suelo:
            if self.tiempo_entre_salto_caida > 0:
                self.estado = "entre"
            else:
                self.estado = "caer" if self.vel_y > 0 else "saltar"
        elif esta_agachado and abs(self.vel_x) > 10:
            self.estado = "agachado_caminando"
        elif esta_agachado:
            # Se conserva el estado original de agachado quieto.
            self.estado = "agachado"
        elif abs(self.vel_x) > 10:
            self.estado = "correr"
        else:
            self.estado = "quieto"

        if self.estado != self.estado_anterior:
            self.frame_index = 0.0
            self.estado_anterior = self.estado



        # ----- PUNTO 1.2.6: Envejecer estela -----
        for p in self.estela[:]:
            p["vida"] -= dt * 4.0
            if p["vida"] <= 0:
                self.estela.remove(p)

    # --------------------------------------------------------
    # PUNTO 1.3: Daño (resetea el contador)
    # --------------------------------------------------------
    def recibir_daño(self, cant):
        if self.dash_invulnerable > 0:
            return
        self.vida -= cant
        self.golpes = 0

    # --------------------------------------------------------
    # PUNTO 1.3.1: Reaparecer en el punto de inicio
    # --------------------------------------------------------
    def reaparecer(self, x, y):
        """
        Vuelve a poner al jugador en el punto del spawn con la vida
        llena. Se llama cuando se muere.

        Se reinicia TODO lo que se pueda haber quedado a medias: de lo
        contrario el jugador reaparece con la vida a medias, con el
        dash en curso o medio enterrado en el suelo.
        """
        # --- Posición: los pies en el spawn ---
        self.hitbox.midbottom = (x, y)
        self.pos.update(
            float(self.hitbox.x),
            float(self.hitbox.y)
        )

        # --- Vida y contador de combo ---
        self.vida = config.JUGADOR_VIDA
        self.golpes = 0

        # --- Física ---
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.en_suelo = True
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.solto_w = False

        # --- Dash ---
        self.dash_tiempo = 0
        self.dash_cooldown = 0
        self.dash_dir.update(0, 0)
        self.dash_invulnerable = 0.0
        self.dash_bar_porcentaje = 1.0
        self.dash_bar_drenaje = 0.0
        self.ya_destello = True
        self.tiempo_destello = 0

        # --- Paredes y wall-jump ---
        self.en_wallslide = False
        self.en_pared_izq = False
        self.en_pared_der = False
        self.walljump_armed = False
        self.wall_jump_cooldown = 0.0
        self.w_was_pressed = False

        # --- Estado visual ---
        self.estela.clear()
        self.en_movimiento = False
        self.corriendo = False
        self.en_agua = False
        self.estaba_en_agua = False
        self.vel_y_anterior = 0.0
        self.tiempo_entre_salto_caida = 0.0
        self.muerte_movimiento = False

        # PUNTO 1.3.1.1: La animación de muerte se corta aquí, o el
        # jugador se quedaría congelado en ese estado.
        self.estado = "quieto"
        self.estado_anterior = "quieto"
        self.frame_index = 0.0

        # --- Ataque ---
        self.ataque_tipo = None
        self.ataque_frame_index = 0.0

    @staticmethod
    def _centrar_sprite_sobre_hitbox(frame, centro_x, suelo):
        """Alinea los píxeles visibles del sprite con el centro de la hitbox."""
        caja_visible = frame.get_bounding_rect()
        desplazamiento_x = caja_visible.centerx - frame.get_width() / 2
        return frame.get_rect(
            midbottom=(centro_x - desplazamiento_x, suelo)
        )

    # --------------------------------------------------------
    # PUNTO 1.4: Dibujo del jugador + estela (dibuja la hitbox)
    # --------------------------------------------------------
    def draw(self, surface, keys, dt):
        # PUNTO 1.4.2: Elegir sprites de ataque o animación normal.
        # --- Cuerpo (la hitbox) ---
        direccion_visual = self.ataque_direccion

        if self.ataque_tipo is not None:
            if self.ataque_tipo == "movimiento":
                if self.ataque_secuencia == 2:
                    sprites = self.frames_ataque_movimiento_2
                else:
                    sprites = self.frames_ataque_movimiento
            elif self.ataque_tipo == "agachado":
                sprites = self.frames_ataque_agachado
            else:
                if self.ataque_secuencia == 2:
                    sprites = self.frames_ataque_quieto_2
                else:
                    sprites = self.frames_ataque_quieto

            self.ataque_frame_index += dt * self.ataque_velocidad

            indice = min(
                int(self.ataque_frame_index),
                len(sprites) - 1
            )

            frame = sprites[indice]
            direccion_visual = self.ataque_direccion

        else:
            sprites = {"quieto": self.frames_quieto,
                        "correr": self.frames_correr,
                        "saltar": self.frames_saltar,
                        "caer": self.frames_caer,
                        "agachado": self.frames_agachado,
                        "dash": self.frames_dash,
                        "agachado_caminando": self.frames_caminar_agachado,
                        "agachado_transicion": self.frames_transcicion_agachado,
                        "agachado_full": self.frames_full_agachado,
                        "muerte": self.frames_death,
                        "muerte_quieto": self.frames_death_quieto,
                        "darse_vuelta": self.frames_darse_vuelta,
                        "wallslide": self.frames_wallslide,
                        "entre": self.frames_anim_entre_salto_caida}[self.estado]

            self.frame_index += dt * 10

            if self.estado in self.animaciones_una_vez:
                indice = min(
                    int(self.frame_index),
                    len(sprites) - 1
                )
            else:
                indice = int(self.frame_index) % len(sprites)

            frame = sprites[indice]
            direccion_visual = self.direccion

        if direccion_visual == -1:
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(
            frame,
            self._centrar_sprite_sobre_hitbox(
                frame,
                self.hitbox.centerx,
                self.hitbox.bottom
            )
        )
        
          # --- Estela del dash ---
            
        for p in self.estela:
            imagen = p["frame"].copy()
            imagen.set_alpha(max(0, int(255 * p["vida"])))
        
            rect = self._centrar_sprite_sobre_hitbox(
                imagen,
                p["pos"].x + p["ancho"] / 2,
                p["pos"].y + p["alto"]
            )
        
            surface.blit(imagen, rect)
                # --- Color según estado ---
            if self.dash_tiempo > 0:
                color_actual = (255, 255, 0)
            else:
                color_actual = (0, 220, 255) if keys[pygame.K_LSHIFT] and self.en_movimiento and self.en_suelo else "blue"
