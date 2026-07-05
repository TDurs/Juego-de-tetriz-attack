# ia_clasica.py
from config import ANCHO_TABLERO
import random
import time

def evaluar(board):
    copia = board.copiar()
    puntos, cadenas, _ = copia.resolver_matches()
    altura_max = max(copia.altura_columna(c) for c in range(ANCHO_TABLERO))
    agujeros = copia.contar_agujeros()
    return puntos + 20 * cadenas - 15 * altura_max - 30 * agujeros

def minimax(board, profundidad, alpha, beta, maximizando):
    if profundidad == 0 or board.esta_perdido():
        return evaluar(board), None
    mejor_mov = None
    if maximizando:
        valor = -float('inf')
        for x in range(ANCHO_TABLERO - 1):
            copia = board.copiar()
            copia.cursor_x = x
            if copia.intercambiar(x):
                copia.resolver_matches()
            else:
                continue
            eval_hijo, _ = minimax(copia, profundidad-1, alpha, beta, False)
            if eval_hijo > valor:
                valor = eval_hijo
                mejor_mov = x
            alpha = max(alpha, valor)
            if alpha >= beta:
                break
        return valor, mejor_mov
    else:
        return evaluar(board), None

def elegir_movimiento_clasico(board, tiempo_limite=0.5):
    mejor_accion = None
    mejor_valor = -float('inf')
    inicio = time.time()
    profundidad = 1
    while time.time() - inicio < tiempo_limite:
        valor, accion = minimax(board, profundidad, -float('inf'), float('inf'), True)
        if accion is not None:
            mejor_valor = valor
            mejor_accion = accion
        profundidad += 1
        if profundidad > 4:
            break
    if mejor_accion is None:
        posibles = [x for x in range(ANCHO_TABLERO-1) if board.copiar().intercambiar(x)]
        mejor_accion = random.choice(posibles) if posibles else 0
    return mejor_accion