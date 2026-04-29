import json
import os
import sys
from pathlib import Path

import joblib
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline

sys.path.append(os.path.dirname(__file__))
from preprocessor import load_and_preprocess  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODELS_DIR / "yield_model.pkl"
METRICS_PATH = MODELS_DIR / "model_metrics.json"
FEATURE_PATH = MODELS_DIR / "feature_importance.json"

print("📥 Loading and preprocessing dataset...")
data = load_and_preprocess("data/crop_data.csv")
if "Yield" not in data.columns:
    raise ValueError("Dataset must contain a 'Yield' column for training.")

X = data.drop("Yield", axis=1)
y = data["Yield"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline = Pipeline([("model", RandomForestRegressor(random_state=42))])

param_grid = [
    {
        "model": [RandomForestRegressor(random_state=42)],
        "model__n_estimators": [200, 400],
        "model__max_depth": [None, 20, 30],
        "model__min_samples_leaf": [1, 3],
    },
    {
        "model": [HistGradientBoostingRegressor(random_state=42)],
        "model__learning_rate": [0.05, 0.1],
        "model__max_depth": [None, 10],
        "model__max_leaf_nodes": [31, 63],
    },
]

print("🔍 Running GridSearchCV (this might take a moment)...")
search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    n_jobs=-1,
    scoring="neg_mean_absolute_error",
    verbose=2,
)
search.fit(X_train, y_train)

best_model = search.best_estimator_
core_model = best_model.named_steps["model"]

print(f"✅ Best model: {core_model.__class__.__name__}")
print(f"🏆 Best params: {search.best_params_}")

joblib.dump(best_model, MODEL_PATH)

y_pred = best_model.predict(X_test)
metrics = {
    "r2_score": round(r2_score(y_test, y_pred), 4),
    "mae": round(mean_absolute_error(y_test, y_pred), 4),
    "rmse": round(mean_squared_error(y_test, y_pred, squared=False), 4),
    "n_samples": len(data),
    "best_model": core_model.__class__.__name__,
    "best_params": search.best_params_,
}
METRICS_PATH.write_text(json.dumps(metrics, indent=2))

if hasattr(core_model, "feature_importances_"):
    importances = core_model.feature_importances_
else:
    print("ℹ️ Computing permutation importances...")
    perm = permutation_importance(
        best_model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1
    )
    importances = perm.importances_mean

feature_importance = {
    feature: round(float(importance), 6)
    for feature, importance in sorted(
        zip(X.columns, importances), key=lambda item: item[1], reverse=True
    )
}
FEATURE_PATH.write_text(json.dumps(feature_importance, indent=2))

print("💾 Model, metrics, and feature importance saved to 'models/' directory.")
print(f"R²: {metrics['r2_score']} | MAE: {metrics['mae']} | RMSE: {metrics['rmse']}")

