import polars as pl
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import joblib
import lightgbm as lgb
from collections import Counter

def evaluar_modelo(model, X_test_data, y_test_data, model_name="Modelo de Clasificación"):
    print(f"\n--- Evaluación del Modelo: {model_name} ---")
    y_pred = model.predict(X_test_data)
    accuracy = accuracy_score(y_test_data, y_pred)
    print(f"Precisión (Accuracy) en el conjunto de prueba: {accuracy:.4f}")
    print("\nReporte de Clasificación:")
    print(classification_report(y_test_data, y_pred, zero_division=0))


def train(id: str, df_cleaned, eval=False):
    # Para quitar observaciones muy poco frecuentes que causaban problemas en el entrenamiento
    df_cleaned = df_cleaned.with_columns(pl.col(id).count().over(id).alias("conteo"))
    df_cleaned = df_cleaned.filter(pl.col("conteo") >= 2)
    df_cleaned = df_cleaned.drop("conteo")

    X = df_cleaned.select(["year", "month", "day", "weekday", "is_business_day", "hour"])
    y = df_cleaned.select(id)

    X_train, X_test, y_train, y_test = train_test_split(
        X.to_numpy(),
        y.to_numpy().flatten(),
        test_size=0.2,
        random_state=42,
        stratify=y.to_numpy().flatten()
    )

    # Contar la frecuencia de cada clase en el conjunto de entrenamiento
    class_counts = Counter(y_train)
    total_samples = len(y_train)
    
    # Aquí usaremos el inverso de la proporción para dar más peso a las clases minoritarias.
    class_weights = {}
    for class_label, count in class_counts.items():
        if count > 0:
            class_weights[class_label] = total_samples / (len(class_counts) * count)
        else:
            class_weights[class_label] = 0

    model = lgb.LGBMClassifier(
        random_state=27,
        objective='multiclass',
        num_class=len(np.unique(y_train)),
        n_estimators=100,
        learning_rate=0.01,
        max_depth=-1,
        verbose=-1,
        class_weight=class_weights
    )
    model.fit(X_train, y_train)

    if eval:
        evaluar_modelo(model, X_test, y_test, model_name="LightGBM con Pesos de Clase")

    return model

def save_model(filename, model):
    joblib.dump(model, filename)

df_cleaned = pl.read_csv("data/data_concat.csv")

df_train = df_cleaned.with_columns(
    pl.col("timestamp").str.to_datetime().dt.year().alias("year"),
    pl.col("timestamp").str.to_datetime().dt.month().alias("month"),
    pl.col("timestamp").str.to_datetime().dt.day().alias("day"),
    pl.col("timestamp").str.to_datetime().dt.weekday().alias("weekday"),
    pl.col("timestamp").str.to_datetime().dt.hour().alias("hour"),
    pl.col("timestamp").str.to_datetime().dt.is_business_day().alias("is_business_day"),
    pl.col("timestamp").str.to_datetime().dt.week().alias("week"),
)
df_train = df_train.drop("timestamp")

df_train_cleaned = df_train.drop_nulls()

cont = 0

feature_cols = ["year", "month", "day", "weekday", "is_business_day", "hour", "week"]
target_cols = [col for col in df_train_cleaned.columns if col not in feature_cols]

for col in target_cols:
    id_carretera = col
    model = train(id_carretera, df_train_cleaned, eval=False)
    save_model(f"models/model_{id_carretera}.joblib", model)
    cont += 1
    print(f"{cont}/{len(target_cols)}")