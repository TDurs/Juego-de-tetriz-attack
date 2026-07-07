# main.py
import pygame
import sys
import random
import math
import csv
from config import *
from board import Board
from ia_clasica import elegir_movimiento_clasico
from ia_adaptativa import cargar_modelo, elegir_movimiento_adaptativo, actualizar_modelo
from puntuaciones import cargar_ranking, guardar_puntaje

pygame.init()
pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
pygame.display.set_caption("Tetris Attack - IA Híbrida")

FUENTE_FAMILIA = "Segoe UI,Verdana,Arial"
fuente = pygame.font.SysFont(FUENTE_FAMILIA, 22)
fuente_grande = pygame.font.SysFont(FUENTE_FAMILIA, 20, bold=True)
fuente_titulo = pygame.font.SysFont(FUENTE_FAMILIA, 50, bold=True)
fuente_hud = pygame.font.SysFont(FUENTE_FAMILIA, 13, bold=True)
fuente_nombre = pygame.font.SysFont(FUENTE_FAMILIA, 50, bold=True)
fuente_chica = pygame.font.SysFont(FUENTE_FAMILIA, 12)
reloj = pygame.time.Clock()

pygame.key.set_repeat(200, 50)

# Configuración global
modo_juego = "clasico"
dificultad_ia = "normal"
velocidad_subida = "normal"

jugador = None
ia = None
modelo_adaptativo = None
turno_ia_timer = 0
ia_accion_pendiente = None      # tupla (columna, fila) donde la IA hizo el intercambio
partida_terminada = False
ganador = None
historial_jugador = []

puntuacion_jugador = 0
puntuacion_ia = 0
combo_jugador = 0
combo_ia = 0
ultima_cadena_jugador = 0
ultima_cadena_ia = 0

TIEMPOS_BASE = {"lento": 6000, "normal": 3000, "rapido": 1500}
tiempo_subida = TIEMPOS_BASE[velocidad_subida]
ultimo_rise = pygame.time.get_ticks()

animaciones = []
pausa = False

# ------------------------------------------------------------
# Utilidades visuales (sin cambios)
# ------------------------------------------------------------
def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def fase(velocidad=1.0):
    return (math.sin(pygame.time.get_ticks() * 0.001 * velocidad) + 1) / 2

def dibujar_gradiente_vertical(superficie, rect, color_top, color_bottom, radius=0):
    x, y, w, h = rect
    if h <= 0: return
    capa = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        color = lerp_color(color_top, color_bottom, t) + (255,)
        pygame.draw.line(capa, color, (0, i), (w, i))
    if radius > 0:
        mascara = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        capa.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    superficie.blit(capa, (x, y))

def panel_ui(superficie, rect, color=COLOR_PANEL_UI, borde=COLOR_BORDE_UI, radius=14, alpha=235, grosor=2):
    x, y, w, h = rect
    capa = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(capa, (*color, alpha), (0, 0, w, h), border_radius=radius)
    pygame.draw.rect(capa, (*borde, 255), (0, 0, w, h), grosor, border_radius=radius)
    superficie.blit(capa, (x, y))

def glow_rect(superficie, rect, color, capas=4, radius=14, alpha_base=40):
    x, y, w, h = rect
    for i in range(capas, 0, -1):
        expand = i * 4
        a = max(0, alpha_base - i * 8)
        halo = pygame.Surface((w + expand * 2, h + expand * 2), pygame.SRCALPHA)
        pygame.draw.rect(halo, (*color, a), halo.get_rect(), border_radius=radius + expand)
        superficie.blit(halo, (x - expand, y - expand))

def crear_fondo():
    surf = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA))
    dibujar_gradiente_vertical(surf, (0, 0, ANCHO_VENTANA, ALTO_VENTANA), COLOR_FONDO_TOP, COLOR_FONDO_BOTTOM)
    for x in range(0, ANCHO_VENTANA, 46):
        for y in range(0, ALTO_VENTANA, 46):
            pygame.draw.circle(surf, (60, 55, 90), (x, y), 1)
    vign = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
    for i in range(90):
        alpha = int(90 * (i / 90) ** 2)
        pygame.draw.rect(vign, (0, 0, 0, alpha), vign.get_rect().inflate(-i * 2, -i * 2), 2)
    surf.blit(vign, (0, 0))
    return surf

fondo_estatico = crear_fondo()

class Estrella:
    def __init__(self):
        self.x = random.randint(0, ANCHO_VENTANA)
        self.y = random.randint(0, ALTO_VENTANA)
        self.vel = random.uniform(8, 30)
        self.tam = random.uniform(0.8, 2.2)
        self.fase_ini = random.uniform(0, 6.28)
        self.color = random.choice([(255, 255, 255), COLOR_ACENTO_2, COLOR_ACENTO])

    def update(self, dt):
        self.y += self.vel * dt
        if self.y > ALTO_VENTANA + 5:
            self.y = -5
            self.x = random.randint(0, ANCHO_VENTANA)

    def draw(self, surf):
        brillo = 0.35 + 0.65 * (math.sin(pygame.time.get_ticks() * 0.002 + self.fase_ini) + 1) / 2
        color = tuple(int(c * brillo) for c in self.color)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), max(1, int(self.tam)))

particulas = [Estrella() for _ in range(60)]

# ------------------------------------------------------------
# Funciones de dibujo del tablero (cursor de IA corregido)
# ------------------------------------------------------------
def dibujar_panel(superficie, color_idx, x, y, w, h):
    if color_idx is None:
        pygame.draw.rect(superficie, (50, 50, 65), (x, y, w, h), 1, border_radius=6)
        return

    base = COLORES_RGB[color_idx]
    claro = COLORES_CLAROS[color_idx]
    oscuro = COLORES_OSCUROS[color_idx]

    sombra = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(sombra, (0, 0, 0, 90), (0, 0, w, h), border_radius=10)
    superficie.blit(sombra, (x + 2, y + 3))

    capa = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        color = lerp_color(claro, oscuro, t)
        pygame.draw.line(capa, (*color, 255), (0, i), (w, i))
    mascara = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=10)
    capa.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    superficie.blit(capa, (x, y))

    pygame.draw.rect(superficie, oscuro, (x, y, w, h), 2, border_radius=10)

    brillo = pygame.Surface((w, h), pygame.SRCALPHA)
    puntos = [(w * 0.18, h * 0.22), (w * 0.42, h * 0.14), (w * 0.30, h * 0.42)]
    pygame.draw.polygon(brillo, (255, 255, 255, 130), puntos)
    pygame.draw.ellipse(brillo, (255, 255, 255, 60), (w * 0.55, h * 0.6, w * 0.32, h * 0.22))
    superficie.blit(brillo, (x, y))
    pygame.draw.circle(superficie, base, (x + w // 2, y + h // 2), max(2, w // 10))

def sombra_rect(superficie, rect, color=(0, 0, 0, 90), desplazamiento=4, radius=12):
    sombra = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(sombra, color, sombra.get_rect(), border_radius=radius)
    superficie.blit(sombra, rect.move(desplazamiento, desplazamiento))

def dibujar_tablero(board, offset_x, offset_y, es_jugador=True, tiempo_subida_restante=1.0, color_tema=COLOR_ACENTO_2):
    ancho_px = ANCHO_TABLERO * TAM_CELDA
    alto_px = ALTO_VISIBLE * TAM_CELDA
    tablero_rect = pygame.Rect(offset_x - 8, offset_y - 8, ancho_px + 16, alto_px + 16)

    sombra_rect(pantalla, tablero_rect, (0, 0, 0, 120), 6, radius=16)
    glow_rect(pantalla, tablero_rect, color_tema, capas=3, radius=16, alpha_base=22)

    fondo_tablero = pygame.Rect(offset_x - 6, offset_y - 6, ancho_px + 12, alto_px + 12)
    dibujar_gradiente_vertical(pantalla, fondo_tablero, (26, 22, 40), (16, 14, 26), radius=14)
    pygame.draw.rect(pantalla, color_tema, fondo_tablero, 2, border_radius=14)

    grid = pygame.Surface((ancho_px, alto_px), pygame.SRCALPHA)
    for c in range(ANCHO_TABLERO + 1):
        x = c * TAM_CELDA
        pygame.draw.line(grid, (255, 255, 255, 12), (x, 0), (x, alto_px), 1)
    for r in range(ALTO_VISIBLE + 1):
        y = r * TAM_CELDA
        pygame.draw.line(grid, (255, 255, 255, 12), (0, y), (ancho_px, y), 1)
    pantalla.blit(grid, (offset_x, offset_y))

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
            dibujar_panel(pantalla, color, x, y, TAM_CELDA - 6, TAM_CELDA - 6)

    # --- Cursor del jugador ---
    if es_jugador:
        cx, cy = board.cursor_x, board.cursor_y
        if inicio_fila <= cy < FILAS_TOTALES:
            fila_vis = cy - inicio_fila
            cx_pix = offset_x + cx * TAM_CELDA
            cy_pix = offset_y + fila_vis * TAM_CELDA
            cursor_rect = pygame.Rect(cx_pix, cy_pix, TAM_CELDA * 2, TAM_CELDA)
            valida = board._posicion_es_valida(cy, cx)
            color_ok = (255, 220, 70)
            color_bad = (255, 90, 100)
            color_borde = color_ok if valida else color_bad
            pulso = fase(2.2)

            aura = pygame.Surface((cursor_rect.width + 20, cursor_rect.height + 20), pygame.SRCALPHA)
            alpha_aura = int(35 + 25 * pulso)
            pygame.draw.rect(aura, (*color_borde, alpha_aura), aura.get_rect(), border_radius=10)
            pantalla.blit(aura, cursor_rect.move(-10, -10))

            grosor = 3 + int(pulso * 2)
            pygame.draw.rect(pantalla, color_borde, cursor_rect, grosor, border_radius=8)
            centro_x = cx_pix + TAM_CELDA
            desp = int(pulso * 3)
            pygame.draw.polygon(pantalla, color_borde,
                [(centro_x - 7, cy_pix - 7 - desp), (centro_x + 7, cy_pix - 7 - desp), (centro_x, cy_pix - 15 - desp)])
            pygame.draw.polygon(pantalla, color_borde,
                [(centro_x - 7, cy_pix + TAM_CELDA + 7 + desp), (centro_x + 7, cy_pix + TAM_CELDA + 7 + desp),
                 (centro_x, cy_pix + TAM_CELDA + 15 + desp)])

    # --- Cursor de la IA (corregido: usa la fila exacta del movimiento) ---
    if not es_jugador and ia_accion_pendiente is not None and board is ia:
        x_col, y_fila = ia_accion_pendiente  # ahora es tupla (columna, fila)
        if inicio_fila <= y_fila < FILAS_TOTALES:
            fila_vis = y_fila - inicio_fila
            cx_pix = offset_x + x_col * TAM_CELDA
            cy_pix = offset_y + fila_vis * TAM_CELDA
            cursor_rect = pygame.Rect(cx_pix, cy_pix, TAM_CELDA*2, TAM_CELDA)
            pulso = fase(3.0)
            color_cursor = COLOR_ACENTO_2
            alpha_aura = int(20 + 15 * pulso)
            aura = pygame.Surface((cursor_rect.width + 16, cursor_rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(aura, (*color_cursor, alpha_aura), aura.get_rect(), border_radius=10)
            pantalla.blit(aura, cursor_rect.move(-8, -8))
            grosor = 2 + int(pulso * 2)
            pygame.draw.rect(pantalla, color_cursor, cursor_rect, grosor, border_radius=6)

    # Barra de subida
    if not partida_terminada:
        barra_rect = pygame.Rect(offset_x, offset_y - 20, ancho_px, 10)
        pygame.draw.rect(pantalla, (20, 20, 30), barra_rect, border_radius=6)
        progreso = 1.0 - tiempo_subida_restante
        ancho_relleno = int(ancho_px * max(0, min(1, progreso)))
        if ancho_relleno > 0:
            relleno = pygame.Rect(offset_x, offset_y - 20, ancho_relleno, 10)
            color_barra = lerp_color((60, 220, 100), (255, 60, 60), progreso)
            pygame.draw.rect(pantalla, color_barra, relleno, border_radius=6)
            if progreso > 0.85:
                glow_rect(pantalla, relleno, (255, 60, 60), capas=2, radius=6, alpha_base=50)
        pygame.draw.rect(pantalla, (70, 70, 90), barra_rect, 1, border_radius=6)

def badge(superficie, centro, texto, color_fondo, color_texto=(20, 20, 25)):
    txt = fuente_chica.render(texto, True, color_texto)
    pad_x, pad_y = 14, 6
    rect = pygame.Rect(0, 0, txt.get_width() + pad_x * 2, txt.get_height() + pad_y * 2)
    rect.center = centro
    pygame.draw.rect(superficie, color_fondo, rect, border_radius=rect.height // 2)
    superficie.blit(txt, (rect.x + pad_x, rect.y + pad_y))

def dibujar_hud():
    panel_rect = pygame.Rect(0, ALTO_VENTANA - 76, ANCHO_VENTANA, 76)
    dibujar_gradiente_vertical(pantalla, panel_rect, (18, 18, 30), (10, 10, 18))
    pygame.draw.line(pantalla, COLOR_BORDE_UI, (0, ALTO_VENTANA - 76), (ANCHO_VENTANA, ALTO_VENTANA - 76), 2)

    if modo_juego == "solitario":
        txt_jug = fuente_hud.render(f"Puntuación  {puntuacion_jugador}", True, COLOR_TEXTO)
        pantalla.blit(txt_jug, (ANCHO_VENTANA // 2 - txt_jug.get_width() // 2, ALTO_VENTANA - 68))
    else:
        pygame.draw.circle(pantalla, COLOR_ACENTO_2, (36, ALTO_VENTANA - 40), 8)
        txt_jug = fuente_hud.render(f"Jugador  {puntuacion_jugador}", True, COLOR_TEXTO)
        pantalla.blit(txt_jug, (52, ALTO_VENTANA - 50))

        txt_ia = fuente_hud.render(f"IA  {puntuacion_ia}", True, COLOR_TEXTO)
        x_ia = ANCHO_VENTANA - 40 - txt_ia.get_width()
        pygame.draw.circle(pantalla, COLOR_ACENTO_3, (x_ia - 16, ALTO_VENTANA - 40), 8)
        pantalla.blit(txt_ia, (x_ia, ALTO_VENTANA - 50))

    badge(pantalla, (ANCHO_VENTANA // 2, ALTO_VENTANA - 30), modo_juego.capitalize(), COLOR_ACENTO)
    txt_pausa = fuente_chica.render("ESC · Pausa", True, COLOR_TEXTO_SUAVE)
    pantalla.blit(txt_pausa, (ANCHO_VENTANA - txt_pausa.get_width() - 24, ALTO_VENTANA - 30))

def mostrar_texto_temporal(texto, x, y, duracion=60, color=(255, 220, 80), tamaño=32):
    fuente_temp = pygame.font.SysFont(FUENTE_FAMILIA, tamaño, bold=True)
    animaciones.append(('texto', (texto, x, y, fuente_temp, color), duracion))

def mostrar_mensaje_centrado(texto, duracion=90, color=(255,255,0), tamaño=40):
    fuente_temp = pygame.font.SysFont(FUENTE_FAMILIA, tamaño, bold=True)
    x = ANCHO_VENTANA // 2 - fuente_temp.size(texto)[0] // 2
    y = ALTO_VENTANA // 2 - 30
    animaciones.append(('texto', (texto, x, y, fuente_temp, color), duracion))

def dibujar_animaciones():
    global animaciones
    restantes = []
    for tipo, datos, tiempo in animaciones:
        if tipo == 'texto':
            texto, x, y, fuente_temp, color = datos
            progreso = 1 - (tiempo / 60)
            alpha = int(255 * min(1.0, tiempo / 25))
            offset_y = -progreso * 18
            escala = 1.0 + 0.15 * math.sin(progreso * math.pi)
            surf = fuente_temp.render(texto, True, color)
            if escala != 1.0:
                w, h = surf.get_size()
                surf = pygame.transform.smoothscale(surf, (max(1, int(w * escala)), max(1, int(h * escala))))
            surf.set_alpha(alpha)
            sombra = pygame.font.SysFont(FUENTE_FAMILIA, fuente_temp.get_height(), bold=True).render(texto, True, (0, 0, 0))
            sombra.set_alpha(alpha // 2)
            pantalla.blit(sombra, (x + 3, y + offset_y + 3))
            pantalla.blit(surf, (x, y + offset_y))
        elif tipo == 'destello':
            x, y, radio = datos
            intensidad = tiempo / 15
            capa = pygame.Surface((int(radio * 4), int(radio * 4)), pygame.SRCALPHA)
            pygame.draw.circle(capa, (255, 235, 150, int(180 * intensidad)),
                                (capa.get_width() // 2, capa.get_height() // 2), int(radio * 2 * intensidad))
            pantalla.blit(capa, (x - capa.get_width() // 2, y - capa.get_height() // 2))
        tiempo -= 1
        if tiempo > 0:
            restantes.append((tipo, datos, tiempo))
    animaciones[:] = restantes

# ------------------------------------------------------------
# Componentes de menú
# ------------------------------------------------------------
def titulo_con_glow(texto, y, tam_fuente=58, color=(255, 255, 255)):
    f = pygame.font.SysFont(FUENTE_FAMILIA, tam_fuente, bold=True)
    txt = f.render(texto, True, color)
    x = ANCHO_VENTANA // 2 - txt.get_width() // 2
    glow = pygame.Surface((txt.get_width() + 40, txt.get_height() + 40), pygame.SRCALPHA)
    glow_txt = f.render(texto, True, COLOR_ACENTO)
    alpha = int(60 + 40 * fase(1.5))
    glow_txt.set_alpha(alpha)
    glow.blit(glow_txt, (20, 20))
    glow = pygame.transform.smoothscale(glow, (int(glow.get_width() * 1.04), int(glow.get_height() * 1.04)))
    pantalla.blit(glow, (x - 20 - (glow.get_width() - txt.get_width() - 40) // 2, y - 20))
    sombra = f.render(texto, True, (0, 0, 0))
    pantalla.blit(sombra, (x + 3, y + 3))
    pantalla.blit(txt, (x, y))

def opcion_menu(texto, y, seleccionada, ancho=420):
    rect = pygame.Rect(0, 0, ancho, 58)
    rect.center = (ANCHO_VENTANA // 2, y)
    if seleccionada:
        glow_rect(pantalla, rect, COLOR_ACENTO, capas=3, radius=16, alpha_base=45)
        panel_ui(pantalla, rect, color=COLOR_PANEL_UI_CLARO, borde=COLOR_ACENTO, radius=16, grosor=3)
        pygame.draw.circle(pantalla, COLOR_ACENTO, (rect.x + 26, rect.centery), 5)
        color_txt = (255, 255, 255)
    else:
        panel_ui(pantalla, rect, color=COLOR_PANEL_UI, borde=COLOR_BORDE_UI, radius=16, grosor=1, alpha=170)
        color_txt = COLOR_TEXTO_SUAVE
    txt = fuente_grande.render(texto, True, color_txt)
    pantalla.blit(txt, (rect.centerx - txt.get_width() // 2 + (14 if seleccionada else 0), rect.centery - txt.get_height() // 2))

# ------------------------------------------------------------
# Menú de pausa (con actualización del modelo al salir)
# ------------------------------------------------------------
def menu_pausa():
    global pausa
    opciones = ["Continuar", "Reiniciar", "Menú Principal", "Salir"]
    seleccion = 0
    while pausa:
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
        overlay.fill((8, 8, 14, 200))
        pantalla.blit(overlay, (0, 0))
        titulo_con_glow("PAUSA", 90, 52)
        for i, op in enumerate(opciones):
            opcion_menu(op, 220 + i * 74, i == seleccion, ancho=320)
        instru = fuente_chica.render("↑ ↓ Navegar   ENTER Elegir   ESC Volver", True, COLOR_TEXTO_SUAVE)
        pantalla.blit(instru, (ANCHO_VENTANA // 2 - instru.get_width() // 2, ALTO_VENTANA - 44))
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                guardar_historial()
                actualizar_modelo()
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE: pausa = False
                elif evento.key == pygame.K_DOWN: seleccion = (seleccion + 1) % 4
                elif evento.key == pygame.K_UP: seleccion = (seleccion - 1) % 4
                elif evento.key == pygame.K_RETURN:
                    if seleccion == 0: pausa = False
                    elif seleccion == 1:
                        guardar_historial()
                        actualizar_modelo()
                        reiniciar_partida()
                        pausa = False
                    elif seleccion == 2:
                        guardar_historial()
                        actualizar_modelo()
                        pausa = False
                        return "menu"
                    elif seleccion == 3:
                        guardar_historial()
                        actualizar_modelo()
                        pygame.quit(); sys.exit()
        pygame.display.flip()
        reloj.tick(30)
    return "juego"

# ------------------------------------------------------------
# Entrada de nombre y ranking (sin cambios)
# ------------------------------------------------------------
def ingresar_nombre(puntaje):
    nombre = ""
    while len(nombre) < 3:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                guardar_historial()
                actualizar_modelo()
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key >= pygame.K_a and evento.key <= pygame.K_z:
                    if len(nombre) < 3:
                        nombre += chr(evento.key).upper()
                elif evento.key == pygame.K_BACKSPACE and len(nombre) > 0:
                    nombre = nombre[:-1]
        pantalla.blit(fondo_estatico, (0, 0))
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
        overlay.fill((8, 8, 14, 190))
        pantalla.blit(overlay, (0, 0))
        titulo_con_glow("¡NUEVO RÉCORD!", 110, 46, color=COLOR_ACENTO)
        txt_sub = fuente_grande.render(f"Puntuación: {puntaje}", True, COLOR_TEXTO)
        pantalla.blit(txt_sub, (ANCHO_VENTANA // 2 - txt_sub.get_width() // 2, 195))
        txt_inst = fuente.render("Ingresa tus iniciales (3 letras)", True, COLOR_TEXTO_SUAVE)
        pantalla.blit(txt_inst, (ANCHO_VENTANA // 2 - txt_inst.get_width() // 2, 260))
        for i in range(3):
            letra = nombre[i] if i < len(nombre) else "_"
            casilla = pygame.Rect(0, 0, 64, 78)
            casilla.center = (ANCHO_VENTANA // 2 - 80 + i * 80, 350)
            activo = i < len(nombre)
            panel_ui(pantalla, casilla, color=COLOR_PANEL_UI_CLARO if activo else COLOR_PANEL_UI,
                     borde=COLOR_ACENTO if activo else COLOR_BORDE_UI, radius=12, grosor=2)
            txt_letra = fuente_nombre.render(letra, True, COLOR_TEXTO if activo else COLOR_TEXTO_SUAVE)
            pantalla.blit(txt_letra, (casilla.centerx - txt_letra.get_width() // 2, casilla.centery - txt_letra.get_height() // 2))
        pygame.display.flip()
        reloj.tick(30)
    return nombre

def mostrar_ranking():
    ranking = cargar_ranking()
    esperando = True
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                guardar_historial()
                actualizar_modelo()
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE or evento.key == pygame.K_RETURN:
                    esperando = False
        pantalla.blit(fondo_estatico, (0, 0))
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
        overlay.fill((8, 8, 14, 210))
        pantalla.blit(overlay, (0, 0))
        titulo_con_glow("MEJORES PUNTAJES", 40, 46, color=COLOR_ACENTO)
        if not ranking:
            txt_vacio = fuente_grande.render("Aún no hay récords", True, COLOR_TEXTO_SUAVE)
            pantalla.blit(txt_vacio, (ANCHO_VENTANA // 2 - txt_vacio.get_width() // 2, 220))
        else:
            for i, entrada in enumerate(ranking):
                fila_rect = pygame.Rect(0, 0, 420, 46)
                fila_rect.center = (ANCHO_VENTANA // 2, 145 + i * 52)
                es_top3 = i < 3
                panel_ui(pantalla, fila_rect,
                         color=COLOR_PANEL_UI_CLARO if es_top3 else COLOR_PANEL_UI,
                         borde=COLOR_ACENTO if es_top3 else COLOR_BORDE_UI,
                         radius=12, grosor=2 if es_top3 else 1, alpha=200)
                color_txt = COLOR_ACENTO if es_top3 else COLOR_TEXTO
                txt = fuente_grande.render(f"{i+1:>2}.  {entrada['nombre']}", True, color_txt)
                puntos = fuente_grande.render(str(entrada['puntaje']), True, color_txt)
                pantalla.blit(txt, (fila_rect.x + 20, fila_rect.centery - txt.get_height() // 2))
                pantalla.blit(puntos, (fila_rect.right - 20 - puntos.get_width(), fila_rect.centery - puntos.get_height() // 2))
        txt_volver = fuente_chica.render("ENTER / ESC para volver", True, COLOR_TEXTO_SUAVE)
        pantalla.blit(txt_volver, (ANCHO_VENTANA // 2 - txt_volver.get_width() // 2, ALTO_VENTANA - 40))
        pygame.display.flip()
        reloj.tick(30)

# ------------------------------------------------------------
# Selección de dificultad
# ------------------------------------------------------------
def menu_dificultad():
    global dificultad_ia
    opciones = ["Fácil", "Normal", "Difícil"]
    seleccion = 1
    while True:
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
        overlay.fill((8, 8, 14, 190))
        pantalla.blit(overlay, (0, 0))
        titulo_con_glow("DIFICULTAD IA", 100, 46)
        for i, op in enumerate(opciones):
            opcion_menu(op, 220 + i * 74, i == seleccion, ancho=320)
        instru = fuente_chica.render("↑ ↓ Elegir   ENTER Confirmar", True, COLOR_TEXTO_SUAVE)
        pantalla.blit(instru, (ANCHO_VENTANA // 2 - instru.get_width() // 2, ALTO_VENTANA - 44))
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                guardar_historial()
                actualizar_modelo()
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_DOWN: seleccion = (seleccion + 1) % 3
                elif evento.key == pygame.K_UP: seleccion = (seleccion - 1) % 3
                elif evento.key == pygame.K_RETURN:
                    dificultad_ia = ["facil", "normal", "dificil"][seleccion]
                    return
        pygame.display.flip()
        reloj.tick(30)

# ------------------------------------------------------------
# Lógica de juego (IA corregida)
# ------------------------------------------------------------
def procesar_eventos():
    global jugador, ia, turno_ia_timer, partida_terminada, ganador, historial_jugador, pausa
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            guardar_historial()
            actualizar_modelo()
            pygame.quit(); sys.exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE and not partida_terminada:
                pausa = True; continue
            if partida_terminada:
                continue
            if pausa: continue
            if evento.key == pygame.K_LEFT: jugador.mover_cursor(-1, 0)
            elif evento.key == pygame.K_RIGHT: jugador.mover_cursor(1, 0)
            elif evento.key == pygame.K_UP: jugador.mover_cursor(0, -1)
            elif evento.key == pygame.K_DOWN: jugador.mover_cursor(0, 1)
            elif evento.key == pygame.K_SPACE:
                estado_previo = jugador.estado_a_vector()
                columna_accion = jugador.cursor_x
                if jugador.intercambiar():
                    destello_x = MARGEN_LATERAL + jugador.cursor_x * TAM_CELDA + TAM_CELDA // 2
                    destello_y = MARGEN_SUPERIOR + (jugador.cursor_y - (FILAS_TOTALES - ALTO_VISIBLE)) * TAM_CELDA + TAM_CELDA // 2
                    animaciones.append(('destello', (destello_x, destello_y, 12), 15))
                    turno_ia_timer = 0
                    historial_jugador.append((estado_previo, columna_accion))

def actualizar_mundo(dt):
    global jugador, ia, puntuacion_jugador, puntuacion_ia, combo_jugador, combo_ia
    global ultima_cadena_jugador, ultima_cadena_ia, partida_terminada, ganador
    if pausa: return

    if modo_juego != "solitario":
        estado_anterior_j = jugador.estado
        jugador.update(dt)
        if estado_anterior_j != 'pausa' and jugador.estado == 'pausa':
            combo_jugador += 1
            puntuacion_jugador += 10 * combo_jugador
            if combo_jugador > 1:
                mostrar_texto_temporal(f"COMBO x{combo_jugador}!", ANCHO_VENTANA // 2 - 120, ALTO_VENTANA // 2 - 50)
            ultima_cadena_jugador = combo_jugador
        if jugador.estado == 'normal' and estado_anterior_j == 'pausa' and jugador.esta_estable():
            if ultima_cadena_jugador > 0:
                ia.recibir_basura(ultima_cadena_jugador * 2)
                ultima_cadena_jugador = 0; combo_jugador = 0

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
    else:
        estado_anterior = jugador.estado
        jugador.update(dt)
        if estado_anterior != 'pausa' and jugador.estado == 'pausa':
            combo_jugador += 1
            puntuacion_jugador += 10 * combo_jugador
            if combo_jugador > 1:
                mostrar_texto_temporal(f"COMBO x{combo_jugador}!", ANCHO_VENTANA // 2 - 120, ALTO_VENTANA // 2 - 50)
        if jugador.esta_perdido():
            partida_terminada = True
            ganador = "Jugador"

def actualizar_ia():
    global ia, turno_ia_timer, modelo_adaptativo, ia_accion_pendiente
    if modo_juego == "solitario" or partida_terminada or pausa:
        return
    turno_ia_timer += 1
    if turno_ia_timer >= IA_DELAY:
        turno_ia_timer = 0
        ia_accion_pendiente = None   # limpiamos el cursor anterior
        copia_logica = ia.copiar()
        if modo_juego == "clasico":
            resultado = elegir_movimiento_clasico(copia_logica, dificultad_ia)
            if resultado is not None:
                x, y = resultado
                ia_accion_pendiente = (x, y)   # tupla con columna y fila
                ia.intercambiar_en(x, y)
        else:  # adaptativo
            if modelo_adaptativo is None:
                modelo_adaptativo = cargar_modelo()
            resultado = elegir_movimiento_adaptativo(copia_logica, modelo_adaptativo)
            if resultado != (None, None):
                x, y = resultado
                ia_accion_pendiente = (x, y)
                ia.intercambiar_en(x, y)

def actualizar_subida():
    global ultimo_rise, tiempo_subida
    if partida_terminada or pausa: return
    ahora = pygame.time.get_ticks()
    if ahora - ultimo_rise >= tiempo_subida:
        jugador.recibir_basura(1)
        if modo_juego != "solitario":
            ia.recibir_basura(1)
        ultimo_rise = ahora
        if velocidad_subida == "rapido":
            tiempo_subida = max(300, tiempo_subida - 80)
        elif velocidad_subida == "normal":
            tiempo_subida = max(500, tiempo_subida - 50)
        else:
            tiempo_subida = max(800, tiempo_subida - 30)

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
    global modelo_adaptativo, ia_accion_pendiente

    guardar_historial()
    jugador = Board(fisica=True)
    if modo_juego != "solitario":
        ia = Board(fisica=True)
    else:
        ia = None
    partida_terminada = False; ganador = None; historial_jugador = []
    puntuacion_jugador = 0; puntuacion_ia = 0
    combo_jugador = 0; combo_ia = 0
    ultima_cadena_jugador = 0; ultima_cadena_ia = 0
    ultimo_rise = pygame.time.get_ticks()
    tiempo_subida = TIEMPOS_BASE[velocidad_subida]
    ia_accion_pendiente = None

    if modo_juego == "adaptativo":
        modelo_adaptativo = cargar_modelo()
    else:
        modelo_adaptativo = None

def dibujar_interfaz(proporcion=1.0):
    pantalla.blit(fondo_estatico, (0, 0))
    for p in particulas:
        p.draw(pantalla)
    if modo_juego != "solitario":
        centro_x = ANCHO_VENTANA // 2
        linea = pygame.Surface((3, ALTO_VENTANA - MARGEN_SUPERIOR - MARGEN_INFERIOR), pygame.SRCALPHA)
        dibujar_gradiente_vertical(linea, (0, 0, 3, linea.get_height()), (120, 110, 170), (60, 55, 90))
        pantalla.blit(linea, (centro_x - 1, MARGEN_SUPERIOR))

        tit_jug = fuente_grande.render("JUGADOR", True, COLOR_ACENTO_2)
        tit_ia = fuente_grande.render("IA", True, COLOR_ACENTO_3)
        pantalla.blit(tit_jug, (MARGEN_LATERAL + (ANCHO_TABLERO * TAM_CELDA) // 2 - tit_jug.get_width() // 2, MARGEN_SUPERIOR - 48))
        pantalla.blit(tit_ia, (ANCHO_VENTANA - MARGEN_LATERAL - (ANCHO_TABLERO * TAM_CELDA) // 2 - tit_ia.get_width() // 2, MARGEN_SUPERIOR - 48))
        offset_jug_x = MARGEN_LATERAL
        offset_ia_x = ANCHO_VENTANA - MARGEN_LATERAL - ANCHO_TABLERO * TAM_CELDA
        offset_y = MARGEN_SUPERIOR
        dibujar_tablero(jugador, offset_jug_x, offset_y, es_jugador=True, tiempo_subida_restante=proporcion, color_tema=COLOR_ACENTO_2)
        dibujar_tablero(ia, offset_ia_x, offset_y, es_jugador=False, tiempo_subida_restante=proporcion, color_tema=COLOR_ACENTO_3)
    else:
        offset_x = ANCHO_VENTANA // 2 - (ANCHO_TABLERO * TAM_CELDA) // 2
        offset_y = MARGEN_SUPERIOR
        tit_jug = fuente_grande.render("SOLITARIO", True, COLOR_ACENTO)
        pantalla.blit(tit_jug, (ANCHO_VENTANA // 2 - tit_jug.get_width() // 2, MARGEN_SUPERIOR - 48))
        dibujar_tablero(jugador, offset_x, offset_y, es_jugador=True, tiempo_subida_restante=proporcion, color_tema=COLOR_ACENTO)
    dibujar_hud()
    if partida_terminada:
        overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
        overlay.fill((8, 8, 14, 190))
        pantalla.blit(overlay, (0, 0))
        if modo_juego == "solitario":
            titulo_con_glow("¡FIN DE PARTIDA!", ALTO_VENTANA // 2 - 90, 44, color=COLOR_ACENTO)
            texto_fin = fuente_grande.render(f"Puntuación: {puntuacion_jugador}", True, COLOR_TEXTO)
        else:
            titulo_con_glow("FIN DEL JUEGO", ALTO_VENTANA // 2 - 90, 44, color=COLOR_ACENTO)
            texto_fin = fuente_grande.render(f"Ganador: {ganador}", True, COLOR_TEXTO)
        pantalla.blit(texto_fin, (ANCHO_VENTANA // 2 - texto_fin.get_width() // 2, ALTO_VENTANA // 2 - 10))
        texto_continuar = fuente_chica.render("ENTER o R para continuar", True, COLOR_TEXTO_SUAVE)
        pantalla.blit(texto_continuar, (ANCHO_VENTANA // 2 - texto_continuar.get_width() // 2, ALTO_VENTANA // 2 + 40))
    dibujar_animaciones()

# ------------------------------------------------------------
# Menú principal
# ------------------------------------------------------------
def menu_seleccion_modo():
    global modo_juego, velocidad_subida, dificultad_ia
    seleccion = 0
    opciones = ["Clásico", "Adaptativo", "Solitario", "Récords",
                f"Velocidad: {velocidad_subida.capitalize()}", "Salir"]
    reloj_local = pygame.time.Clock()
    dt = 0.0
    while True:
        for p in particulas:
            p.update(dt)
        pantalla.blit(fondo_estatico, (0, 0))
        for p in particulas:
            p.draw(pantalla)
        titulo_con_glow("TETRIS ATTACK", 62, 58)
        subtitulo = fuente.render("Panel de Pon · IA Híbrida", True, COLOR_TEXTO_SUAVE)
        pantalla.blit(subtitulo, (ANCHO_VENTANA // 2 - subtitulo.get_width() // 2, 138))
        for i, op in enumerate(opciones):
            opcion_menu(op, 210 + i * 62, i == seleccion)
        instru = fuente_chica.render("↑ ↓ Elegir   ENTER Confirmar   ← → Cambiar velocidad", True, COLOR_TEXTO_SUAVE)
        pantalla.blit(instru, (ANCHO_VENTANA // 2 - instru.get_width() // 2, ALTO_VENTANA - 40))
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                guardar_historial()
                actualizar_modelo()
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_DOWN: seleccion = (seleccion + 1) % len(opciones)
                elif evento.key == pygame.K_UP: seleccion = (seleccion - 1) % len(opciones)
                elif evento.key == pygame.K_RETURN:
                    if seleccion == 0:
                        menu_dificultad()
                        modo_juego = "clasico"; return
                    elif seleccion == 1:
                        modo_juego = "adaptativo"; return
                    elif seleccion == 2:
                        modo_juego = "solitario"; return
                    elif seleccion == 3:
                        mostrar_ranking()
                    elif seleccion == 4:
                        pass
                    elif seleccion == 5:
                        guardar_historial()
                        actualizar_modelo()
                        pygame.quit(); sys.exit()
                elif evento.key == pygame.K_ESCAPE:
                    guardar_historial()
                    actualizar_modelo()
                    pygame.quit(); sys.exit()
                if seleccion == 4:
                    if evento.key == pygame.K_LEFT or evento.key == pygame.K_RIGHT:
                        if velocidad_subida == "lento":
                            velocidad_subida = "normal" if evento.key == pygame.K_RIGHT else "rapido"
                        elif velocidad_subida == "normal":
                            velocidad_subida = "rapido" if evento.key == pygame.K_RIGHT else "lento"
                        elif velocidad_subida == "rapido":
                            velocidad_subida = "lento" if evento.key == pygame.K_RIGHT else "normal"
                        opciones[4] = f"Velocidad: {velocidad_subida.capitalize()}"
        pygame.display.flip()
        dt = reloj_local.tick(60) / 1000.0

# ------------------------------------------------------------
# Bucle principal
# ------------------------------------------------------------
def main():
    global pausa, partida_terminada, ganador, modo_juego, puntuacion_jugador, tiempo_subida, velocidad_subida
    while True:
        menu_seleccion_modo()
        tiempo_subida = TIEMPOS_BASE[velocidad_subida]
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
            dt = reloj.tick(FPS) / 1000.0

            if partida_terminada:
                reloj.tick(30)
                esperando = True
                while esperando:
                    for evento in pygame.event.get():
                        if evento.type == pygame.QUIT:
                            guardar_historial()
                            actualizar_modelo()
                            pygame.quit(); sys.exit()
                        if evento.type == pygame.KEYDOWN:
                            if evento.key == pygame.K_RETURN or evento.key == pygame.K_r:
                                esperando = False
                    dibujar_interfaz(proporcion)
                    pygame.display.flip()
                    reloj.tick(30)
                break

        guardar_historial()
        mostrar_mensaje_centrado("Actualizando IA...", 80, COLOR_ACENTO, 36)
        actualizar_modelo()
        mostrar_mensaje_centrado("¡IA actualizada!", 120, (100,255,100), 36)

        if modo_juego == "solitario" and partida_terminada and puntuacion_jugador > 0:
            ranking = cargar_ranking()
            if len(ranking) < 10 or puntuacion_jugador > ranking[-1]['puntaje']:
                nombre = ingresar_nombre(puntuacion_jugador)
                guardar_puntaje(nombre, puntuacion_jugador)
            mostrar_ranking()

if __name__ == "__main__":
    main()