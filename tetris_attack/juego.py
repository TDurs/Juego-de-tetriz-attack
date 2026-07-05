class Board:
    def __init__(self, ancho=6, alto=12):
        self.ancho = ancho
        self.alto = alto
        self.matriz = [[None]*ancho for _ in range(alto)]  # None o entero (id color)
        self.cursor_x = ancho//2  # posición columna cursor

    def copiar(self):
        # Devuelve una copia profunda
        ...

    def realizar_intercambio(self, x):
        # Intercambia (x, y) con (x+1, y) en la fila del cursor
        ...

    def actualizar(self):
        # Detecta grupos, elimina, aplica gravedad y repite hasta estabilizar
        # Retorna (puntos, cadenas, basura generada)
        ...

    def estado_a_vector(self):
        # Convierte el tablero en un vector de características para ML
        # Ej: matriz aplanada one-hot, alturas de columna, número de grupos potenciales...
        ...