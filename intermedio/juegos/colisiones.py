import pygame


# --------------------------------------------------------
# PUNTO 9.1: Sacar la hitbox de los sólidos del mapa
# --------------------------------------------------------
def resolver_solidos(hitbox, vel_x, vel_y, solidos, bottom_previo):
    """
    Empuja la hitbox fuera de los sólidos, eje por eje.
    Devuelve: (en_suelo, bloqueo_x, bloqueo_arriba)
    """
    en_suelo = False
    bloqueo_x = False
    bloqueo_arriba = False

    # Vertical: solo cuenta como ATERRIZAJE si los pies venían de
    # arriba. Si no, es que el jugador chocó de lado contra un
    # escalón.
    #
    # Con vel_y == 0 (durante el dash) NO se resuelve el suelo aquí:
    # el dash entra por debajo de los tiles al subir en diagonal, y
    # tomarlos como suelo lo subía de golpe 63 px. Ese caso lo
    # resuelve desatarcar, que elige la salida más corta.
    if vel_y > 0:
        for solido in solidos:
            if not hitbox.colliderect(solido):
                continue
            if bottom_previo > solido.top + 2:
                continue
            hitbox.bottom = min(hitbox.bottom, solido.top)
            en_suelo = True

    elif vel_y < 0:
        # El techo es el SOLIDO MÁS BAJO de los que toca, no la suma.
        techo = None
        mitad = hitbox.width / 2

        for solido in solidos:
            if not hitbox.colliderect(solido):
                continue

            # Solo cuenta como techo si el sólido está REALMENTE
            # encima (su borde inferior no baja del centro del
            # personaje) y además lo golpea de frente.
            #
            # Sin el primer filtro, un tile que estaba abajo-derecha
            # con solo 16 px de solapamiento lateral se tomaba como
            # techo y empujaba al jugador 60 px hacia abajo.
            # Sin el segundo, un roce de canto lo empujaba 20 px.
            if solido.bottom > hitbox.centery:
                continue

            solape_x = min(hitbox.right, solido.right) - max(
                hitbox.left,
                solido.left
            )

            if solape_x <= mitad:
                continue

            if techo is None or solido.bottom < techo:
                techo = solido.bottom

        if techo is not None:
            hitbox.top = techo
            bloqueo_arriba = True

    # Horizontal: frena contra el escalón sin subirlo.
    #
    # Solo si salir de LADO es la salida más corta. Si el personaje
    # está metido en el tile por arriba o por abajo (el dash a 700
    # px/s lo hace), empujarlo de lado lo lanzaba 24 px de golpe.
    # Si de lado no compensa, lo deja a desatarcar, que elige bien.
    if vel_x > 0:
        for solido in solidos:
            if not hitbox.colliderect(solido):
                continue

            vertical = min(
                solido.bottom - hitbox.top,
                hitbox.bottom - solido.top
            )

            if vertical < hitbox.right - solido.left:
                continue

            hitbox.right = min(hitbox.right, solido.left)
            bloqueo_x = True

    elif vel_x < 0:
        for solido in solidos:
            if not hitbox.colliderect(solido):
                continue

            vertical = min(
                solido.bottom - hitbox.top,
                hitbox.bottom - solido.top
            )

            if vertical < solido.right - hitbox.left:
                continue

            hitbox.left = max(hitbox.left, solido.right)
            bloqueo_x = True

    return en_suelo, bloqueo_x, bloqueo_arriba


# --------------------------------------------------------
# PUNTO 9.1.0: Red de seguridad si la hitbox acaba dentro del terreno
# --------------------------------------------------------
def desatarcar(hitbox, solidos, vel_x=0.0, vel_y=0.0):
    """
    Saca la hitbox de los sólidos.

    Hay dos reglas:

    1. Si el personaje venía moviéndose en vertical y el sólido está
       de verdad bajo (o sobre) él, se apoya (o frena) ahí. Si no,
       al caer a 1000 px/s y meterse 18 px en el suelo, la salida más
       corta era de lado (16 px) y lo teletransportaba en horizontal
       en vez de dejarlo apoyado arriba.
    2. Si no se está moviendo en vertical (por ejemplo un empujón
       externo), sale por la salida MÁS CORTA de las cuatro. Antes
       solo se salía arriba/abajo, y un roce de 1 px de lado lo
       empujaba 20 px hacia abajo.
    """
    for _ in range(8):
        mitad = hitbox.width / 2
        chocan = [s for s in solidos if hitbox.colliderect(s)]

        if not chocan:
            return

        # Un tile cuenta solo si el personaje lo tiene ENCIMA de la
        # mitad del cuerpo. Si se solapan la mitad o menos de lado,
        # el jugador solo lo rozó de canto, y empujarlo de arriba
        # abajo lo teletransportaba (rozando un tile nadando en el
        # agua lo lanzaba 64 px hacia arriba).
        verticales = [
            s
            for s in chocan
            if min(hitbox.right, s.right) - max(hitbox.left, s.left) > mitad
        ]

        # REGLA 1a: venía cayendo -> se apoya en la superficie.
        if vel_y > 0:
            suelos = [s for s in verticales if s.top >= hitbox.centery]

            if suelos:
                # El más alto (el primero que golpea al bajar), no
                # todos: aplicarlos uno a uno atravesaba la columna
                # entera de tiles.
                hitbox.bottom = min(s.top for s in suelos)
                continue

        # REGLA 1b: venía subiendo -> frena con el techo.
        if vel_y < 0:
            techos = [s for s in verticales if s.bottom <= hitbox.centery]

            if techos:
                hitbox.top = min(s.bottom for s in techos)
                continue

        # REGLA 2: salida más corta de las cuatro.
        movido = False

        for solido in chocan:
            arriba = solido.bottom - hitbox.top
            abajo = hitbox.bottom - solido.top
            izquierda = solido.right - hitbox.left
            derecha = hitbox.right - solido.left

            minima = min(arriba, abajo, izquierda, derecha)

            if minima == arriba:
                hitbox.top = solido.bottom
            elif minima == abajo:
                hitbox.bottom = solido.top
            elif minima == izquierda:
                hitbox.left = solido.right
            else:
                hitbox.right = solido.left

            movido = True

        if not movido:
            return


# --------------------------------------------------------
# PUNTO 9.1.1: Apoyar en el terreno al tocar el borde inferior
# --------------------------------------------------------
def limitar_abajo(hitbox, solidos, alto_mundo):
    """
    Si el personaje se pasó del borde inferior del mapa, lo deja
    apoyado en la SUPERFICIE del terreno y no en el borde.

    Hace falta porque el último tile del mapa va de y=352 a y=382 y
    el borde está en y=384. Si se lo deja en el borde queda 2 px
    dentro del suelo; al frame siguiente bottom_previo = 384
    descarta el aterrizaje (384 > 382 + 2) y el personaje atraviesa
    el piso cayendo en bucle.

    Devuelve True si hubo que limitar.
    """
    if hitbox.bottom <= alto_mundo:
        return False

    hitbox.bottom = alto_mundo

    superficies = [
        solido.top
        for solido in solidos
        if solido.top < alto_mundo and hitbox.colliderect(solido)
    ]

    if superficies:
        hitbox.bottom = min(superficies)

    # Con vel_y = 1.0 (fingiendo que venía cayendo) sale por la
    # superficie, que es lo que se quiere al llegar al borde.
    desatarcar(hitbox, solidos, 0.0, 1.0)

    return True


# --------------------------------------------------------
# PUNTO 9.1.2: Comprobar si hay suelo justo debajo
# --------------------------------------------------------
def hay_suelo_debajo(hitbox, solidos, margen=2):
    """Mira un poco más abajo para que en_suelo no parpadee."""
    hitbox.bottom += margen

    apoyado = hitbox.collidelist(solidos) != -1

    hitbox.bottom -= margen

    return apoyado


# --------------------------------------------------------
# PUNTO 9.1.3: Comprobar si hay pared pegada a un lado
# --------------------------------------------------------
def hay_pared(hitbox, solidos, lado, margen=2):
    if lado == "der":
        hitbox.right += margen
    else:
        hitbox.left -= margen

    pegado = hitbox.collidelist(solidos) != -1

    if lado == "der":
        hitbox.right -= margen
    else:
        hitbox.left += margen

    return pegado