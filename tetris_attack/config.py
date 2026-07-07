# config.py
import os

ANCHO_TABLERO = 6
ALTO_VISIBLE = 12
FILAS_TOTALES = 16
NUM_COLORES = 5

# ------------------------------------------------------------
# Paleta de gemas: colores base, claros y oscuros para el sombreado
# ------------------------------------------------------------
COLORES_RGB = [
    (235, 64, 82),      # rojo rubí
    (58, 201, 120),     # verde esmeralda
    (64, 130, 235),     # azul zafiro
    (240, 200, 60),     # amarillo topacio
    (190, 90, 235),     # violeta amatista
]

COLORES_CLAROS = [tuple(min(c + 90, 255) for c in col) for col in COLORES_RGB]
COLORES_OSCUROS = [tuple(max(c - 90, 0) for c in col) for col in COLORES_RGB]

# ------------------------------------------------------------
# Paleta de interfaz (fondos, paneles, texto, acentos)
# ------------------------------------------------------------
COLOR_FONDO_TOP = (10, 12, 24)
COLOR_FONDO_BOTTOM = (30, 18, 46)
COLOR_PANEL_UI = (22, 24, 40)
COLOR_PANEL_UI_CLARO = (34, 36, 58)
COLOR_BORDE_UI = (95, 84, 160)
COLOR_ACENTO = (255, 196, 60)      # dorado, para selección / récords
COLOR_ACENTO_2 = (100, 200, 255)   # celeste, para IA / info
COLOR_ACENTO_3 = (255, 100, 130)   # rosa, para alertas / peligro
COLOR_TEXTO = (240, 240, 250)
COLOR_TEXTO_SUAVE = (165, 165, 190)

# Dimensiones
TAM_CELDA = 50
MARGEN_LATERAL = 60
MARGEN_ENTRE_TABLEROS = 80
MARGEN_SUPERIOR = 50
MARGEN_INFERIOR = 90

ANCHO_VENTANA = (MARGEN_LATERAL * 2) + (ANCHO_TABLERO * TAM_CELDA) * 2 + MARGEN_ENTRE_TABLEROS
ALTO_VENTANA = MARGEN_SUPERIOR + (ALTO_VISIBLE * TAM_CELDA) + MARGEN_INFERIOR
FPS = 60

IA_DELAY = 15

# Rutas de archivos (conservadas tal cual las tenías)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARCHIVO_DATOS = os.path.join(BASE_DIR, "datos_jugador.csv")
ARCHIVO_MODELO = os.path.join(BASE_DIR, "modelo_adaptativo.pkl")
ARCHIVO_RANKING = os.path.join(BASE_DIR, "ranking.json")