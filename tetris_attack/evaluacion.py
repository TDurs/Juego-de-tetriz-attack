# evaluacion.py
from config import ANCHO_TABLERO

def evaluar(board):
    """
    Evalúa el tablero para la IA. Retorna un valor numérico (mayor = mejor).
    """
    copia = board.copiar()
    puntos, cadenas, _ = copia.resolver_matches()
    altura_max = max(copia.altura_columna(c) for c in range(ANCHO_TABLERO))
    agujeros = copia.contar_agujeros()
    return puntos + 20 * cadenas - 15 * altura_max - 30 * agujeros