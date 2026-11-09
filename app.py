import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="News Click & Engagement Analytics", page_icon="📰", layout="wide")

st.title("News Click & Engagement Analytics")
st.write(
    "An interactive dashboard to explore how users engage with news articles "
    "across categories, devices and demographic groups."
)

@st.cache_data
def load_data():
    path = Path(__file__).parent / "News_Clicks_dataset_V1.csv"
    data = pd.read_csv(path)
    data["publish_time"] = pd.to_datetime(data["publish_time"], errors="coerce")
    data["click"] = pd.to_numeric(data["click"], errors="coerce").fillna(0).astype(int)
    data["age"] = pd.to_numeric(data["age"], errors="coerce")
    return data

df = load_data()

# Sidebar filters
st.sidebar.header("Explore the dataset")
min_date = df["publish_time"].min().date()
max_date = df["publish_time"].max().date()
date_range = st.sidebar.date_input(
    "Publication date range", value=(min_date, max_date),
    min_value=min_date, max_value=max_date
)
categories = sorted(df["category"].dropna().unique())
chosen_categories = st.sidebar.multiselect("News category", categories, default=categories)
devices = sorted(df["device"].dropna().unique())
chosen_devices = st.sidebar.multiselect("Device", devices, default=devices)
genders = sorted(df["gender"].dropna().unique())
chosen_genders = st.sidebar.multiselect("Gender", genders, default=genders)
age_min, age_max = int(df["age"].min()), int(df["age"].max())
age_range = st.sidebar.slider("User age", age_min, age_max, (age_min, age_max))

# Apply filters
data = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    data = data[
        data["publish_time"].dt.date.between(date_range[0], date_range[1])
    ]
data = data[
    data["category"].isin(chosen_categories)
    & data["device"].isin(chosen_devices)
    & data["gender"].isin(chosen_genders)
    & data["age"].between(age_range[0], age_range[1])
]

# KPIs
st.subheader("Key Performance Indicators")
impressions = len(data)
clicks = int(data["click"].sum())
ctr = (clicks / impressions * 100) if impressions else 0
unique_users = data["user_id"].nunique()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Impressions", f"{impressions:,}")
k2.metric("Total Clicks", f"{clicks:,}")
k3.metric("Click-through Rate", f"{ctr:.2f}%")
k4.metric("Unique Users", f"{unique_users:,}")
st.caption("All KPI values, tables and charts respond to the filters in the sidebar.")

overview, analysis, charts, insights = st.tabs(
    ["Dataset Overview", "Data Analysis", "Visualizations", "Insights"]
)

with overview:
    st.subheader("Filtered News Records")
    st.write(f"Currently displaying **{len(data):,}** records.")
    st.dataframe(data, use_container_width=True)
    with st.expander("Dataset information and column meanings"):
        st.write(
            "The dataset contains user and news identifiers, news category and "
            "subcategory, title, abstract, publication timestamp, user age, gender, "
            "location, device and click outcome."
        )
        st.write("A click value of 1 means the article was clicked; 0 means it was not clicked.")
        st.write("Click-through rate (CTR) = (Total clicks / Total impressions) × 100.")

with analysis:
    st.subheader("Engagement summaries")
    if data.empty:
        st.warning("No records match these filters. Change the sidebar selections.")
    else:
        category_summary = data.groupby("category").agg(
            impressions=("click", "size"),
            clicks=("click", "sum"),
            click_rate=("click", "mean")
        ).reset_index()
        category_summary["click_rate"] *= 100
        category_summary = category_summary.sort_values("click_rate", ascending=False)
        st.write("**Category-wise engagement**")
        st.dataframe(category_summary.round(2), use_container_width=True)

        device_summary = data.groupby("device").agg(
            impressions=("click", "size"),
            clicks=("click", "sum"),
            click_rate=("click", "mean")
        ).reset_index()
        device_summary["click_rate"] *= 100
        st.write("**Device-wise engagement**")
        st.dataframe(device_summary.round(2), use_container_width=True)

        left, right = st.columns(2)
        with left:
            st.write("**Number of records by category**")
            counts = data.groupby("category").size().reset_index(name="records")
            st.bar_chart(counts, x="category", y="records")
        with right:
            st.write("**Clicks by device**")
            by_device = data.groupby("device")["click"].sum().reset_index(name="clicks")
            st.bar_chart(by_device, x="device", y="clicks")

with charts:
    st.subheader("Explore engagement patterns")
    if data.empty:
        st.warning("No records match these filters. Change the sidebar selections.")
    else:
        st.write("**1. Bar Chart – Clicks by News Category**")
        category_clicks = data.groupby("category")["click"].sum().reset_index(name="clicks")
        st.bar_chart(category_clicks, x="category", y="clicks")
        st.caption("This chart compares the total number of clicks received by each news category.")

        st.write("**2. Line Chart – Daily News Click Trend**")
        daily = data.set_index("publish_time").resample("D")["click"].sum().reset_index()
        st.line_chart(daily, x="publish_time", y="click")
        st.caption("This chart shows how the number of clicks changes over publication dates.")

        st.write("**3. Scatter Plot – Age vs Click-through Rate**")
        age_engagement = data.groupby("age").agg(
            clicks=("click", "sum"), impressions=("click", "size")
        ).reset_index()
        age_engagement["click_rate"] = age_engagement["clicks"] / age_engagement["impressions"] * 100
        st.scatter_chart(age_engagement, x="age", y="click_rate")
        st.caption(
            "Each point represents an age group. It compares user age with the percentage "
            "of records clicked for that age. Groups with fewer records should be interpreted cautiously."
        )

with insights:
    st.subheader("Key observations from the selected records")
    if data.empty:
        st.info("Change the filters to generate insights.")
    else:
        cat_clicks = data.groupby("category")["click"].sum()
        device_clicks = data.groupby("device")["click"].sum()
        top_category = cat_clicks.idxmax() if len(cat_clicks) else "N/A"
        top_device = device_clicks.idxmax() if len(device_clicks) else "N/A"
        avg_age = data["age"].mean()
        st.write(f"- **Category with the most clicks:** {top_category}.")
        st.write(f"- **Device with the most clicks:** {top_device}.")
        st.write(f"- **Average age of users in the filtered records:** {avg_age:.1f} years.")
        st.write(f"- **Click-through rate for the filtered records:** {ctr:.2f}%.")
        st.caption("These insights describe the currently filtered dataset, not causal relationships.")

st.divider()