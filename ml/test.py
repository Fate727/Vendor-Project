import joblib
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# ==========================
# Load trained model
# ==========================

MODEL_PATH = "ml/models/random_forest_stock.pkl"

model = joblib.load(MODEL_PATH)

print("Model loaded successfully")


# ==========================
# Load test dataset
# ==========================

TEST_DATA = "data/ml_product_sales_dataset.csv"

df = pd.read_csv(TEST_DATA)


# Target column
TARGET_COLUMN = "TargetNext7Days"


# Split features and target
X_test = df.drop(columns=[TARGET_COLUMN])
y_test = df[TARGET_COLUMN]


# Make sure columns match training
FEATURE_COLUMNS = list(model.feature_names_in_)

X_test = X_test[FEATURE_COLUMNS]


# ==========================
# Prediction
# ==========================

predictions = model.predict(X_test)


# ==========================
# Evaluation Metrics
# ==========================

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

print(f"Mean Absolute Error      : {mae:.2f}")
print(f"Mean Squared Error       : {mse:.2f}")
print(f"Root Mean Squared Error  : {rmse:.2f}")
print(f"R² Score                 : {r2:.4f}")

print("=" * 50)