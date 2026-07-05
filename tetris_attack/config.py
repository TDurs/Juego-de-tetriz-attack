# config.py
# Parámetros y constantes del juego

ANCHO_TABLERO = 6       # columnas
ALTO_VISIBLE = 12       # filas visibles
FILAS_TOTALES = 16      # filas totales (incluye 4 ocultas arriba)
NUM_COLORES = 5         # 0..4

# Colores en formato RGB para Pygame
COLORES_RGB = [
    (255, 0, 0),    # rojo
    (0, 255, 0),    # verde
    (0, 0, 255),    # azul
    (255, 255, 0),  # amarillo
    (255, 0, 255),  # magenta
]

TAM_CELDA = 30
MARGEN = 5
ANCHO_VENTANA = (ANCHO_TABLERO * TAM_CELDA + MARGEN) * 2 + 200
ALTO_VENTANA = ALTO_VISIBLE * TAM_CELDA + 50
FPS = 30

# Velocidad de la IA (en frames)
IA_DELAY = 20          # la IA mueve cada 20 frames (aprox. 0.66 seg a 30 FPS)

# Archivos de datos
ARCHIVO_DATOS = "datos_jugador.csv"
ARCHIVO_MODELO = "modelo_adaptativo.pkl"