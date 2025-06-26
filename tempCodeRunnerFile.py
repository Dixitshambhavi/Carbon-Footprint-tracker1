from fastapi import FastAPI
import pandas as pd

app = FastAPI()
df = pd.read_excel(r"C:\Users\asus\Downloads\carbon_footprint_tracker_multiuser_20users.xlsx")

@app.get("/user/{user_id}/summary")
def user_summary(user_id: str):
    user_data = df[df["UserID"] == user_id]
    total_emission = float(user_data["CO2e (kg)"].sum())
    by_category = user_data.groupby("Category")["CO2e (kg)"].sum().to_dict()
    return {"user": user_id, "total_emission": total_emission, "by_category": by_category}
