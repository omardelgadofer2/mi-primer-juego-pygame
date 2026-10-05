import pygame
import config
import os

class Inventario:
    def __init__(self, cantidad_slots=1):
        self.espacios = [None] * cantidad_slots
        self.slot_equipado = None

    @property
    def equipado(self):
        if self.slot_equipado is None:
            return None

        return self.espacios[self.slot_equipado]

    def agregar(self, item, slot=0):
        if slot < 0 or slot >= len(self.espacios):
            return False

        if self.espacios[slot] is not None:
            return False

        self.espacios[slot] = item

        if self.slot_equipado is None:
            self.slot_equipado = slot

        return True

    def equipar(self, slot):
        if slot < 0 or slot >= len(self.espacios):
            return False

        if self.espacios[slot] is None:
            return False

        self.slot_equipado = slot
        return True

    def desequipar(self):
        self.slot_equipado = None

    def tiene_equipado(self):
        return self.equipado is not None

    def soltar(self, slot=None):
        if slot is None:
            slot = self.slot_equipado

        if slot is None:
            return None

        if slot < 0 or slot >= len(self.espacios):
            return None

        item = self.espacios[slot]

        if item is None:
            return None

        self.espacios[slot] = None

        if self.slot_equipado == slot:
            self.slot_equipado = None

        # Si existen otros objetos, se equipa el primero disponible.
        for i, objeto in enumerate(self.espacios):
            if objeto is not None:
                self.slot_equipado = i
                break

        return item