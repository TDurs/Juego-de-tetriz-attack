# config.py
import os


ANCHO_TABLERO = 6
ALTO_VISIBLE = 12
FILAS_TOTALES = 16
NUM_COLORES = 5

COLORES_RGB = [
    (230, 40, 40),      # rojo
    (40, 190, 40),      # verde
    (40, 40, 230),      # azul
    (230, 230, 40),     # amarillo
    (210, 40, 210),     # magenta
]

TAM_CELDA = 54           # celdas más grandes
MARGEN_LATERAL = 60      # espacio a izquierda y derecha
MARGEN_ENTRE_TABLEROS = 80  # espacio entre los dos tableros
MARGEN_SUPERIOR = 60     # espacio arriba
MARGEN_INFERIOR = 80     # espacio abajo para HUD

ANCHO_VENTANA = (MARGEN_LATERAL * 2) + (ANCHO_TABLERO * TAM_CELDA) * 2 + MARGEN_ENTRE_TABLEROS
ALTO_VENTANA = MARGEN_SUPERIOR + (ALTO_VISIBLE * TAM_CELDA) + MARGEN_INFERIOR
FPS = 60

IA_DELAY = 15

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARCHIVO_DATOS = os.path.join(BASE_DIR, "datos_jugador.csv")
ARCHIVO_MODELO = os.path.join(BASE_DIR, "modelo_adaptativo.pkl")
ARCHIVO_RANKING = os.path.join(BASE_DIR, "ranking.json")


