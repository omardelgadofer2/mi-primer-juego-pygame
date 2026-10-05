import pygame
from mapa import Mapa

pygame.init()
screen = pygame.display.set_mode((1024, 384))

mapa = Mapa("nivel1.tmx")

print("Mapa:", mapa.ancho, "x", mapa.alto)
for nombre, posicion in mapa.spawns.items():
    print("  spawn:", nombre, posicion)

corriendo = True

while corriendo:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            corriendo = False

    screen.fill((60, 30, 90))
    mapa.draw(screen)
    pygame.display.flip()

pygame.quit()