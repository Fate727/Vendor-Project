import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split


# ==========================================================
# Load Dataset
# ==========================================================

DATASET_PATH = "data/ml_product_sales_dataset.csv"

df = pd.read_csv(DATASET_PATH)


print("=" * 50)
print("Dataset Loaded Successfully")
print("=" * 50)

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print()


# ==========================================================
# Convert Date Features
# ==========================================================

df["Date"] = pd.to_datetime(df["Date"])


df["Year"] = df["Date"].dt.year

df["Day"] = df["Date"].dt.day

# Remove original Date

df.drop(
    columns=["Date"],
    inplace=True
)


# ==========================================================
# Remove Text Columns
# ==========================================================

# Random Forest cannot understand text directly

df.drop(
    columns=[
        "CategoryName"
    ],
    inplace=True
)


# ==========================================================
# Missing Values
# ==========================================================

print("Missing Values:")
print(df.isnull().sum())
print()


# ==========================================================
# Features and Target
# ==========================================================

TARGET_COLUMN = "TargetNext7Days"

X = df.drop(
    columns=[
        TARGET_COLUMN
    ]
)

y = df[TARGET_COLUMN]


print("Feature Columns:")
print(list(X.columns))
print()

# ==========================================================
# Train/Test Split
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print(f"Training Samples : {len(X_train)}")
print(f"Testing Samples  : {len(X_test)}")
print()

# ==========================================================
# Train Random Forest
# ==========================================================

print("Training Random Forest...")

model = RandomForestRegressor(

    n_estimators=200,

    random_state=42,

    n_jobs=-1
)


model.fit(
    X_train,
    y_train
)

print("Training Complete!")
print()


# ==========================================================
# Prediction
# ==========================================================

predictions = model.predict(
    X_test
)

# ==========================================================
# Evaluation
# ==========================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

mse = mean_squared_error(
    y_test,
    predictions
)

rmse = mse ** 0.5

r2 = r2_score(
    y_test,
    predictions
)

print("=" * 50)
print("MODEL EVALUATION")
print("=" * 50)

print(
    f"Mean Absolute Error : {mae:.2f}"
)

print(
    f"Mean Squared Error  : {mse:.2f}"
)

print(
    f"Root Mean Squared Error : {rmse:.2f}"
)

print(
    f"R² Score            : {r2:.4f}"
)

print()


# ==========================================================
# Feature Importance
# ==========================================================

importance = pd.DataFrame({

    "Feature":
        X.columns,

    "Importance":
        model.feature_importances_

})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)


print("=" * 50)
print("FEATURE IMPORTANCE")
print("=" * 50)

print(
    importance
)

print()

# ==========================================================
# Save Model
# ==========================================================

os.makedirs(
    "ml/models",
    exist_ok=True
)

MODEL_PATH = (
    "ml/models/random_forest_stock.pkl"
)


joblib.dump(
    model,
    MODEL_PATH
)

print("=" * 50)
print("Model Saved Successfully")
print(MODEL_PATH)
print("=" * 50)