import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score

# -----------------------
# Load Data
# -----------------------
df = pd.read_csv("data/telco.csv")

# -----------------------
# Data Cleaning
# -----------------------
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df["TotalCharges"] = df["TotalCharges"].fillna(0)

# Convert target variable
df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

# -----------------------
# Feature Engineering
# -----------------------
df["CLV"] = df["MonthlyCharges"] * df["tenure"]

services = [
    "PhoneService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies"
]

df["ServiceCount"] = df[services].apply(lambda x: (x == "Yes").sum(), axis=1)

df["IsMonthToMonth"] = (df["Contract"] == "Month-to-month").astype(int)
df["IsElectronicCheck"] = (df["PaymentMethod"] == "Electronic check").astype(int)

# -----------------------
# Select Features
# -----------------------
features = [
    "tenure",
    "MonthlyCharges",
    "CLV",
    "ServiceCount",
    "IsMonthToMonth",
    "IsElectronicCheck"
]

X = df[features]
y = df["Churn"]

# -----------------------
# Train-Test Split
# -----------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------
# Train Model
# -----------------------
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# -----------------------
# Evaluate Model
# -----------------------
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("\n=== MODEL PERFORMANCE ===")
print(classification_report(y_test, y_pred))
print("ROC-AUC Score:", round(roc_auc_score(y_test, y_prob), 3))

# -----------------------
# Feature Importance
# -----------------------
coefficients = pd.DataFrame({
    "Feature": features,
    "Weight": model.coef_[0]
}).sort_values("Weight", ascending=False)

print("\n=== FEATURE IMPORTANCE ===")
print(coefficients)

# -----------------------
# Attach Predictions
# -----------------------
X_test = X_test.copy()

X_test["ChurnProbability"] = y_prob

# Financial Risk
X_test["RevenueRisk"] = X_test["ChurnProbability"] * X_test["CLV"]

# -----------------------
# Customer Segmentation (Vectorized)
# -----------------------
X_test["Segment"] = "Safe"

X_test.loc[X_test["CLV"] > 3000, "Segment"] = "Stable Premium"
X_test.loc[X_test["ChurnProbability"] > 0.5, "Segment"] = "Low Value Risk"
X_test.loc[
    (X_test["CLV"] > 3000) & (X_test["ChurnProbability"] > 0.5),
    "Segment"
] = "VIP At Risk"

# -----------------------
# Show Top Risks
# -----------------------
top_risk = X_test.sort_values("RevenueRisk", ascending=False)

print("\n=== TOP 10 HIGH RISK CUSTOMERS ===")
print(top_risk.head(10))

# -----------------------
# Save Base Output
# -----------------------
os.makedirs("outputs", exist_ok=True)
X_test.to_csv("outputs/churn_risk_predictions.csv", index=False)

# -----------------------
# Retention Campaign Simulator
# -----------------------
discount_cost = 500
churn_reduction = 0.30

# Expected savings
X_test["ExpectedRevenueSaved"] = (
    churn_reduction * X_test["ChurnProbability"] * X_test["CLV"]
)

# Select profitable targets
campaign_targets = X_test[X_test["ExpectedRevenueSaved"] > discount_cost]

total_revenue_saved = campaign_targets["ExpectedRevenueSaved"].sum()
campaign_cost = len(campaign_targets) * discount_cost
net_profit = total_revenue_saved - campaign_cost

# -----------------------
# Profit Curve (Cumulative)
# -----------------------
profit_df = X_test.sort_values(
    by="ExpectedRevenueSaved", ascending=False
).reset_index(drop=True)

profit_df["MarginalProfit"] = profit_df["ExpectedRevenueSaved"] - discount_cost
profit_df["CumulativeProfit"] = profit_df["MarginalProfit"].cumsum()
profit_df["CustomersTargeted"] = profit_df.index + 1

profit_curve = profit_df[["CustomersTargeted", "CumulativeProfit"]].copy()
profit_curve.rename(columns={"CumulativeProfit": "Profit"}, inplace=True)

profit_curve.to_csv("outputs/profit_curve.csv", index=False)

# -----------------------
# Export Dashboard Dataset
# -----------------------
final_dataset = X_test.copy()

final_dataset["CustomerID"] = df.loc[final_dataset.index, "customerID"]

final_dataset = final_dataset[[
    "CustomerID",
    "tenure",
    "MonthlyCharges",
    "CLV",
    "ChurnProbability",
    "RevenueRisk",
    "ExpectedRevenueSaved",
    "Segment"
]]

final_dataset.to_csv("outputs/churn_dashboard_dataset.csv", index=False)

# -----------------------
# Final Results
# -----------------------
print("\n=== RETENTION CAMPAIGN RESULTS ===")
print("Customers Targeted:", len(campaign_targets))
print("Total Revenue Saved:", round(total_revenue_saved, 2))
print("Campaign Cost:", campaign_cost)
print("Net Profit:", round(net_profit, 2))