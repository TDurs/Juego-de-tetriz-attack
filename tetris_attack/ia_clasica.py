# ia_clasica.py
from board import Board
from config import ANCHO_TABLERO
import random
import time

def evaluar(board):
    """Función heurística para el estado actual. A mayor valor, mejor para la IA."""
    copia = board.copiar()
    puntos, cadenas, basura = copia.actualizar()
    altura_max = max([copia.altura_columna(c) for c in range(ANCHO_TABLERO)])
    agujeros = copia.contar_agujeros()
    # Pesos ajustables
    score = puntos + 20 * cadenas - 15 * altura_max - 30 * agujeros
    return score

def minimax(board, profundidad, alpha, beta, maximizando):
    """
    Algoritmo Minimax con poda alfa-beta.
    'maximizando' = True significa que es el turno de la IA de buscar su mejor movimiento.
    """
    if profundidad == 0 or board.esta_perdido():
        return evaluar(board), None

    mejor_mov = None
    if maximizando:
        valor = -float('inf')
        for x in range(ANCHO_TABLERO - 1):
            copia = board.copiar()
            copia.cursor_x = x
            if copia.intercambiar(x):
                copia.actualizar()  # realiza la cascada
            else:
                continue  # movimiento inválido (no hay paneles para intercambiar)
            eval_hijo, _ = minimax(copia, profundidad-1, alpha, beta, False)
            if eval_hijo > valor:
                valor = eval_hijo
                mejor_mov = x
            alpha = max(alpha, valor)
            if alpha >= beta:
                break
        return valor, mejor_mov
    else:
        # Nodo de "entorno": aquí simulamos que el oponente no juega activamente,
        # pero podemos añadir basura o simplemente devolver la evaluación.
        # Para simplificar, consideramos que el entorno no cambia el estado (pasivo).
        return evaluar(board), None

def elegir_movimiento_clasico(board, tiempo_limite=0.5):
    """
    Elige el mejor movimiento usando Minimax con profundidad iterativa.
    """
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
        if profundidad > 4:  # límite para evitar lentitud
            break
    if mejor_accion is None:
        # Si no se encontró ningún movimiento válido, elegir aleatorio entre los posibles
        posibles = [x for x in range(ANCHO_TABLERO-1) if board.copiar().intercambiar(x)]
        if posibles:
            mejor_accion = random.choice(posibles)
        else:
            mejor_accion = 0
    return mejor_accion