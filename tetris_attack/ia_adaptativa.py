# ia_adaptativa.py
import numpy as np
import pickle
import os
import pandas as pd
import time
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from config import ARCHIVO_MODELO, ANCHO_TABLERO, ARCHIVO_DATOS, FILAS_TOTALES
from evaluacion import evaluar

MAX_EJEMPLOS = 5000

def cargar_modelo():
    if not os.path.exists(ARCHIVO_MODELO):
        print("⚠️ Modelo adaptativo no encontrado.")
        return None
    try:
        with open(ARCHIVO_MODELO, 'rb') as f:
            modelo = pickle.load(f)
        print("✅ Modelo adaptativo cargado correctamente.")
        return modelo
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}.")
        return None

def predecir_movimiento(board, modelo):
    """Predice la columna según el modelo. Retorna None si no es válida."""
    if modelo is None:
        return None
    X = board.estado_a_vector().reshape(1, -1)
    pred = modelo.predict(X)[0]
    if board.puede_intercambiar(pred):
        return pred
    return None

def _mejor_fila_para_columna(board, x):
    """
    Para una columna x, prueba todas las filas donde el intercambio sea legal
    y retorna (fila, valor_heurístico) de la mejor opción.
    """
    mejor_valor = -float('inf')
    mejor_fila = None
    copia_base = board.copiar()
    for y in range(FILAS_TOTALES):
        if copia_base._posicion_es_valida(y, x):
            copia = copia_base.copiar()
            if copia.intercambiar_en(x, y):
                copia.resolver_matches()
                valor = evaluar(copia)
                if valor > mejor_valor:
                    mejor_valor = valor
                    mejor_fila = y
    return mejor_fila, mejor_valor

def elegir_movimiento_adaptativo(board, modelo):
    print(f"DEBUG: modelo es None? {modelo is None}")
    """
    Retorna una tupla (columna, fila) con la mejor jugada,
    combinando el modelo supervisado y búsqueda heurística.
    """
    # --- Intento con el modelo supervisado ---
    if modelo is not None:
        columna = predecir_movimiento(board, modelo)
        if columna is not None:
            fila, valor = _mejor_fila_para_columna(board, columna)
            if fila is not None:
                valor_actual = evaluar(board)
                if valor > valor_actual * 0.8:
                    print(f"🤖 Movimiento según modelo: columna {columna}, fila {fila} (valor {valor})")
                    return (columna, fila)
                else:
                    print(f"⚠️ Movimiento del modelo ({columna}) es malo (valor {valor}). Buscando alternativa...")
            else:
                print(f"⚠️ No hay fila válida para columna {columna}.")

    # --- Búsqueda heurística completa (explora columna x fila) ---
    print("🔍 Realizando búsqueda heurística...")
    return _busqueda_rapida(board)

def _busqueda_rapida(board):
    """Prueba todas las combinaciones (columna, fila) y elige la mejor."""
    mejor_x = None
    mejor_y = None
    mejor_valor = -float('inf')
    inicio = time.time()

    for x in range(ANCHO_TABLERO - 1):
        for y in range(FILAS_TOTALES):
            copia = board.copiar()
            if copia.intercambiar_en(x, y):
                copia.resolver_matches()
                valor = evaluar(copia)
                if valor > mejor_valor:
                    mejor_valor = valor
                    mejor_x = x
                    mejor_y = y
        # Limitar tiempo total a 0.3 s
        if time.time() - inicio > 0.3:
            break

    if mejor_x is not None:
        print(f"🎯 Mejor movimiento heurístico: columna {mejor_x}, fila {mejor_y} (valor {mejor_valor})")
        return (mejor_x, mejor_y)
    else:
        print("❌ No se encontró ningún movimiento legal.")
        return (None, None)

def entrenar_modelo():
    if not os.path.exists(ARCHIVO_DATOS):
        print(f"No se encontró {ARCHIVO_DATOS}. No se puede entrenar.")
        return
    datos = pd.read_csv(ARCHIVO_DATOS)
    if len(datos) == 0:
        print("El archivo CSV está vacío. No se puede entrenar.")
        return
    X = datos.iloc[:, :-1].values
    y = datos.iloc[:, -1].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = DecisionTreeClassifier(max_depth=10)
    modelo.fit(X_train, y_train)
    precision = modelo.score(X_test, y_test)
    print(f"Precisión en test: {precision:.2f}")
    with open(ARCHIVO_MODELO, 'wb') as f:
        pickle.dump(modelo, f)
    print(f"Modelo guardado en {ARCHIVO_MODELO}")

def actualizar_modelo():
    if not os.path.exists(ARCHIVO_DATOS):
        return
    datos = pd.read_csv(ARCHIVO_DATOS)
    if len(datos) == 0:
        return
    if len(datos) > MAX_EJEMPLOS:
        datos = datos.tail(MAX_EJEMPLOS)
        datos.to_csv(ARCHIVO_DATOS, index=False)
    X = datos.iloc[:, :-1].values
    y = datos.iloc[:, -1].values
    modelo = DecisionTreeClassifier(max_depth=10)
    modelo.fit(X, y)
    with open(ARCHIVO_MODELO, 'wb') as f:
        pickle.dump(modelo, f)

if __name__ == "__main__":
    entrenar_modelo()