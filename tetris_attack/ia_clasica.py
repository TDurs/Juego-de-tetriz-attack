# ia_clasica.py
import random
import time
from config import ANCHO_TABLERO
from evaluacion import evaluar

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

def elegir_movimiento_clasico(board, dificultad="normal"):
    if dificultad == "facil":
        tiempo_limite = 0.2
        profundidad_max = 1
        prob_aleatorio = 0.3
    elif dificultad == "dificil":
        tiempo_limite = 1.0
        profundidad_max = 6
        prob_aleatorio = 0.0
    else:  # normal
        tiempo_limite = 0.5
        profundidad_max = 4
        prob_aleatorio = 0.0

    if random.random() < prob_aleatorio:
        posibles = [x for x in range(ANCHO_TABLERO-1) if board.copiar().intercambiar(x)]
        return random.choice(posibles) if posibles else 0

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
        if profundidad > profundidad_max:
            break
    if mejor_accion is None:
        posibles = [x for x in range(ANCHO_TABLERO-1) if board.copiar().intercambiar(x)]
        mejor_accion = random.choice(posibles) if posibles else 0
    return mejor_accion