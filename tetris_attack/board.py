# board.py
import random
import numpy as np
from config import ANCHO_TABLERO, ALTO_VISIBLE, FILAS_TOTALES, NUM_COLORES, TAM_CELDA
from utils import generar_panel

class Panel:
    """Un panel individual con física de caída continua."""
    __slots__ = ('color', 'offset_y', 'velocidad')
    def __init__(self, color):
        self.color = color
        self.offset_y = 0.0      # desplazamiento en píxeles desde la parte superior de la celda
        self.velocidad = 0.0     # píxeles por segundo hacia abajo

    def copiar(self):
        """Copia solo el color, sin física."""
        return Panel(self.color)

class Board:
    def __init__(self, fisica=True):
        self.fisica = fisica
        # matriz de Panel o None
        self.matriz = [[None] * ANCHO_TABLERO for _ in range(FILAS_TOTALES)]
        self.cursor_x = ANCHO_TABLERO // 2
        self.cursor_y = FILAS_TOTALES - 1
        # Máquina de estados solo para pausa de matches
        self.estado = 'normal'          # 'normal' o 'pausa'
        self.timer_estado = 0
        self.pausa_duracion = 12        # frames de pausa antes de eliminar
        self.grupos_a_eliminar = set()  # coordenadas (fila, col) a eliminar tras la pausa
        # Parámetros físicos
        self.gravedad = 1800.0          # píxeles/s²
        self.vel_max = 900.0            # píxeles/s
        self.llenar_inicial(4)
        self._ajustar_cursor()

    # ------------------------------------------------------------
    # Inicialización y copia
    # ------------------------------------------------------------
    def llenar_inicial(self, filas_iniciales=4):
        inicio = FILAS_TOTALES - filas_iniciales
        for fila in range(inicio, FILAS_TOTALES):
            for col in range(ANCHO_TABLERO):
                color = generar_panel()
                while (col >= 2 and
                       self._color(fila, col-1) == color and
                       self._color(fila, col-2) == color):
                    color = generar_panel()
                while (fila >= inicio + 2 and
                       self._color(fila-1, col) == color and
                       self._color(fila-2, col) == color):
                    color = generar_panel()
                self.matriz[fila][col] = Panel(color)

    def _color(self, fila, col):
        p = self.matriz[fila][col]
        return p.color if p else None

    def copiar(self):
        """Copia lógica sin física (para la IA)."""
        nuevo = Board(fisica=False)
        for f in range(FILAS_TOTALES):
            for c in range(ANCHO_TABLERO):
                if self.matriz[f][c]:
                    nuevo.matriz[f][c] = self.matriz[f][c].copiar()
        nuevo.cursor_x = self.cursor_x
        nuevo.cursor_y = self.cursor_y
        return nuevo

    # ------------------------------------------------------------
    # Movimiento del cursor
    # ------------------------------------------------------------
    def _posicion_es_valida(self, fila, col):
        if col < 0 or col >= ANCHO_TABLERO - 1:
            return False
        if fila < 0 or fila >= FILAS_TOTALES:
            return False
        p1 = self.matriz[fila][col]
        p2 = self.matriz[fila][col+1]
        return not (p1 is None and p2 is None)

    def _ajustar_cursor(self):
        if self._posicion_es_valida(self.cursor_y, self.cursor_x):
            return
        for dy in range(FILAS_TOTALES):
            fa = self.cursor_y + dy
            if fa < FILAS_TOTALES and self._posicion_es_valida(fa, self.cursor_x):
                self.cursor_y = fa
                return
            fb = self.cursor_y - dy
            if fb >= 0 and self._posicion_es_valida(fb, self.cursor_x):
                self.cursor_y = fb
                return

    def mover_cursor(self, dx, dy):
        if dx != 0:
            nuevo_x = max(0, min(ANCHO_TABLERO - 2, self.cursor_x + dx))
            if nuevo_x != self.cursor_x:
                self.cursor_x = nuevo_x
                self._ajustar_cursor()
        if dy != 0:
            limite_inf = FILAS_TOTALES - 1
            limite_sup = FILAS_TOTALES - ALTO_VISIBLE
            nueva_y = self.cursor_y + dy
            if limite_sup <= nueva_y <= limite_inf:
                self.cursor_y = nueva_y

    # ------------------------------------------------------------
    # Intercambio
    # ------------------------------------------------------------
    def intercambiar(self, x=None):
        if x is not None:
            self.cursor_x = x
            self._ajustar_cursor()
        cx, cy = self.cursor_x, self.cursor_y
        if not self._posicion_es_valida(cy, cx):
            return False
        self.matriz[cy][cx], self.matriz[cy][cx+1] = self.matriz[cy][cx+1], self.matriz[cy][cx]
        return True

    # ------------------------------------------------------------
    # Búsqueda de grupos
    # ------------------------------------------------------------
    def _buscar_grupos(self):
        grupos = set()
        for r in range(FILAS_TOTALES):
            for c in range(ANCHO_TABLERO - 2):
                p0, p1, p2 = self.matriz[r][c], self.matriz[r][c+1], self.matriz[r][c+2]
                if p0 and p1 and p2 and p0.color == p1.color == p2.color:
                    grupos.update([(r, c), (r, c+1), (r, c+2)])
        for c in range(ANCHO_TABLERO):
            for r in range(FILAS_TOTALES - 2):
                p0, p1, p2 = self.matriz[r][c], self.matriz[r+1][c], self.matriz[r+2][c]
                if p0 and p1 and p2 and p0.color == p1.color == p2.color:
                    grupos.update([(r, c), (r+1, c), (r+2, c)])
        return grupos

    # ------------------------------------------------------------
    # Gravedad continua (aplicada en cada frame en estado 'normal')
    # ------------------------------------------------------------
    def _aplicar_gravedad(self, dt):
        """Recorre todas las columnas de abajo hacia arriba aplicando gravedad a cada panel."""
        for c in range(ANCHO_TABLERO):
            # Recorremos desde la fila más baja (la última) hacia arriba
            for r in range(FILAS_TOTALES - 1, 0, -1):
                p = self.matriz[r-1][c]   # panel que está encima de la celda r
                if p is None:
                    continue
                # Si la celda de abajo (r) está vacía, el panel puede caer
                if self.matriz[r][c] is None:
                    p.velocidad += self.gravedad * dt
                    if p.velocidad > self.vel_max:
                        p.velocidad = self.vel_max
                    p.offset_y += p.velocidad * dt

                    # Mientras haya suficiente offset para bajar una celda completa y el destino siga vacío
                    while p.offset_y >= TAM_CELDA and r < FILAS_TOTALES and self.matriz[r][c] is None:
                        self.matriz[r][c] = p
                        self.matriz[r-1][c] = None
                        p.offset_y -= TAM_CELDA
                        r += 1
                        if r == FILAS_TOTALES:
                            break
                    # Si después de moverse ya no cabe o chocó, detener
                    if r < FILAS_TOTALES and self.matriz[r][c] is not None:
                        p.offset_y = 0.0
                        p.velocidad = 0.0
                else:
                    # No hay espacio debajo, detener cualquier movimiento residual
                    if p.velocidad != 0.0 or p.offset_y != 0.0:
                        p.velocidad = 0.0
                        p.offset_y = 0.0

    # ------------------------------------------------------------
    # Estabilidad (ningún panel se está moviendo)
    # ------------------------------------------------------------
    def esta_estable(self):
        """True si ningún panel tiene velocidad ni desplazamiento."""
        for r in range(FILAS_TOTALES):
            for c in range(ANCHO_TABLERO):
                p = self.matriz[r][c]
                if p and (p.velocidad != 0.0 or p.offset_y != 0.0):
                    return False
        return True

    # ------------------------------------------------------------
    # Actualización principal (llamada cada frame con dt en segundos)
    # ------------------------------------------------------------
    def update(self, dt):
        if self.estado == 'normal':
            # Aplicar gravedad a todos los paneles que puedan caer
            self._aplicar_gravedad(dt)
            # Buscar matches después de la caída
            grupos = self._buscar_grupos()
            if grupos:
                self.grupos_a_eliminar = grupos
                self.estado = 'pausa'
                self.timer_estado = self.pausa_duracion
        elif self.estado == 'pausa':
            self.timer_estado -= 1
            if self.timer_estado <= 0:
                # Eliminar los paneles marcados
                for (r, c) in self.grupos_a_eliminar:
                    self.matriz[r][c] = None
                self.grupos_a_eliminar.clear()
                # Volver a normal; la gravedad actuará inmediatamente en el siguiente frame
                self.estado = 'normal'

    # ------------------------------------------------------------
    # Basura
    # ------------------------------------------------------------
    def recibir_basura(self, lineas):
        for _ in range(lineas):
            fila_basura = [generar_panel() for _ in range(ANCHO_TABLERO)]
            hueco = random.randint(0, ANCHO_TABLERO - 1)
            fila_basura[hueco] = None
            for r in range(FILAS_TOTALES - 1):
                self.matriz[r] = self.matriz[r+1]
            self.matriz[FILAS_TOTALES - 1] = [
                Panel(c) if c is not None else None for c in fila_basura
            ]
        # Si estábamos en normal, la gravedad se encarga de los huecos en el próximo update

    # ------------------------------------------------------------
    # Método para la IA: resolución instantánea sin física
    # ------------------------------------------------------------
    def resolver_matches(self):
        puntos = 0
        cadenas = 0
        while True:
            grupos = self._buscar_grupos()
            if not grupos:
                break
            cadenas += 1
            eliminados = 0
            for (r, c) in grupos:
                if self.matriz[r][c] is not None:
                    eliminados += 1
                    self.matriz[r][c] = None
            puntos += eliminados * 10 * cadenas
            self._compactar()
        basura = cadenas * 2
        return puntos, cadenas, basura

    def _compactar(self):
        for c in range(ANCHO_TABLERO):
            columna = [self.matriz[r][c] for r in range(FILAS_TOTALES-1, -1, -1) if self.matriz[r][c] is not None]
            for r in range(FILAS_TOTALES):
                if r < len(columna):
                    self.matriz[FILAS_TOTALES-1-r][c] = columna[r]
                else:
                    self.matriz[FILAS_TOTALES-1-r][c] = None

    # ------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------
    def esta_perdido(self):
        limite = FILAS_TOTALES - ALTO_VISIBLE
        for c in range(ANCHO_TABLERO):
            if self.matriz[limite][c] is not None:
                return True
        return False

    def altura_columna(self, col):
        for r in range(FILAS_TOTALES):
            if self.matriz[r][col] is not None:
                return FILAS_TOTALES - r
        return 0

    def contar_agujeros(self):
        agujeros = 0
        for c in range(ANCHO_TABLERO):
            bloque = False
            for r in range(FILAS_TOTALES):
                if self.matriz[r][c] is not None:
                    bloque = True
                elif bloque:
                    agujeros += 1
        return agujeros

    def contar_parejas_adyacentes(self):
        parejas = 0
        for r in range(FILAS_TOTALES):
            for c in range(ANCHO_TABLERO-1):
                p1, p2 = self.matriz[r][c], self.matriz[r][c+1]
                if p1 and p2 and p1.color == p2.color:
                    parejas += 1
        for c in range(ANCHO_TABLERO):
            for r in range(FILAS_TOTALES-1):
                p1, p2 = self.matriz[r][c], self.matriz[r+1][c]
                if p1 and p2 and p1.color == p2.color:
                    parejas += 1
        return parejas

    def estado_a_vector(self):
        alturas = [self.altura_columna(c)/FILAS_TOTALES for c in range(ANCHO_TABLERO)]
        colores_top = []
        for c in range(ANCHO_TABLERO):
            h = self.altura_columna(c)
            if h > 0:
                color = self.matriz[FILAS_TOTALES - h][c].color
                oh = [0]*NUM_COLORES
                oh[color] = 1
                colores_top.extend(oh)
            else:
                colores_top.extend([0]*NUM_COLORES)
        parejas = self.contar_parejas_adyacentes() / (ANCHO_TABLERO * FILAS_TOTALES)
        cursor = [0]*ANCHO_TABLERO
        cursor[self.cursor_x] = 1
        return np.array(alturas + colores_top + [parejas] + cursor)