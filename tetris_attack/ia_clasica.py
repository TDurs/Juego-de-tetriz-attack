# ia_clasica.py
import random
import time
from config import ANCHO_TABLERO, FILAS_TOTALES
from evaluacion import evaluar

def minimax(board, profundidad, alpha, beta, maximizando):
    if profundidad == 0 or board.esta_perdido():
        return evaluar(board), None

    if maximizando:
        mejor_valor = -float('inf')
        mejor_mov = None
        # Explorar todas las columnas
        for x in range(ANCHO_TABLERO - 1):
            # Y para cada columna, todas las filas donde el intercambio sea legal
            for y in range(FILAS_TOTALES):
                if not board._posicion_es_valida(y, x):
                    continue
                copia = board.copiar()
                if copia.intercambiar_en(x, y):
                    copia.resolver_matches()
                    eval_hijo, _ = minimax(copia, profundidad - 1, alpha, beta, False)
                    if eval_hijo > mejor_valor:
                        mejor_valor = eval_hijo
                        mejor_mov = (x, y)
                    alpha = max(alpha, mejor_valor)
                    if alpha >= beta:
                        break
            if alpha >= beta:
                break
        return mejor_valor, mejor_mov
    else:
        # Nivel del "entorno" (pasivo) – simplemente evaluamos
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

    # Movimiento aleatorio con cierta probabilidad en fácil
    if random.random() < prob_aleatorio:
        posibles = []
        for x in range(ANCHO_TABLERO - 1):
            for y in range(FILAS_TOTALES):
                if board._posicion_es_valida(y, x):
                    posibles.append((x, y))
        if posibles:
            return random.choice(posibles)
        return (0, FILAS_TOTALES - 1)

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

    # Si no se encontró ningún movimiento (raro), buscar el primer movimiento legal
    if mejor_accion is None:
        for x in range(ANCHO_TABLERO - 1):
            for y in range(FILAS_TOTALES):
                if board._posicion_es_valida(y, x):
                    mejor_accion = (x, y)
                    break
            if mejor_accion:
                break

    return mejor_accion