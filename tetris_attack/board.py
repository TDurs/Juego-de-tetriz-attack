# board.py
from config import ANCHO_TABLERO, ALTO_VISIBLE, FILAS_TOTALES, NUM_COLORES
from utils import generar_panel, crear_tablero_vacio, copiar_tablero
import numpy as np
import random

class Board:
    def __init__(self):
        self.matriz = crear_tablero_vacio()
        self.cursor_x = ANCHO_TABLERO // 2
        self.cursor_y = FILAS_TOTALES - 1
        self.basura_pendiente = 0
        # Sistema de caída animada (rápida)
        self.cayendo = False
        self.frames_caida = 0
        self.max_frames_caida = 4      # caída en 4 frames (~0.13s a 30fps)
        self.paneles_cayendo = []      # lista de dict: {col, color, fila_ini, fila_fin}
        self.llenar_inicial(filas_iniciales=4)
        self._reubicar_cursor_en_columna_actual()

    def llenar_inicial(self, filas_iniciales=4):
        inicio = FILAS_TOTALES - filas_iniciales
        for fila in range(inicio, FILAS_TOTALES):
            for col in range(ANCHO_TABLERO):
                color = generar_panel()
                while (col >= 2 and
                       self.matriz[fila][col-1] == color and
                       self.matriz[fila][col-2] == color):
                    color = generar_panel()
                while (fila >= inicio + 2 and
                       self.matriz[fila-1][col] == color and
                       self.matriz[fila-2][col] == color):
                    color = generar_panel()
                self.matriz[fila][col] = color

    def copiar(self):
        nuevo = Board.__new__(Board)
        nuevo.matriz = copiar_tablero(self.matriz)
        nuevo.cursor_x = self.cursor_x
        nuevo.cursor_y = self.cursor_y
        nuevo.basura_pendiente = self.basura_pendiente
        # No copiar estado de caída para la IA
        return nuevo

    def _posicion_es_valida(self, fila, col):
        if col < 0 or col >= ANCHO_TABLERO - 1:
            return False
        if fila < 0 or fila >= FILAS_TOTALES:
            return False
        return self.matriz[fila][col] is not None and self.matriz[fila][col+1] is not None

    def _reubicar_cursor_en_columna_actual(self):
        for fila in range(FILAS_TOTALES-1, -1, -1):
            if self._posicion_es_valida(fila, self.cursor_x):
                self.cursor_y = fila
                return

    def _ajustar_cursor_si_es_necesario(self):
        if self._posicion_es_valida(self.cursor_y, self.cursor_x):
            return
        for dy in range(FILAS_TOTALES):
            fila_abajo = self.cursor_y + dy
            if fila_abajo < FILAS_TOTALES and self._posicion_es_valida(fila_abajo, self.cursor_x):
                self.cursor_y = fila_abajo
                return
            fila_arriba = self.cursor_y - dy
            if fila_arriba >= 0 and self._posicion_es_valida(fila_arriba, self.cursor_x):
                self.cursor_y = fila_arriba
                return

    def mover_cursor(self, dx, dy):
        if dx != 0:
            nuevo_x = max(0, min(ANCHO_TABLERO-2, self.cursor_x + dx))
            if nuevo_x != self.cursor_x:
                self.cursor_x = nuevo_x
                if not self._posicion_es_valida(self.cursor_y, self.cursor_x):
                    self._ajustar_cursor_si_es_necesario()
        if dy != 0:
            limite_inf = FILAS_TOTALES - 1
            limite_sup = FILAS_TOTALES - ALTO_VISIBLE
            nueva_y = self.cursor_y + dy
            if limite_sup <= nueva_y <= limite_inf:
                self.cursor_y = nueva_y

    def intercambiar(self, x=None):
        if x is not None:
            self.cursor_x = x
            self._reubicar_cursor_en_columna_actual()
        if not self._posicion_es_valida(self.cursor_y, self.cursor_x):
            return False
        cx, cy = self.cursor_x, self.cursor_y
        self.matriz[cy][cx], self.matriz[cy][cx+1] = self.matriz[cy][cx+1], self.matriz[cy][cx]
        return True

    def actualizar(self):
        puntos = 0
        cadenas = 0
        while True:
            grupos = self._encontrar_grupos()
            if not grupos:
                break
            cadenas += 1
            paneles_eliminados = 0
            for (r, c) in grupos:
                if self.matriz[r][c] is not None:
                    paneles_eliminados += 1
                    self.matriz[r][c] = None
            puntos += paneles_eliminados * 10 * cadenas
            self._aplicar_gravedad()
        self._ajustar_cursor_si_es_necesario()
        basura_total = cadenas * 2
        return puntos, cadenas, basura_total

    def _encontrar_grupos(self):
        grupos = set()
        for r in range(FILAS_TOTALES):
            for c in range(ANCHO_TABLERO - 2):
                color = self.matriz[r][c]
                if color is not None and color == self.matriz[r][c+1] == self.matriz[r][c+2]:
                    grupos.update([(r, c), (r, c+1), (r, c+2)])
        for c in range(ANCHO_TABLERO):
            for r in range(FILAS_TOTALES - 2):
                color = self.matriz[r][c]
                if color is not None and color == self.matriz[r+1][c] == self.matriz[r+2][c]:
                    grupos.update([(r, c), (r+1, c), (r+2, c)])
        return grupos

    def _aplicar_gravedad(self):
        for c in range(ANCHO_TABLERO):
            columna = [self.matriz[r][c] for r in range(FILAS_TOTALES-1, -1, -1) if self.matriz[r][c] is not None]
            for r in range(FILAS_TOTALES):
                if r < len(columna):
                    self.matriz[FILAS_TOTALES-1-r][c] = columna[r]
                else:
                    self.matriz[FILAS_TOTALES-1-r][c] = None

    def recibir_basura(self, lineas):
        for _ in range(lineas):
            fila_basura = [generar_panel() for _ in range(ANCHO_TABLERO)]
            hueco = random.randint(0, ANCHO_TABLERO-1)
            fila_basura[hueco] = None
            for r in range(FILAS_TOTALES-1):
                self.matriz[r] = self.matriz[r+1][:]
            self.matriz[FILAS_TOTALES-1] = fila_basura
        self._ajustar_cursor_si_es_necesario()

    def esta_perdido(self):
        limite = FILAS_TOTALES - ALTO_VISIBLE
        for c in range(ANCHO_TABLERO):
            if self.matriz[limite][c] is not None:
                return True
        return False

    # -----------------------------------------------
    #  Sistema de animación de caída rápida
    # -----------------------------------------------
    def iniciar_caida(self, matriz_antes, duracion=None):
        """Compara la matriz actual con 'matriz_antes' y genera animaciones de los paneles que cayeron.
           Si duracion es None, usa el valor por defecto (4); si es 0, compacta sin animar.
        """
        if duracion is None:
            duracion = self.max_frames_caida
        self.paneles_cayendo.clear()
        for c in range(ANCHO_TABLERO):
            viejos = []
            for r in range(FILAS_TOTALES-1, -1, -1):
                if matriz_antes[r][c] is not None:
                    viejos.append((matriz_antes[r][c], r))
            nuevos = []
            for r in range(FILAS_TOTALES-1, -1, -1):
                if self.matriz[r][c] is not None:
                    nuevos.append((self.matriz[r][c], r))
            for (color_v, fila_v), (color_n, fila_n) in zip(viejos, nuevos):
                if fila_v != fila_n:
                    self.paneles_cayendo.append({
                        'col': c,
                        'color': color_n,
                        'fila_ini': fila_v,
                        'fila_fin': fila_n
                    })
        if self.paneles_cayendo and duracion > 0:
            self.cayendo = True
            self.frames_caida = duracion
            self.max_frames_caida = duracion
        else:
            self.cayendo = False
            self.paneles_cayendo.clear()

    def actualizar_caida(self):
        """Decrementa el contador de frames de caída. Al llegar a 0, termina la animación."""
        if self.cayendo:
            self.frames_caida -= 1
            if self.frames_caida <= 0:
                self.cayendo = False
                self.paneles_cayendo.clear()

    def altura_columna(self, col):
        for r in range(FILAS_TOTALES):
            if self.matriz[r][col] is not None:
                return FILAS_TOTALES - r
        return 0

    def contar_agujeros(self):
        agujeros = 0
        for c in range(ANCHO_TABLERO):
            bloque_lleno = False
            for r in range(FILAS_TOTALES):
                if self.matriz[r][c] is not None:
                    bloque_lleno = True
                elif bloque_lleno:
                    agujeros += 1
        return agujeros

    def contar_parejas_adyacentes(self):
        parejas = 0
        for r in range(FILAS_TOTALES):
            for c in range(ANCHO_TABLERO-1):
                if self.matriz[r][c] is not None and self.matriz[r][c] == self.matriz[r][c+1]:
                    parejas += 1
        for c in range(ANCHO_TABLERO):
            for r in range(FILAS_TOTALES-1):
                if self.matriz[r][c] is not None and self.matriz[r][c] == self.matriz[r+1][c]:
                    parejas += 1
        return parejas

    def estado_a_vector(self):
        alturas = [self.altura_columna(c)/FILAS_TOTALES for c in range(ANCHO_TABLERO)]
        colores_top = []
        for c in range(ANCHO_TABLERO):
            h = self.altura_columna(c)
            if h > 0:
                color = self.matriz[FILAS_TOTALES - h][c]
                one_hot = [0]*NUM_COLORES
                one_hot[color] = 1
                colores_top.extend(one_hot)
            else:
                colores_top.extend([0]*NUM_COLORES)
        parejas = self.contar_parejas_adyacentes() / (ANCHO_TABLERO * FILAS_TOTALES)
        cursor = [0]*ANCHO_TABLERO
        cursor[self.cursor_x] = 1
        return np.array(alturas + colores_top + [parejas] + cursor)