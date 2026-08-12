import joblib
import pandas as pd

# Load trained model
MODEL_PATH = "ml/models/random_forest_stock.pkl"
model = joblib.load(MODEL_PATH)

# Features expected by the trained model
FEATURE_COLUMNS = list(model.feature_names_in_)

print("Model expects:", FEATURE_COLUMNS)


def predict_stock(features):
    """
    Predict next 7 days sales.
    """

    # Create dataframe from incoming features
    df = pd.DataFrame([features])

    # Add any missing columns with default value 0
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0

    # Remove any extra columns and reorder to match training
    df = df[FEATURE_COLUMNS]

    # print("Prediction DataFrame:")
    # print(df)

    prediction = model.predict(df)[0]

    return max(0, round(float(prediction)))


if __name__ == "__main__":

    sample = {
    "ProductID": 3212,
    "SellerID": 12,
    "TotalSales": 50,
    "SalesLast7Days": 10,
    "SalesPrevious7Days": 5,
    "SalesLast30Days": 35,
    "SalesGrowthRate": 1.0,
    "Revenue": 45000,
    "AvgDailySales": 1.6,
    "Price": 1200,
    "CategoryID": 3,
    "CurrentStock": 20,
    "ProductAgeDays": 200,
    "DaysSinceLastSale": 2,
    "Year": 2026,
    "Month": 7,
    "Week": 27,
    "Day": 7,
    "DayOfWeek": 1,
    }

    prediction = predict_stock(sample)

    print(f"Predicted Sales (Next 7 Days): {prediction}")