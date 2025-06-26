import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Carbon Tracker", layout="wide")
st.title("🌍 Carbon Footprint Tracker Dashboard")

# Sidebar user selection
user_id = st.sidebar.selectbox("Select User", [f"User{str(i).zfill(3)}" for i in range(1, 21)])

# --- LOGIN SECTION ---
st.sidebar.header("🔐 User Login")

user_ids = [f"User{str(i).zfill(3)}" for i in range(1, 21)]
credentials = {uid: "carbon" for uid in user_ids}  # Same password for demo

user_id = st.sidebar.selectbox("👤 Select User", user_ids)
password = st.sidebar.text_input("🔑 Enter Password", type="password")

if password != credentials.get(user_id):
    st.sidebar.warning("Invalid password ❌")
    st.stop()

st.sidebar.success(f"Welcome, {user_id}! ✅")

category_filter = st.sidebar.multiselect("Filter by Category", ["Transportation", "Diet", "Electricity"], default=["Transportation", "Diet", "Electricity"])

# API URLs
BASE = "http://127.0.0.1:8000"
summary_url = f"{BASE}/user/{user_id}/summary"
monthly_url = f"{BASE}/user/{user_id}/monthly"

# Load summary
res = requests.get(summary_url)
data = res.json() if res.status_code == 200 else None

# Load monthly trend
trend = requests.get(monthly_url)
monthly_data = trend.json() if trend.status_code == 200 else None

# Load full Excel data
@st.cache_data
def load_data():
    return pd.read_excel(r"C:\Users\asus\Downloads\carbon_footprint_tracker_multiuser_20users.xlsx")

full_df = load_data()
user_df = full_df[full_df["UserID"].str.strip() == user_id]
user_df["Date"] = pd.to_datetime(user_df["Date"])
user_df = user_df[user_df["Category"].isin(category_filter)]

# Metric and Pie
col1, col2 = st.columns(2)

if data:
    with col1:
        st.metric("👤 Total CO₂ Emission", round(data["total_emission"], 2), "kg")

    with col2:
        st.subheader("🥧 Category Breakdown")
        if data["by_category"]:
            pie_df = pd.DataFrame(list(data["by_category"].items()), columns=["Category", "CO2e (kg)"])
            pie_df = pie_df[pie_df["Category"].isin(category_filter)]
            fig = px.pie(pie_df, values="CO2e (kg)", names="Category", title="Category Split")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No category data.")

# Line Chart for Monthly Emissions
if monthly_data and monthly_data["monthly_emission"]:
    st.subheader("📈 Monthly Emissions Trend")
    trend_df = pd.DataFrame(list(monthly_data["monthly_emission"].items()), columns=["Month", "CO2e (kg)"])
    trend_df["Month"] = pd.to_datetime(trend_df["Month"])
    trend_df = trend_df.sort_values("Month")
    fig = px.line(trend_df, x="Month", y="CO2e (kg)", markers=True, title=f"Monthly CO₂e for {user_id}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No monthly data available.")

# Date filter + table
st.subheader("📋 Emission Activity Details")
date_range = st.date_input("Select date range", [user_df["Date"].min(), user_df["Date"].max()])
if len(date_range) == 2:
    start, end = date_range
    filtered_df = user_df[(user_df["Date"] >= pd.to_datetime(start)) & (user_df["Date"] <= pd.to_datetime(end))]
    st.dataframe(filtered_df[["Date", "Category", "CO2e (kg)"]].sort_values("Date"))

    # Download CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name=f"{user_id}_emissions.csv", mime="text/csv")

    # 📆 Top 5 Highest Emission Days
    st.subheader("📆 Top 5 Highest Emission Days")
    top_days = filtered_df.sort_values("CO2e (kg)", ascending=False).head(5)
    if not top_days.empty:
        fig = px.bar(top_days, x="Date", y="CO2e (kg)", color="Category", title="Top 5 Emission Days")
        st.plotly_chart(fig, use_container_width=True)

    # 📊 Category Trend Over Time
    st.subheader("📊 Category Emission Trend Over Time")
    cat_trend = filtered_df.groupby(["Date", "Category"])["CO2e (kg)"].sum().reset_index()
    if not cat_trend.empty:
        fig = px.area(cat_trend, x="Date", y="CO2e (kg)", color="Category", title="Daily CO₂e by Category")
        st.plotly_chart(fig, use_container_width=True)

# 🎯 Carbon Budget Gauge
if data:
    st.subheader("🎯 Carbon Budget Gauge")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=data['total_emission'],
        title={'text': "Total CO₂ Emission (kg)"},
        gauge={
            'axis': {'range': [0, 1000]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 500], 'color': "lightgreen"},
                {'range': [500, 800], 'color': "orange"},
                {'range': [800, 1000], 'color': "red"}
            ]
        }
    ))
    st.plotly_chart(gauge, use_container_width=True)
