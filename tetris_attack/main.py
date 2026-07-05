# main.py
import pygame
import sys
import random
import csv
from config import *
from board import Board
from utils import copiar_tablero
from ia_clasica import elegir_movimiento_clasico
from ia_adaptativa import cargar_modelo, predecir_movimiento

pygame.init()
pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
pygame.display.set_caption("Tetris Attack - IA Híbrida")
fuente = pygame.font.SysFont("Arial", 18)
fuente_grande = pygame.font.SysFont("Arial", 32, bold=True)
reloj = pygame.time.Clock()

pygame.key.set_repeat(200, 50)

modo_juego = "clasico"
jugador = Board()
ia = Board()
turno_ia_timer = 0
partida_terminada = False
ganador = None
historial_jugador = []

puntuacion_jugador = 0
puntuacion_ia = 0
combo_jugador = 0
combo_ia = 0

TIEMPO_SUBIDA_INICIAL = 3000
tiempo_subida = TIEMPO_SUBIDA_INICIAL
ultimo_rise = pygame.time.get_ticks()

animaciones = []

COLOR_FONDO = (20, 20, 30)
COLOR_LINEAS_GUIA = (50, 50, 60)
ALPHA_BRILLO = 80

def dibujar_panel(superficie, color_idx, rect, con_brillo=True):
    if color_idx is None:
        pygame.draw.rect(superficie, (30, 30, 40), rect, 1)
        return
    color_base = COLORES_RGB[color_idx]
    x, y, w, h = rect
    pygame.draw.rect(superficie, color_base, rect)
    borde_claro = [min(c + 80, 255) for c in color_base]
    pygame.draw.line(superficie, borde_claro, (x, y), (x+w-1, y), 2)
    pygame.draw.line(superficie, borde_claro, (x, y), (x, y+h-1), 2)
    borde_oscuro = [max(c - 80, 0) for c in color_base]
    pygame.draw.line(superficie, borde_oscuro, (x, y+h-1), (x+w-1, y+h-1), 2)
    pygame.draw.line(superficie, borde_oscuro, (x+w-1, y), (x+w-1, y+h-1), 2)
    if con_brillo:
        brillo_surf = pygame.Surface((w//2, h//2), pygame.SRCALPHA)
        brillo_surf.fill((255, 255, 255, ALPHA_BRILLO))
        superficie.blit(brillo_surf, (x+2, y+2))

def dibujar_tablero(board, offset_x, offset_y, es_jugador=True, tiempo_subida_restante=1.0):
    tablero_rect = pygame.Rect(offset_x-5, offset_y-5, ANCHO_TABLERO*TAM_CELDA+10, ALTO_VISIBLE*TAM_CELDA+10)
    pygame.draw.rect(pantalla, (10, 10, 15), tablero_rect, border_radius=8)
    for c in range(ANCHO_TABLERO+1):
        x = offset_x + c*TAM_CELDA
        pygame.draw.line(pantalla, COLOR_LINEAS_GUIA, (x, offset_y), (x, offset_y+ALTO_VISIBLE*TAM_CELDA), 1)
    for r in range(ALTO_VISIBLE+1):
        y = offset_y + r*TAM_CELDA
        pygame.draw.line(pantalla, COLOR_LINEAS_GUIA, (offset_x, y), (offset_x+ANCHO_TABLERO*TAM_CELDA, y), 1)

    inicio_fila = FILAS_TOTALES - ALTO_VISIBLE
    # Dibujar paneles con interpolación si están cayendo (animación visual)
    for r in range(inicio_fila, FILAS_TOTALES):
        for c in range(ANCHO_TABLERO):
            color = board.matriz[r][c]
            if color is None:
                continue
            if es_jugador and board.cayendo:
                encontrado = False
                for p in board.paneles_cayendo:
                    if p['col'] == c and p['fila_fin'] == r:
                        progreso = 1.0 - (board.frames_caida / board.max_frames_caida)
                        fila_actual = p['fila_ini'] + (p['fila_fin'] - p['fila_ini']) * progreso
                        if inicio_fila <= fila_actual < FILAS_TOTALES:
                            fila_vis = fila_actual - inicio_fila
                            x = offset_x + c * TAM_CELDA + 2
                            y = offset_y + fila_vis * TAM_CELDA + 2
                            rect = pygame.Rect(x, y, TAM_CELDA-4, TAM_CELDA-4)
                            dibujar_panel(pantalla, color, rect)
                        encontrado = True
                        break
                if not encontrado:
                    x = offset_x + c * TAM_CELDA + 2
                    y = offset_y + (r - inicio_fila) * TAM_CELDA + 2
                    rect = pygame.Rect(x, y, TAM_CELDA-4, TAM_CELDA-4)
                    dibujar_panel(pantalla, color, rect)
            else:
                x = offset_x + c * TAM_CELDA + 2
                y = offset_y + (r - inicio_fila) * TAM_CELDA + 2
                rect = pygame.Rect(x, y, TAM_CELDA-4, TAM_CELDA-4)
                dibujar_panel(pantalla, color, rect)

    # Cursor del jugador (siempre visible)
    if es_jugador:
        cx = board.cursor_x
        cy = board.cursor_y
        if inicio_fila <= cy < FILAS_TOTALES:
            fila_visible = cy - inicio_fila
            cx_pix = offset_x + cx * TAM_CELDA
            cy_pix = offset_y + fila_visible * TAM_CELDA
            cursor_rect = pygame.Rect(cx_pix, cy_pix, TAM_CELDA*2, TAM_CELDA)
            valida = board._posicion_es_valida(cy, cx)
            color_borde = (255, 255, 0, 140) if valida else (255, 100, 100, 120)
            sombra_surf = pygame.Surface((cursor_rect.width, cursor_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(sombra_surf, (0, 0, 0, 60), sombra_surf.get_rect(), border_radius=4)
            pantalla.blit(sombra_surf, cursor_rect.move(2, 2))
            cursor_surf = pygame.Surface((cursor_rect.width, cursor_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(cursor_surf, color_borde, cursor_surf.get_rect(), 4, border_radius=4)
            pantalla.blit(cursor_surf, cursor_rect)
            centro_x = cx_pix + TAM_CELDA
            centro_y = cy_pix - 5
            puntos_triangulo = [(centro_x-5, centro_y+5), (centro_x+5, centro_y+5), (centro_x, centro_y-5)]
            color_tri = (255, 255, 0, 200) if valida else (255, 100, 100, 180)
            pygame.draw.polygon(pantalla, color_tri, puntos_triangulo)

    if not partida_terminada:
        barra_ancho = ANCHO_TABLERO * TAM_CELDA
        barra_rect = pygame.Rect(offset_x, offset_y - 12, barra_ancho, 8)
        pygame.draw.rect(pantalla, (50, 50, 50), barra_rect, border_radius=4)
        progreso = 1.0 - tiempo_subida_restante
        relleno = pygame.Rect(offset_x, offset_y - 12, barra_ancho * max(0, min(1, progreso)), 8)
        color_barra = (0, 255, 0) if progreso < 0.7 else (255, 255, 0) if progreso < 0.9 else (255, 0, 0)
        pygame.draw.rect(pantalla, color_barra, relleno, border_radius=4)

def mostrar_texto_temporal(texto, x, y, duracion=60, color=(255, 255, 0), tamaño=24):
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
            pantalla.blit(surf, (x, y))
        elif tipo == 'destello':
            x, y, radio = datos
            intensidad = tiempo / 15
            color = (255, 255, 100 * intensidad)
            pygame.draw.circle(pantalla, color, (int(x), int(y)), int(radio * intensidad))
        tiempo -= 1
        if tiempo <= 0:
            animaciones.remove(anim)
        else:
            animaciones[animaciones.index(anim)] = (tipo, datos, tiempo)

def dibujar_hud():
    txt_jug = fuente.render(f"Puntos: {puntuacion_jugador}", True, (255, 255, 255))
    pantalla.blit(txt_jug, (10, ALTO_VENTANA-60))
    txt_ia = fuente.render(f"Puntos IA: {puntuacion_ia}", True, (255, 255, 255))
    pantalla.blit(txt_ia, (ANCHO_VENTANA//2 + 20, ALTO_VENTANA-60))
    txt_modo = fuente.render(f"Modo: {modo_juego.upper()}", True, (200, 200, 200))
    pantalla.blit(txt_modo, (ANCHO_VENTANA//2 - 60, 10))

def procesar_eventos():
    global jugador, ia, turno_ia_timer, partida_terminada, ganador, historial_jugador
    global puntuacion_jugador, combo_jugador
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if evento.type == pygame.KEYDOWN:
            if partida_terminada:
                if evento.key == pygame.K_r:
                    reiniciar_partida()
                continue
            # Movimiento del cursor siempre permitido
            if evento.key == pygame.K_LEFT:
                jugador.mover_cursor(-1, 0)
            elif evento.key == pygame.K_RIGHT:
                jugador.mover_cursor(1, 0)
            elif evento.key == pygame.K_UP:
                jugador.mover_cursor(0, -1)
            elif evento.key == pygame.K_DOWN:
                jugador.mover_cursor(0, 1)
            elif evento.key == pygame.K_SPACE:
                # Permitir intercambio incluso durante la caída visual
                # Cancelamos la animación de caída anterior si existía
                if jugador.cayendo:
                    jugador.cayendo = False
                    jugador.paneles_cayendo.clear()
                
                matriz_antes = copiar_tablero(jugador.matriz)
                estado_vector = jugador.estado_a_vector()
                if jugador.intercambiar():
                    destello_x = 10 + jugador.cursor_x * TAM_CELDA + TAM_CELDA//2
                    destello_y = 40 + (jugador.cursor_y - (FILAS_TOTALES - ALTO_VISIBLE)) * TAM_CELDA + TAM_CELDA//2
                    animaciones.append(('destello', (destello_x, destello_y, 8), 15))
                    puntos, cadenas, basura = jugador.actualizar()
                    puntuacion_jugador += puntos
                    combo_jugador = max(combo_jugador, cadenas) if cadenas > 0 else 0
                    if cadenas > 1:
                        mostrar_texto_temporal(f"COMBO x{cadenas}!", 120, ALTO_VENTANA//2, duracion=90)
                    # Iniciar nueva caída si hubo cambios
                    if cadenas > 0:
                        jugador.iniciar_caida(matriz_antes)
                    if basura > 0:
                        ia.recibir_basura(basura)
                    if modo_juego == "adaptativo":
                        historial_jugador.append((estado_vector, jugador.cursor_x))
                    turno_ia_timer = 0

def actualizar_ia():
    global ia, jugador, turno_ia_timer, partida_terminada, ganador
    global puntuacion_ia, combo_ia
    if partida_terminada:
        return
    turno_ia_timer += 1
    if turno_ia_timer >= IA_DELAY:
        turno_ia_timer = 0
        if modo_juego == "clasico":
            accion = elegir_movimiento_clasico(ia)
        else:
            try:
                modelo = cargar_modelo()
                accion = predecir_movimiento(ia, modelo)
            except:
                accion = random.randint(0, ANCHO_TABLERO-2)
        if ia.intercambiar(accion):
            puntos, cadenas, basura = ia.actualizar()
            puntuacion_ia += puntos
            combo_ia = max(combo_ia, cadenas) if cadenas > 0 else 0
            if basura > 0:
                jugador.recibir_basura(basura)
        if jugador.esta_perdido():
            partida_terminada = True
            ganador = "IA"
        elif ia.esta_perdido():
            partida_terminada = True
            ganador = "Jugador"

def actualizar_subida():
    global ultimo_rise, tiempo_subida
    ahora = pygame.time.get_ticks()
    if ahora - ultimo_rise >= tiempo_subida:
        jugador.recibir_basura(1)
        ia.recibir_basura(1)
        # Limpiar automáticamente sin animar (instantáneo)
        jugador.actualizar()
        ia.actualizar()
        ultimo_rise = ahora
        tiempo_subida = max(500, tiempo_subida - 50)
    if jugador.esta_perdido():
        partida_terminada = True
        ganador = "IA"
    elif ia.esta_perdido():
        partida_terminada = True
        ganador = "Jugador"

def guardar_historial():
    if historial_jugador:
        with open(ARCHIVO_DATOS, 'a', newline='') as f:
            escritor = csv.writer(f)
            for estado, accion in historial_jugador:
                escritor.writerow(list(estado) + [accion])
        print(f"Se guardaron {len(historial_jugador)} ejemplos en {ARCHIVO_DATOS}")
        historial_jugador.clear()

def reiniciar_partida():
    global jugador, ia, partida_terminada, ganador, historial_jugador
    global puntuacion_jugador, puntuacion_ia, combo_jugador, combo_ia
    global ultimo_rise, tiempo_subida
    guardar_historial()
    jugador = Board()
    ia = Board()
    partida_terminada = False
    ganador = None
    historial_jugador = []
    puntuacion_jugador = 0
    puntuacion_ia = 0
    combo_jugador = 0
    combo_ia = 0
    ultimo_rise = pygame.time.get_ticks()
    tiempo_subida = TIEMPO_SUBIDA_INICIAL

def dibujar_interfaz(proporcion=1.0):
    pantalla.fill(COLOR_FONDO)
    texto_jugador = fuente.render("JUGADOR", True, (255, 255, 255))
    pantalla.blit(texto_jugador, (10, 10))
    texto_ia = fuente.render("IA", True, (255, 255, 255))
    pantalla.blit(texto_ia, (ANCHO_VENTANA//2 + 20, 10))
    dibujar_tablero(jugador, 10, 40, es_jugador=True, tiempo_subida_restante=proporcion)
    dibujar_tablero(ia, ANCHO_VENTANA//2 + 20, 40, es_jugador=False, tiempo_subida_restante=proporcion)
    dibujar_hud()
    if partida_terminada:
        texto_fin = fuente.render(f"FIN DEL JUEGO. GANADOR: {ganador} (R para reiniciar)", True, (255, 255, 0))
        pantalla.blit(texto_fin, (ANCHO_VENTANA//2 - 200, ALTO_VENTANA-80))
    dibujar_animaciones()

def menu_seleccion_modo():
    global modo_juego
    seleccion = 0
    opciones = ["clasico", "adaptativo"]
    fondo = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA))
    fondo.fill((15, 15, 30))
    titulo_fuente = pygame.font.SysFont("Arial", 40, bold=True)
    titulo_surf = titulo_fuente.render("TETRIS ATTACK IA", True, (255, 255, 255))
    titulo_rect = titulo_surf.get_rect(center=(ANCHO_VENTANA//2, 80))
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_DOWN:
                    seleccion = (seleccion + 1) % len(opciones)
                elif evento.key == pygame.K_UP:
                    seleccion = (seleccion - 1) % len(opciones)
                elif evento.key == pygame.K_RETURN:
                    modo_juego = opciones[seleccion]
                    return
        pantalla.blit(fondo, (0, 0))
        pantalla.blit(titulo_surf, titulo_rect)
        for i, op in enumerate(opciones):
            color = (255, 215, 0) if i == seleccion else (180, 180, 180)
            if i == seleccion:
                pygame.draw.rect(pantalla, (50, 50, 70), (ANCHO_VENTANA//2-90, 190+i*70, 180, 50), border_radius=10)
            texto = fuente_grande.render(op.capitalize(), True, color)
            texto_rect = texto.get_rect(center=(ANCHO_VENTANA//2, 215+i*70))
            pantalla.blit(texto, texto_rect)
        instrucciones = fuente.render("Usa ↑↓ para elegir, ENTER para confirmar", True, (150, 150, 150))
        pantalla.blit(instrucciones, (ANCHO_VENTANA//2 - 180, 400))
        pygame.display.flip()
        reloj.tick(30)

def main():
    menu_seleccion_modo()
    reloj.tick(FPS)
    while True:
        ahora = pygame.time.get_ticks()
        tiempo_para_subida = max(0, tiempo_subida - (ahora - ultimo_rise))
        proporcion = tiempo_para_subida / tiempo_subida if tiempo_subida > 0 else 0

        # Actualizar animación de caída (sigue su curso aunque el jugador haga cosas)
        jugador.actualizar_caida()

        procesar_eventos()
        actualizar_ia()
        actualizar_subida()
        dibujar_interfaz(proporcion)
        pygame.display.flip()
        reloj.tick(FPS)

if __name__ == "__main__":
    main()