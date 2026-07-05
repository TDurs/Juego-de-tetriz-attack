# main.py
import pygame
import sys
import random
import csv
from config import *
from board import Board
from ia_clasica import elegir_movimiento_clasico
from ia_adaptativa import cargar_modelo, predecir_movimiento

pygame.init()
pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
pygame.display.set_caption("Tetris Attack - IA Híbrida")
fuente = pygame.font.SysFont("Arial", 24)
fuente_grande = pygame.font.SysFont("Arial", 38, bold=True)
fuente_titulo = pygame.font.SysFont("Arial", 56, bold=True)
fuente_hud = pygame.font.SysFont("Arial", 26, bold=True)
reloj = pygame.time.Clock()

pygame.key.set_repeat(200, 50)

modo_juego = "clasico"
jugador = Board(fisica=True)
ia = Board(fisica=True)
turno_ia_timer = 0
partida_terminada = False
ganador = None
historial_jugador = []

puntuacion_jugador = 0
puntuacion_ia = 0
combo_jugador = 0
combo_ia = 0
ultima_cadena_jugador = 0
ultima_cadena_ia = 0

TIEMPO_SUBIDA_INICIAL = 3000
tiempo_subida = TIEMPO_SUBIDA_INICIAL
ultimo_rise = pygame.time.get_ticks()

animaciones = []
pausa = False

# Colores modernos
COLOR_FONDO = (18, 18, 28)
COLOR_LINEAS_GUIA = (55, 55, 70)
ALPHA_BRILLO = 60

# Fondo elegante con degradado
def crear_fondo():
    surf = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA))
    for y in range(ALTO_VENTANA):
        color = (15 + y//20, 15 + y//25, 25 + y//30)
        pygame.draw.line(surf, color, (0, y), (ANCHO_VENTANA, y))
    # Patrón de puntos muy sutiles
    for x in range(0, ANCHO_VENTANA, 80):
        for y in range(0, ALTO_VENTANA, 80):
            pygame.draw.circle(surf, (30,30,40), (x, y), 1)
    return surf

fondo_estatico = crear_fondo()

# Partículas decorativas (estilo estrellas)
class Particula:
    def __init__(self):
        self.x = random.randint(0, ANCHO_VENTANA)
        self.y = random.randint(-50, -10)
        self.vel = random.uniform(15, 50)
        self.color = random.choice(COLORES_RGB)
        self.tam = random.randint(1, 3)
    def update(self, dt):
        self.y += self.vel * dt
        if self.y > ALTO_VENTANA + 20:
            self.y = random.randint(-50, -10)
            self.x = random.randint(0, ANCHO_VENTANA)
    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.tam)

particulas = [Particula() for _ in range(50)]

# ------------------------------------------------------------
# Dibujo de paneles con efecto vidrioso
# ------------------------------------------------------------
def dibujar_panel(superficie, color_idx, x, y, w, h):
    rect = pygame.Rect(x, y, w, h)
    if color_idx is None:
        pygame.draw.rect(superficie, (40,40,50), rect, 1)
        return
    color_base = COLORES_RGB[color_idx]
    # Sombra interna
    pygame.draw.rect(superficie, color_base, rect, border_radius=4)
    # Borde superior e izquierdo más claro
    claro = [min(c + 100, 255) for c in color_base]
    oscuro = [max(c - 100, 0) for c in color_base]
    pygame.draw.line(superficie, claro, (x, y), (x+w-1, y), 3)
    pygame.draw.line(superficie, claro, (x, y), (x, y+h-1), 3)
    pygame.draw.line(superficie, oscuro, (x, y+h-1), (x+w-1, y+h-1), 3)
    pygame.draw.line(superficie, oscuro, (x+w-1, y), (x+w-1, y+h-1), 3)
    # Brillo diagonal
    brillo = pygame.Surface((w//3, h//3), pygame.SRCALPHA)
    brillo.fill((255,255,255, ALPHA_BRILLO))
    superficie.blit(brillo, (x+3, y+3))

def sombra_rect(superficie, rect, color=(0,0,0,60), desplazamiento=2):
    sombra = pygame.Surface(rect.size, pygame.SRCALPHA)
    sombra.fill(color)
    superficie.blit(sombra, rect.move(desplazamiento, desplazamiento))

def dibujar_tablero(board, offset_x, offset_y, es_jugador=True, tiempo_subida_restante=1.0):
    # Fondo del tablero con sombra y borde decorativo
    tablero_rect = pygame.Rect(offset_x-6, offset_y-6, ANCHO_TABLERO*TAM_CELDA+12, ALTO_VISIBLE*TAM_CELDA+12)
    sombra_rect(pantalla, tablero_rect, (0,0,0,100), 4)
    pygame.draw.rect(pantalla, (25,25,35), tablero_rect, border_radius=10)
    pygame.draw.rect(pantalla, (80,70,40), tablero_rect, 2, border_radius=10)  # marco dorado oscuro

    # Líneas guía suaves
    for c in range(ANCHO_TABLERO+1):
        x = offset_x + c*TAM_CELDA
        pygame.draw.line(pantalla, COLOR_LINEAS_GUIA, (x, offset_y), (x, offset_y+ALTO_VISIBLE*TAM_CELDA), 1)
    for r in range(ALTO_VISIBLE+1):
        y = offset_y + r*TAM_CELDA
        pygame.draw.line(pantalla, COLOR_LINEAS_GUIA, (offset_x, y), (offset_x+ANCHO_TABLERO*TAM_CELDA, y), 1)

    inicio_fila = FILAS_TOTALES - ALTO_VISIBLE
    for r in range(inicio_fila, FILAS_TOTALES):
        for c in range(ANCHO_TABLERO):
            p = board.matriz[r][c]
            if p is None:
                continue
            color = p.color
            fila_vis = r - inicio_fila
            x = offset_x + c * TAM_CELDA + 3
            base_y = offset_y + fila_vis * TAM_CELDA + 3
            y = base_y + p.offset_y
            dibujar_panel(pantalla, color, x, y, TAM_CELDA-6, TAM_CELDA-6)

    # Cursor del jugador mejorado (solo si es su tablero)
    if es_jugador:
        cx, cy = board.cursor_x, board.cursor_y
        if inicio_fila <= cy < FILAS_TOTALES:
            fila_vis = cy - inicio_fila
            cx_pix = offset_x + cx * TAM_CELDA
            cy_pix = offset_y + fila_vis * TAM_CELDA
            cursor_rect = pygame.Rect(cx_pix, cy_pix, TAM_CELDA*2, TAM_CELDA)
            valida = board._posicion_es_valida(cy, cx)
            # Aura luminosa
            color_aura = (255,255,120,50) if valida else (255,120,120,50)
            aura = pygame.Surface((cursor_rect.width+14, cursor_rect.height+14), pygame.SRCALPHA)
            pygame.draw.rect(aura, color_aura, aura.get_rect(), border_radius=8)
            pantalla.blit(aura, cursor_rect.move(-7,-7))
            # Borde grueso
            color_borde = (255,255,0,230) if valida else (255,100,100,210)
            pygame.draw.rect(pantalla, color_borde, cursor_rect, 4, border_radius=6)
            # Marcas triangulares superior e inferior
            centro_x = cx_pix + TAM_CELDA
            # triángulo arriba
            pygame.draw.polygon(pantalla, color_borde,
                [(centro_x-6, cy_pix-6), (centro_x+6, cy_pix-6), (centro_x, cy_pix-12)])
            # triángulo abajo
            pygame.draw.polygon(pantalla, color_borde,
                [(centro_x-6, cy_pix+TAM_CELDA+6), (centro_x+6, cy_pix+TAM_CELDA+6), (centro_x, cy_pix+TAM_CELDA+12)])

    # Barra de subida
    if not partida_terminada:
        barra_rect = pygame.Rect(offset_x, offset_y - 18, ANCHO_TABLERO*TAM_CELDA, 10)
        pygame.draw.rect(pantalla, (30,30,30), barra_rect, border_radius=5)
        progreso = 1.0 - tiempo_subida_restante
        relleno = pygame.Rect(offset_x, offset_y - 18, int(ANCHO_TABLERO*TAM_CELDA * max(0, min(1, progreso))), 10)
        color_barra = (0,200,0) if progreso < 0.7 else (255,200,0) if progreso < 0.9 else (255,50,50)
        pygame.draw.rect(pantalla, color_barra, relleno, border_radius=5)

def dibujar_hud():
    # Panel inferior translúcido
    panel = pygame.Rect(0, ALTO_VENTANA-70, ANCHO_VENTANA, 70)
    pygame.draw.rect(pantalla, (15,15,25,220), panel)
    pygame.draw.line(pantalla, (80,80,100), (0, ALTO_VENTANA-70), (ANCHO_VENTANA, ALTO_VENTANA-70), 2)
    # Puntuaciones
    txt_jug = fuente_hud.render(f"Jugador: {puntuacion_jugador}", True, (255,255,255))
    txt_ia = fuente_hud.render(f"IA: {puntuacion_ia}", True, (255,255,255))
    pantalla.blit(txt_jug, (40, ALTO_VENTANA-55))
    pantalla.blit(txt_ia, (ANCHO_VENTANA//2 + 40, ALTO_VENTANA-55))
    # Modo y pausa
    txt_modo = fuente.render(f"Modo: {modo_juego.upper()}", True, (200,200,200))
    txt_pausa = fuente.render("ESC: Pausa", True, (150,150,150))
    pantalla.blit(txt_modo, (ANCHO_VENTANA//2 - 70, ALTO_VENTANA-65))
    pantalla.blit(txt_pausa, (ANCHO_VENTANA - 170, ALTO_VENTANA-55))

def mostrar_texto_temporal(texto, x, y, duracion=60, color=(255, 255, 0), tamaño=32):
    fuente_temp = pygame.font.SysFont("Arial", tamaño, bold=True)
    animaciones.append(('texto', (texto, x, y, fuente_temp, color), duracion))

def dibujar_animaciones():
    global animaciones
    for anim in animaciones[:]:
        tipo, datos, tiempo = anim
        if tipo == 'texto':
            texto, x, y, fuente_temp, color = datos
            alpha = int(255 * (tiempo / 60)) if tiempo < 60 else 255
            surf = fuente_temp.render(texto, True, color)
            surf.set_alpha(alpha)
            sombra = fuente_temp.render(texto, True, (0,0,0))
            sombra.set_alpha(alpha//2)
            pantalla.blit(sombra, (x+2, y+2))
            pantalla.blit(surf, (x, y))
        elif tipo == 'destello':
            x, y, radio = datos
            intensidad = tiempo / 15
            color = (255, 255, 150 * intensidad)
            pygame.draw.circle(pantalla, color, (int(x), int(y)), int(radio * intensidad))
        tiempo -= 1
        if tiempo <= 0:
            animaciones.remove(anim)
        else:
            animaciones[animaciones.index(anim)] = (tipo, datos, tiempo)

def menu_pausa():
    global pausa
    opciones = ["Continuar", "Reiniciar", "Menú Principal", "Salir"]
    seleccion = 0
    while pausa:
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        pantalla.blit(overlay, (0,0))
        txt_titulo = fuente_titulo.render("PAUSA", True, (255,255,255))
        pantalla.blit(txt_titulo, (ANCHO_VENTANA//2 - txt_titulo.get_width()//2, 100))
        for i, op in enumerate(opciones):
            color = (255,215,0) if i == seleccion else (200,200,200)
            txt = fuente_grande.render(op, True, color)
            rect = txt.get_rect(center=(ANCHO_VENTANA//2, 220 + i*80))
            if i == seleccion:
                pygame.draw.rect(pantalla, (40,40,60), rect.inflate(50, 20), border_radius=14)
                pygame.draw.rect(pantalla, (255,215,0), rect.inflate(50, 20), 3, border_radius=14)
            pantalla.blit(txt, rect)
        instru = fuente.render("↑↓: Navegar  ENTER: Seleccionar  ESC: Volver", True, (150,150,150))
        pantalla.blit(instru, (ANCHO_VENTANA//2 - instru.get_width()//2, ALTO_VENTANA-50))
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE: pausa = False
                elif evento.key == pygame.K_DOWN: seleccion = (seleccion+1)%4
                elif evento.key == pygame.K_UP: seleccion = (seleccion-1)%4
                elif evento.key == pygame.K_RETURN:
                    if seleccion == 0: pausa = False
                    elif seleccion == 1: reiniciar_partida(); pausa = False
                    elif seleccion == 2: guardar_historial(); pausa = False; return "menu"
                    elif seleccion == 3: guardar_historial(); pygame.quit(); sys.exit()
        pygame.display.flip()
        reloj.tick(30)
    return "juego"

def procesar_eventos():
    global jugador, ia, turno_ia_timer, partida_terminada, ganador, historial_jugador, pausa
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE and not partida_terminada:
                pausa = True; continue
            if partida_terminada:
                if evento.key == pygame.K_r: reiniciar_partida()
                continue
            if pausa: continue
            if evento.key == pygame.K_LEFT: jugador.mover_cursor(-1, 0)
            elif evento.key == pygame.K_RIGHT: jugador.mover_cursor(1, 0)
            elif evento.key == pygame.K_UP: jugador.mover_cursor(0, -1)
            elif evento.key == pygame.K_DOWN: jugador.mover_cursor(0, 1)
            elif evento.key == pygame.K_SPACE:
                if jugador.intercambiar():
                    destello_x = MARGEN_LATERAL + jugador.cursor_x * TAM_CELDA + TAM_CELDA//2
                    destello_y = MARGEN_SUPERIOR + (jugador.cursor_y - (FILAS_TOTALES - ALTO_VISIBLE)) * TAM_CELDA + TAM_CELDA//2
                    animaciones.append(('destello', (destello_x, destello_y, 12), 15))
                    turno_ia_timer = 0

def actualizar_mundo(dt):
    global jugador, ia, puntuacion_jugador, puntuacion_ia, combo_jugador, combo_ia
    global ultima_cadena_jugador, ultima_cadena_ia, partida_terminada, ganador
    if pausa: return
    # Jugador
    estado_anterior_j = jugador.estado
    jugador.update(dt)
    if estado_anterior_j != 'pausa' and jugador.estado == 'pausa':
        combo_jugador += 1
        puntuacion_jugador += 10 * combo_jugador
        if combo_jugador > 1:
            mostrar_texto_temporal(f"COMBO x{combo_jugador}!", ANCHO_VENTANA//2-120, ALTO_VENTANA//2-50)
        ultima_cadena_jugador = combo_jugador
    if jugador.estado == 'normal' and estado_anterior_j == 'pausa' and jugador.esta_estable():
        if ultima_cadena_jugador > 0:
            ia.recibir_basura(ultima_cadena_jugador * 2)
            ultima_cadena_jugador = 0; combo_jugador = 0
    # IA
    estado_anterior_i = ia.estado
    ia.update(dt)
    if estado_anterior_i != 'pausa' and ia.estado == 'pausa':
        combo_ia += 1
        puntuacion_ia += 10 * combo_ia
        ultima_cadena_ia = combo_ia
    if ia.estado == 'normal' and estado_anterior_i == 'pausa' and ia.esta_estable():
        if ultima_cadena_ia > 0:
            jugador.recibir_basura(ultima_cadena_ia * 2)
            ultima_cadena_ia = 0; combo_ia = 0
    if jugador.esta_perdido(): partida_terminada = True; ganador = "IA"
    elif ia.esta_perdido(): partida_terminada = True; ganador = "Jugador"

def actualizar_ia():
    global ia, turno_ia_timer
    if partida_terminada or pausa: return
    turno_ia_timer += 1
    if turno_ia_timer >= IA_DELAY:
        turno_ia_timer = 0
        copia_logica = ia.copiar()
        if modo_juego == "clasico":
            accion = elegir_movimiento_clasico(copia_logica)
        else:
            try:
                modelo = cargar_modelo()
                accion = predecir_movimiento(copia_logica, modelo)
            except: accion = random.randint(0, ANCHO_TABLERO-2)
        ia.intercambiar(accion)

def actualizar_subida():
    global ultimo_rise, tiempo_subida
    if partida_terminada or pausa: return
    ahora = pygame.time.get_ticks()
    if ahora - ultimo_rise >= tiempo_subida:
        jugador.recibir_basura(1)
        ia.recibir_basura(1)
        ultimo_rise = ahora
        tiempo_subida = max(500, tiempo_subida - 50)

def guardar_historial():
    if historial_jugador:
        with open(ARCHIVO_DATOS, 'a', newline='') as f:
            escritor = csv.writer(f)
            for estado, accion in historial_jugador:
                escritor.writerow(list(estado) + [accion])
        print(f"Guardados {len(historial_jugador)} ejemplos.")
        historial_jugador.clear()

def reiniciar_partida():
    global jugador, ia, partida_terminada, ganador, historial_jugador
    global puntuacion_jugador, puntuacion_ia, combo_jugador, combo_ia
    global ultimo_rise, tiempo_subida, ultima_cadena_jugador, ultima_cadena_ia
    guardar_historial()
    jugador = Board(fisica=True)
    ia = Board(fisica=True)
    partida_terminada = False; ganador = None; historial_jugador = []
    puntuacion_jugador = 0; puntuacion_ia = 0
    combo_jugador = 0; combo_ia = 0
    ultima_cadena_jugador = 0; ultima_cadena_ia = 0
    ultimo_rise = pygame.time.get_ticks()
    tiempo_subida = TIEMPO_SUBIDA_INICIAL

def dibujar_interfaz(proporcion=1.0):
    pantalla.blit(fondo_estatico, (0,0))
    # Partículas decorativas
    for p in particulas:
        p.draw(pantalla)
    # Línea divisoria central con brillo
    centro_x = ANCHO_VENTANA//2
    pygame.draw.line(pantalla, (60,60,80), (centro_x, MARGEN_SUPERIOR), (centro_x, ALTO_VENTANA-MARGEN_INFERIOR), 2)
    for i in range(5):
        pygame.draw.line(pantalla, (100,100,140, 50-i*10), (centro_x-1, MARGEN_SUPERIOR), (centro_x-1, ALTO_VENTANA-MARGEN_INFERIOR), 1)
    # Títulos encima de cada tablero
    tit_jug = fuente_grande.render("JUGADOR", True, (255,255,255))
    tit_ia = fuente_grande.render("IA", True, (255,255,255))
    pantalla.blit(tit_jug, (MARGEN_LATERAL + (ANCHO_TABLERO*TAM_CELDA)//2 - tit_jug.get_width()//2, MARGEN_SUPERIOR-50))
    pantalla.blit(tit_ia, (ANCHO_VENTANA - MARGEN_LATERAL - (ANCHO_TABLERO*TAM_CELDA)//2 - tit_ia.get_width()//2, MARGEN_SUPERIOR-50))
    # Tableros
    offset_jug_x = MARGEN_LATERAL
    offset_ia_x = ANCHO_VENTANA - MARGEN_LATERAL - ANCHO_TABLERO*TAM_CELDA
    offset_y = MARGEN_SUPERIOR
    dibujar_tablero(jugador, offset_jug_x, offset_y, es_jugador=True, tiempo_subida_restante=proporcion)
    dibujar_tablero(ia, offset_ia_x, offset_y, es_jugador=False, tiempo_subida_restante=proporcion)
    dibujar_hud()
    if partida_terminada:
        fin_rect = pygame.Rect(0, ALTO_VENTANA-100, ANCHO_VENTANA, 50)
        pygame.draw.rect(pantalla, (20,20,30,230), fin_rect)
        texto_fin = fuente_grande.render(f"FIN DEL JUEGO. GANADOR: {ganador} (R para reiniciar)", True, (255,255,100))
        pantalla.blit(texto_fin, (ANCHO_VENTANA//2 - texto_fin.get_width()//2, ALTO_VENTANA-90))
    dibujar_animaciones()

def menu_seleccion_modo():
    global modo_juego
    seleccion = 0
    opciones = ["Clásico", "Adaptativo"]
    reloj_local = pygame.time.Clock()
    dt = 0.0
    while True:
        for p in particulas:
            p.update(dt)
        pantalla.blit(fondo_estatico, (0,0))
        for p in particulas:
            p.draw(pantalla)
        titulo = fuente_titulo.render("TETRIS ATTACK", True, (255,255,255))
        sombra = fuente_titulo.render("TETRIS ATTACK", True, (0,0,0))
        pantalla.blit(sombra, (ANCHO_VENTANA//2 - titulo.get_width()//2 + 3, 73))
        pantalla.blit(titulo, (ANCHO_VENTANA//2 - titulo.get_width()//2, 70))
        subtitulo = fuente_grande.render("Panel de Pon IA", True, (200,200,200))
        pantalla.blit(subtitulo, (ANCHO_VENTANA//2 - subtitulo.get_width()//2, 160))
        for i, op in enumerate(opciones):
            color = (255,215,0) if i == seleccion else (200,200,200)
            txt = fuente_grande.render(op, True, color)
            rect = txt.get_rect(center=(ANCHO_VENTANA//2, 300 + i*90))
            if i == seleccion:
                pygame.draw.rect(pantalla, (40,40,60), rect.inflate(60, 25), border_radius=16)
                pygame.draw.rect(pantalla, (255,215,0), rect.inflate(60, 25), 4, border_radius=16)
            pantalla.blit(txt, rect)
        instru = fuente.render("↑↓: Elegir   ENTER: Confirmar   ESC: Salir", True, (150,150,150))
        pantalla.blit(instru, (ANCHO_VENTANA//2 - instru.get_width()//2, ALTO_VENTANA-50))
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_DOWN: seleccion = (seleccion+1)%2
                elif evento.key == pygame.K_UP: seleccion = (seleccion-1)%2
                elif evento.key == pygame.K_RETURN:
                    modo_juego = "clasico" if seleccion==0 else "adaptativo"
                    return
                elif evento.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
        pygame.display.flip()
        dt = reloj_local.tick(60)/1000.0

def main():
    global pausa, partida_terminada, ganador
    while True:
        menu_seleccion_modo()
        reiniciar_partida()
        dt = 0.0
        en_partida = True
        while en_partida:
            ahora = pygame.time.get_ticks()
            tiempo_para_subida = max(0, tiempo_subida - (ahora - ultimo_rise))
            proporcion = tiempo_para_subida / tiempo_subida if tiempo_subida > 0 else 0
            procesar_eventos()
            if pausa:
                accion = menu_pausa()
                if accion == "menu": en_partida = False
                continue
            actualizar_ia()
            actualizar_mundo(dt)
            actualizar_subida()
            dibujar_interfaz(proporcion)
            pygame.display.flip()
            dt = reloj.tick(FPS)/1000.0
        guardar_historial()

if __name__ == "__main__":
    main()