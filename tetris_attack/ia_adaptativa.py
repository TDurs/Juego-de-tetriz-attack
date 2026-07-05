# ia_adaptativa.py
import numpy as np
import pickle
from board import Board
from config import ARCHIVO_MODELO, ANCHO_TABLERO

def cargar_modelo():
    """Carga el modelo entrenado desde disco."""
    with open(ARCHIVO_MODELO, 'rb') as f:
        modelo = pickle.load(f)
    return modelo

def predecir_movimiento(board, modelo):
    """Dado un tablero, predice la columna donde intercambiar según el modelo ML."""
    X = board.estado_a_vector().reshape(1, -1)
    pred = modelo.predict(X)[0]
    # Asegurar que el movimiento sea legal: intentar intercambiar en esa columna
    if not board.copiar().intercambiar(pred):
        # Si falla, buscar el primer movimiento legal
        for x in range(ANCHO_TABLERO-1):
            if board.copiar().intercambiar(x):
                return x
    return pred

def entrenar_modelo():
    """
    Lee el archivo CSV de datos, entrena un árbol de decisión y guarda el modelo.
    Este script se puede ejecutar independientemente.
    """
    import pandas as pd
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import train_test_split
    from config import ARCHIVO_DATOS, ARCHIVO_MODELO

    datos = pd.read_csv(ARCHIVO_DATOS)
    X = datos.iloc[:, :-1].values
    y = datos.iloc[:, -1].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = DecisionTreeClassifier(max_depth=10)
    modelo.fit(X_train, y_train)
    print(f"Precisión en test: {modelo.score(X_test, y_test):.2f}")

    with open(ARCHIVO_MODELO, 'wb') as f:
        pickle.dump(modelo, f)
    print(f"Modelo guardado en {ARCHIVO_MODELO}")

if __name__ == "__main__":
    entrenar_modelo()