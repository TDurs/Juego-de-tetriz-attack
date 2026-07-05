# puntuaciones.py
import os
import json

ARCHIVO_RANKING = "ranking.json"
MAX_REGISTROS = 10

def cargar_ranking():
    """Devuelve lista de dicts [{'nombre': 'AAA', 'puntaje': 999}, ...] ordenada descendente."""
    if not os.path.exists(ARCHIVO_RANKING):
        return []
    try:
        with open(ARCHIVO_RANKING, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            if isinstance(datos, list):
                return sorted(datos, key=lambda x: x['puntaje'], reverse=True)[:MAX_REGISTROS]
    except (json.JSONDecodeError, KeyError):
        return []
    return []

def guardar_puntaje(nombre, puntaje):
    """Añade un puntaje y mantiene los 10 mejores."""
    ranking = cargar_ranking()
    ranking.append({'nombre': nombre.upper()[:3].ljust(3, '?'), 'puntaje': puntaje})
    ranking = sorted(ranking, key=lambda x: x['puntaje'], reverse=True)[:MAX_REGISTROS]
    with open(ARCHIVO_RANKING, 'w', encoding='utf-8') as f:
        json.dump(ranking, f, indent=2)