import pygame
import config
from personaje_cuadrado import Player
from hud import draw_hud
from enemigo import Enemigo
from espada import Espada
from combate import SistemaCombate
from mapa import Mapa
from camara import Camara
from colisiones import desatarcar

def calcular_area_ventana(tamano_ventana):
    """Ajusta el juego al centro de la ventana sin deformarlo."""
    ancho_ventana, alto_ventana = tamano_ventana

    escala = min(
        ancho_ventana / config.ANCHO_VIRTUAL,
        alto_ventana / config.ALTO_VIRTUAL
    )

    ancho = max(1, int(config.ANCHO_VIRTUAL * escala))
    alto = max(1, int(config.ALTO_VIRTUAL * escala))

    return pygame.Rect(
        (ancho_ventana - ancho) // 2,
        (alto_ventana - alto) // 2,
        ancho,
        alto
    )


def gestionar_enemigos(enemigos, jugador):
    """
    Decide cuántos enemigos pueden estar alerta a la vez.

    Sin esto los 11 enemigos del mapa detectan al jugador a la vez y
    es imposible jugar. Se quedan alerta como mucho
    config.ENEMIGO_ACTIVOS_MAXIMO, y entran los más cercanos.

    Un enemigo ya activo no pierde el turno porque otro esté más
    cerca: solo se le va la "memoria" (ENEMIGO_MEMORIA segundos) y
    entonces vuelve al Idle.
    """
    if jugador is None or jugador.vida <= 0:
        for enemigo in enemigos:
            enemigo.desactivar()

        return

    activos = [e for e in enemigos if e.activo and e.vivo]

    # PUNTO 1.7.1.1: También hay que PODER apagar. Si el jugador le
    # pega a un enemigo que estaba en Idle, ese enemigo se activa en
    # el acto y nos pasamos del tope (se vio 5 activos con tope 3).
    # Se apagan primero los más lejanos.
    if len(activos) > config.ENEMIGO_ACTIVOS_MAXIMO:
        activos.sort(
            key=lambda e: e.distancia_jugador(jugador),
            reverse=True
        )

        for sobra in activos[config.ENEMIGO_ACTIVOS_MAXIMO:]:
            sobra.desactivar()

        activos = activos[:config.ENEMIGO_ACTIVOS_MAXIMO]

    lugares = config.ENEMIGO_ACTIVOS_MAXIMO - len(activos)

    if lugares <= 0:
        return

    candidatos = [
        e
        for e in enemigos
        if e.vivo and not e.activo and e.ve_a(jugador)
    ]

    # Los más cercanos al jugador alertan primero.
    candidatos.sort(key=lambda e: e.distancia_jugador(jugador))

    for enemigo in candidatos[:lugares]:
        enemigo.activar()

# ============================================================
# PUNTO 1: INICIALIZACIÓN
# ============================================================
pygame.init()
screen = pygame.display.set_mode((1280, 720),pygame.RESIZABLE)
pantalla_virtual = pygame.Surface((config.ANCHO_VIRTUAL, config.ALTO_VIRTUAL))
clock = pygame.time.Clock()
running = True
dt = 0
# PUNTO 2.0: Cargar el mapa de Tiled.
mapa = Mapa("nivel1.tmx")
spawn_jugador = mapa.obtener_spawn("jugador")
spawn_espada = mapa.obtener_spawn("espada")
# Los enemigos NO se piden con obtener_spawn: hay 11 puntos con ese
# nombre y el diccionario spawns solo guardaba el último. Para varios
# hay que usar spawns_nombre, que devuelve la lista entera.

# PUNTO 2.0.2: El mundo se dibuja aparte y la cámara lo recorta.
superficie_mundo = pygame.Surface((mapa.ancho, mapa.alto))
camara = Camara(mapa)

player = Player()
combate = SistemaCombate()
# PUNTO 2.0.3: El punto del mapa marca donde pisan los pies.
player.hitbox.midbottom = spawn_jugador
player.pos.update(player.hitbox.x, player.hitbox.y)

espada = Espada(spawn_espada.x, spawn_espada.y)
solidos = mapa.solidos(capas=("piso",))
agua = mapa.liquidos()

# PUNTO 8.1: Hay varios puntos llamados 'Enemigo' en el mapa,
# as�� que se crea uno por cada punto (el diccionario spawns
# solo guardaba el último).
enemigos = [
    Enemigo(spawn.x, spawn.y)
    for spawn in mapa.spawns_nombre("Enemigo")
]

player.configurar_mundo(mapa.ancho, mapa.alto, solidos, agua)
espada.configurar_mundo(mapa.ancho, mapa.alto, solidos)

for enemigo in enemigos:
    enemigo.configurar_mundo(mapa.ancho, mapa.alto, solidos)
    desatarcar(enemigo.hitbox, solidos, enemigo.vel_x, enemigo.vel_y)

desatarcar(espada.hitbox, solidos, 0.0, espada.vel_y)

# PUNTO 1.7.11: Tiempo que falta para reaparecer. Si es 0 o menos,
# el jugador está vivo.
tiempo_reaparicion = 0.0

# ============================================================
# PUNTO 2: BUCLE PRINCIPAL
# ============================================================
while running:
    
    # --------------------------------------------------------
    # PUNTO 2.1.0: Flags de entrada de este frame
    # --------------------------------------------------------
    recoger_presionado = False
    soltar_presionado = False
    ataque_presionado = False
    # --------------------------------------------------------
    # PUNTO 2.1: Eventos del sistema
    # --------------------------------------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # PUNTO 2.1.1: E recoge el arma cercana.
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            recoger_presionado = True

        # PUNTO 2.1.2: Q suelta el arma equipada.
        elif (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_q
        ):
            soltar_presionado = True

        # PUNTO 2.1.3: Click izquierdo inicia un ataque.
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            ataque_presionado = True

        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(
                (event.w, event.h),
                pygame.RESIZABLE
            )

    # --------------------------------------------------------
    # PUNTO 2.2: Lógica (update)
    # --------------------------------------------------------

    keys = pygame.key.get_pressed()

    # PUNTO 2.2.1: Convertir el mouse de pantalla a coordenadas virtuales.
    area_ventana = calcular_area_ventana(screen.get_size())

    mouse_x, mouse_y = pygame.mouse.get_pos()
    mouse_virtual_x = (
        (mouse_x - area_ventana.x)
        * config.ANCHO_VIRTUAL
        / area_ventana.width
    )

    player.update(dt, keys)

    # PUNTO 1.7.12: Reaparición del jugador. Se comprueba aquí, antes
    # de que los enemigos cambien de estado, para que no ataquen a un
    # jugador que ya está muerto.
    if player.vida <= 0:
        if tiempo_reaparicion <= 0:
            tiempo_reaparicion = config.REAPARICION_ESPERA
        else:
            tiempo_reaparicion -= dt

            if tiempo_reaparicion <= 0:
                tiempo_reaparicion = 0.0
                player.reaparecer(spawn_jugador.x, spawn_jugador.y)
                desatarcar(player.hitbox, solidos, 0.0, 0.0)
                player.pos.update(
                    float(player.hitbox.x),
                    float(player.hitbox.y)
                )
    else:
        tiempo_reaparicion = 0.0

    # PUNTO 2.2.2: Actualizar la IA y la física de todos los enemigos.
    # Cada enemigo decide su estado según lo que el gestor le dejó
    # en el frame anterior.
    for enemigo in enemigos:
        enemigo.update(dt, player)

    # PUNTO 2.2.3: Resolver la colisión física entre jugador y enemigos.
    for enemigo in enemigos:
        if not enemigo.vivo:
            continue

        if not player.hitbox.colliderect(enemigo.hitbox):
            continue

        dx_izq = player.hitbox.right - enemigo.hitbox.left    # entró por izquierda
        dx_der = enemigo.hitbox.right - player.hitbox.left    # entró por derecha
        dy_arr = player.hitbox.bottom - enemigo.hitbox.top    # cayó encima
        dy_aba = enemigo.hitbox.bottom - player.hitbox.top    # golpe desde abajo
        empuje = min(dx_izq, dx_der, dy_arr, dy_aba)
        if empuje == dx_izq:
            player.hitbox.right = enemigo.hitbox.left
        elif empuje == dx_der:
            player.hitbox.left = enemigo.hitbox.right
        elif empuje == dy_arr:
            player.hitbox.bottom = enemigo.hitbox.top
            player.vel_y = 0
            player.en_suelo = True
        else:
            player.hitbox.top = enemigo.hitbox.bottom
            player.vel_y = 0

        player.pos.x = float(player.hitbox.x)
        player.pos.y = float(player.hitbox.y)

        # PUNTO 9.3: El empujón puede meter al jugador en un
        # sólido, así que se lo saca enseguida.
        desatarcar(player.hitbox, solidos, player.vel_x, player.vel_y)
        player.pos.x = float(player.hitbox.x)
        player.pos.y = float(player.hitbox.y)

        break

    # PUNTO 2.2.4: Actualizar combate, ataque, dirección y hitbox.
    combate.update(
        dt,
        keys,
        player,
        ataque_presionado,
        mouse_virtual_x,
        enemigos
    )

    # PUNTO 1.7.13: Reparto de los enemigos que pueden estar alerta.
    #
    # Va DESPUÉS del combate a propósito: al golpear, el enemigo
    # afectado se activa en el acto, y si el gestor corriera antes se
    # quedaría un frame con un enemigo activo de más. Así el tope se
    # respeta siempre.
    gestionar_enemigos(enemigos, player)

    # PUNTO 2.2.5: Recoger el arma con E cuando el jugador está cerca.
    espada.update(dt)
    espada_cerca = espada.jugador_cerca(player.hitbox)
    if (
        recoger_presionado
        and not espada.recogida
        and espada_cerca
    ):
        if player.inventario.agregar(espada):
            espada.recogida = True

    # PUNTO 2.2.6: Soltar el arma equipada con Q.
    if soltar_presionado:
        item = player.inventario.soltar()

        if item is not None:
            item.recogida = False
            item.en_suelo = False
            item.vel_y = 0
            item.angulo = 0
            item.tiempo_visual = 0

            item.hitbox.midbottom = (
                player.hitbox.centerx,
                player.hitbox.top
            )

            item.zona_interaccion = item.hitbox.inflate(
                *config.ESPADA_ZONA_INFLAR
            )

            espada = item
# --------------------------------------------------------
# PUNTO 2.3: Dibujo
# --------------------------------------------------------
     # PUNTO 2.3.1: Dibujar el mundo completo sobre su superficie.
    camara.seguir(player)

    mapa.draw(superficie_mundo)
    player.draw(superficie_mundo, keys, dt)

    # PUNTO 1.7.14: Se dibujan también los que están muriendo, para
    # que se vea la animación de muerte antes de desaparecer. Los que
    # ya desaparecieron (muriendo = False y vivo = False) no se pintan.
    for enemigo in enemigos:
        if enemigo.vivo or enemigo.muriendo:
            enemigo.draw(superficie_mundo, dt)

    if not espada.recogida:
        espada.draw(
            superficie_mundo,
            espada_cerca
        )

    # PUNTO 2.3.2: Recortar la parte del mundo que ve la cámara.
    pantalla_virtual.fill(config.COLOR_FONDO_MAPA)
    pantalla_virtual.blit(
        superficie_mundo,
        (0, 0),
        camara.area()
    )

    # PUNTO 2.3.3: El HUD queda fijo, sin cámara.
    draw_hud(pantalla_virtual, player)
    

    # PUNTO 2.4: Escalado + FPS
    area_ventana = calcular_area_ventana(screen.get_size())

    pantalla_escalada = pygame.transform.scale(
        pantalla_virtual,
        area_ventana.size
    )

    screen.fill((0, 0, 0))
    screen.blit(pantalla_escalada, area_ventana.topleft)
    pygame.display.flip()

    dt = min(clock.tick(60) / 1000, 0.033)

pygame.quit()
