# utils.py
import random
from config import ANCHO_TABLERO, FILAS_TOTALES, NUM_COLORES

def generar_panel():
    """Devuelve un color aleatorio entre 0 y NUM_COLORES-1"""
    return random.randint(0, NUM_COLORES-1)

def crear_tablero_vacio():
    """Crea una matriz de FILAS_TOTALES x ANCHO_TABLERO llena de None"""
    return [[None]*ANCHO_TABLERO for _ in range(FILAS_TOTALES)]

def copiar_tablero(tablero):
    """Copia profunda de la matriz del tablero"""
    return [fila[:] for fila in tablero]