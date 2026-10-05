import os
import pygame
import pytmx
import config
import xml.etree.ElementTree as ET
MASCARA_GID = 0x0FFFFFFF


class Mapa:
    # --------------------------------------------------------
    # PUNTO 2.1: Cargar el archivo de Tiled
    # --------------------------------------------------------
    def __init__(self, nombre_archivo):
        self.ruta = os.path.join(
            config.RUTA_ASSETS,
            "mapa",
            nombre_archivo
        )

        self.tmx = pytmx.load_pygame(self.ruta, scaling=1)

        self.ancho = self.tmx.width * self.tmx.tilewidth
        self.alto = self.tmx.height * self.tmx.tileheight

        self.spawns = self._leer_spawns()
        self.formas = self._leer_formas()

    def _imagen_de_capa(self, capa):
        """
        pytmx se confunde cuando hay archivos con el mismo nombre
        en carpetas distintas, asi que cargamos la imagen a mano.
        """
        ruta = os.path.normpath(
            os.path.join(os.path.dirname(self.ruta), capa.source)
        )

        if os.path.isfile(ruta):
            return pygame.image.load(ruta).convert_alpha()

        return capa.image
 # --------------------------------------------------------
    # PUNTO 2.2: Leer los puntos de aparición
    # --------------------------------------------------------
    def _leer_formas(self):
        """
        Cada tile puede tener una forma de colisión dibujada en Tiled
        (Edit → Tile Collision Editor). Acá se leen.
        """
        formas = {}
        base = os.path.dirname(self.ruta)
        raiz = ET.parse(self.ruta).getroot()

        for conjunto in raiz.findall("tileset"):
            primero = int(conjunto.get("firstgid"))
            archivo = conjunto.get("source")

            ruta_tsx = os.path.join(base, archivo)

            # utf-8-sig porque algunos .tsx traen BOM y el parser se cae.
            with open(ruta_tsx, "rb") as archivo_binario:
                contenido = archivo_binario.read().decode(
                    "utf-8-sig",
                    errors="replace"
                )

            arbol = ET.fromstring(contenido)

            for tile in arbol.findall("tile"):
                lista = []

                for grupo in tile.findall("objectgroup"):
                    for objeto in grupo.findall("object"):
                        lista.append((
                            objeto.get("type") or "",
                            float(objeto.get("x") or 0),
                            float(objeto.get("y") or 0),
                            float(objeto.get("width") or 0),
                            float(objeto.get("height") or 0)
                        ))

                if lista:
                    formas[primero + int(tile.get("id"))] = lista

        return formas
    
    def _leer_spawns(self):
        spawns = {}

        capa = self.tmx.get_layer_by_name("spawpoints")

        if capa is None:
            return spawns

        # En pytmx 3.x la capa de objetos es una lista.
        for objeto in capa:
            spawns[objeto.name] = pygame.Vector2(
                objeto.x,
                objeto.y
            )

        return spawns
    

    def obtener_spawn(self, nombre):
        return self.spawns.get(nombre)

    def spawns_nombre(self, nombre):
        """
        Devuelve TODOS los puntos que tienen ese nombre.
        Necesario cuando hay varios enemigos con el mismo nombre.
        """
        capa = self.tmx.get_layer_by_name("spawpoints")

        if capa is None:
            return []

        return [
            pygame.Vector2(objeto.x, objeto.y)
            for objeto in capa
            if objeto.name == nombre
        ]
    # --------------------------------------------------------
    # PUNTO 2.3: Dibujar el mapa
    # --------------------------------------------------------
    def draw(self, surface):
        # Color de respaldo donde no llega ninguna capa.
        surface.fill(config.COLOR_FONDO_MAPA)

        # Primero los fondos: se repiten en horizontal.
        for capa in self.tmx.layers:
            if isinstance(capa, pytmx.TiledImageLayer):
                imagen = self._imagen_de_capa(capa)

                surface.blit(
                    imagen,
                    (int(capa.offsetx), int(capa.offsety))
                )
        # Después los tiles: sol, arboles, agua, piso, pasto.
        for capa in self.tmx.layers:
            if isinstance(capa, pytmx.TiledTileLayer):
                for x, y, imagen in capa.tiles():
                    if imagen is not None:
                        surface.blit(
                            imagen,
                            (
                                x * self.tmx.tilewidth,
                                y * self.tmx.tileheight
                            )
                        )
    def _capas_tiles(self):
        for capa in self.tmx.layers:
            if isinstance(capa, pytmx.TiledTileLayer):
                yield capa

    def _tiles_de_capa(self, capa, con_formas):
        rectangulos = []

        for y, fila in enumerate(capa.data):
            for x, gid_crudo in enumerate(fila):
                if gid_crudo == 0:
                    continue

                gid = gid_crudo & MASCARA_GID
                px = x * self.tmx.tilewidth
                py = y * self.tmx.tileheight

                if con_formas:
                    # Usa la forma que dibujaste en Tiled.
                    for clase, ox, oy, ancho, alto in self.formas.get(gid, []):
                        rectangulos.append(
                            pygame.Rect(
                                int(px + ox),
                                int(py + oy),
                                int(ancho),
                                int(alto)
                            )
                        )
                else:
                    # Tile completo, para zonas como el agua.
                    rectangulos.append(
                        pygame.Rect(
                            px,
                            py,
                            self.tmx.tilewidth,
                            self.tmx.tileheight
                        )
                    )

        return rectangulos

    def solidos(self, capas=None):
        """
        Tiles con forma de colisión. Si pasás 'capas', solo mira esas.
        """
        rectangulos = []

        for capa in self._capas_tiles():
            if capas is not None and capa.name not in capas:
                continue

            if capa.properties.get("es_agua", False):
                continue

            rectangulos.extend(
                self._tiles_de_capa(capa, con_formas=True)
            )

        return rectangulos

    def liquidos(self):
        """Tiles de las capas marcadas con es_agua = true."""
        rectangulos = []

        for capa in self._capas_tiles():
            if not capa.properties.get("es_agua", False):
                continue
            rectangulos.extend(
                self._tiles_de_capa(capa, con_formas=False)
            )

        return rectangulos

