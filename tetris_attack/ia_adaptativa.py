# ia_adaptativa.py
import numpy as np
import pickle
import os
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from config import ARCHIVO_MODELO, ANCHO_TABLERO, ARCHIVO_DATOS

MAX_EJEMPLOS = 5000

def cargar_modelo():
    if not os.path.exists(ARCHIVO_MODELO):
        print("⚠️ Modelo adaptativo no encontrado. La IA usará movimientos aleatorios.")
        return None
    try:
        with open(ARCHIVO_MODELO, 'rb') as f:
            modelo = pickle.load(f)
        print("✅ Modelo adaptativo cargado correctamente.")
        return modelo
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}. Se usarán movimientos aleatorios.")
        return None

def predecir_movimiento(board, modelo):
    if modelo is None:
        return None
    X = board.estado_a_vector().reshape(1, -1)
    pred = modelo.predict(X)[0]
    # Verificar si el movimiento predicho es legal (sin modificar el tablero)
    if board.puede_intercambiar(pred):
        return pred
    # Si no, devolver None para que el llamador use fallback
    return None

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