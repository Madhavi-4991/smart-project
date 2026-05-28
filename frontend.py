import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="EcoWatt India", page_icon="⚡", layout="wide")
BACKEND_URL = "http://127.0.0.1:8000"

# ---------------- CSS ----------------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#1f4037,#99f2c8); color:#111; }
.card { background: white; padding:15px; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.1); text-align:center; height: 100%;}
.card img { height:180px; object-fit:cover; border-radius:10px; width:100%; }
h1,h2,h3 {color:#0b3d2e;}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "login" not in st.session_state:
    st.session_state.login = False
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Date", "Usage"])

# ---------------- AUTH UI ----------------
def login_page():
    st.title("⚡ Smart Electricity Consumption Analysis")
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username", key="l1")
        p = st.text_input("Password", type="password", key="l2")
        if st.button("Login"):
            res = requests.post(f"{BACKEND_URL}/login", json={"username": u, "password": p})
            if res.status_code == 200:
                st.session_state.login = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        u = st.text_input("New Username", key="s1")
        p = st.text_input("New Password", type="password", key="s2")
        if st.button("Create"):
            res = requests.post(f"{BACKEND_URL}/signup", json={"username": u, "password": p})
            if res.status_code == 200:
                st.success("Account created! Please switch to the login tab.")
            else:
                st.error(res.json().get("detail", "Error creating user"))

# ---------------- PAGES ----------------
def dashboard():
    st.title("⚡ EcoWatt Dashboard")
    col1, col2, col3 = st.columns(3)
    
    cards = [
        ("https://images.unsplash.com/photo-1559305616-3f99cd43e353", "Track Usage", "Monitor daily electricity consumption"),
        ("https://images.unsplash.com/photo-1581092918056-0c4c3acd3789", "Analyze Trends", "Visualize patterns with charts"),
        ("https://images.unsplash.com/photo-1509395176047-4a66953fd231", "AI Prediction", "Forecast future consumption")
    ]
    
    for col, (img, title, desc) in zip([col1, col2, col3], cards):
        col.markdown(f'<div class="card"><img src="{img}"><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

def input_page():
    st.header("📥 Data Management")
    
    st.subheader("Option 1: Add Manually")
    d = st.date_input("Date", datetime.today())
    u = st.number_input("Units (kWh)", min_value=0.0, step=0.1)
    if st.button("Add Record"):
        new_row = pd.DataFrame([[d.strftime('%Y-%m-%d'), u]], columns=["Date", "Usage"])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True).drop_duplicates(subset=['Date'])
        st.success("Added row!")

    st.write("---")
    st.subheader("Option 2: Bulk CSV Upload")
    uploaded_file = st.file_uploader("Upload CSV containing 'Date' and 'Usage' columns", type=["csv"])
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            if "Date" in uploaded_df.columns and "Usage" in uploaded_df.columns:
                uploaded_df["Date"] = pd.to_datetime(uploaded_df["Date"]).dt.strftime('%Y-%m-%d')
                st.session_state.df = pd.concat([st.session_state.df, uploaded_df], ignore_index=True).drop_duplicates(subset=['Date'])
                st.success("CSV Imported Successfully!")
            else:
                st.error("CSV must contain exactly 'Date' and 'Usage' columns.")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    st.write("### Current Data View")
    st.dataframe(st.session_state.df, use_container_width=True)

def analysis_page():
    st.header("📊 Analysis Insights")
    if st.session_state.df.empty:
        st.warning("No data found. Please add or upload data in the Input tab.")
        return

    payload = {"data": st.session_state.df.to_dict(orient="records")}
    res = requests.post(f"{BACKEND_URL}/analyze", json=payload)
    
    if res.status_code == 200:
        metrics = res.json()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Usage", f"{metrics['total_usage']:.2f} kWh")
        m2.metric("Total Cost", f"₹{metrics['cost']:.2f}")
        m3.metric("Carbon Footprint", f"{metrics['co2']:.2f} kg CO₂")
        
        st.info(f"⚡ **Peak Consumption Alert:** Maximum usage of **{metrics['peak_usage']} kWh** recorded on **{metrics['peak_date']}**")
        
        fig = px.line(st.session_state.df.sort_values(by="Date"), x="Date", y="Usage", title="Consumption Trend Curve", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Error retrieving analysis calculation from backend.")

def prediction_page():
    st.header("🔮 AI Analytics & Forecasting")
    if len(st.session_state.df) < 2:
        st.warning("Insufficient history. Need at least 2 unique record days to run calculations.")
        return

    payload = {"data": st.session_state.df.to_dict(orient="records")}
    res = requests.post(f"{BACKEND_URL}/predict", json=payload)
    
    if res.status_code == 200:
        pred_data = res.json()
        
        df_hist = st.session_state.df.copy().sort_values(by="Date")
        df_pred = pd.DataFrame({"Date": pred_data["future_dates"], "Usage": pred_data["predictions"]})
        
        fig = px.line(title="7-Day Forward Consumption Horizon Forecast Model")
        fig.add_scatter(x=df_hist["Date"], y=df_hist["Usage"], name="Historical Records")
        fig.add_scatter(x=df_pred["Date"], y=df_pred["Usage"], name="AI Projection Forecast", line=dict(dash='dash', color='orange'))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Machine learning calculations threw an error on the engine module.")

def suggestions_page():
    st.header("💡 Dynamic Energy Optimization Engine")
    
    col1, col2, col3 = st.columns(3)
    tips = [
        ("https://images.unsplash.com/photo-1584277261846-c6a1672ed979", "Energy Efficient Devices", "Upgrade appliances to BEE 5-star rated equipment configurations to lower constant overhead loads."),
        ("https://images.unsplash.com/photo-1521207418485-99c705420785", "Off-Peak Operations", "De-fer heavy cycle processes (washing machines, water heaters) into localized grid off-peak blocks."),
        ("https://images.unsplash.com/photo-1592833159155-c62df1b65634", "Solar System Alternatives", "Deploy onsite rooftop photovoltaic solar strings to achieve structural dependency reductions.")
    ]
    for col, (img, title, desc) in zip([col1, col2, col3], tips):
        col.markdown(f'<div class="card"><img src="{img}"><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

def report_page():
    st.header("📄 Consolidated Data Exporter")
    if st.session_state.df.empty:
        st.warning("No dynamic payload array available to compile output files.")
        return
        
    csv_out = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download Usage Report (CSV)", data=csv_out, file_name="ecowatt_usage_export.csv", mime="text/csv")

# ---------------- CONTROL FLOW ----------------
if not st.session_state.login:
    login_page()
else:
    page = st.sidebar.radio("Menu Navigation", ["Dashboard", "Input Management", "Analysis Insights", "Forecasting Engine", "Smart Suggestions", "Reports Export"])
    
    if page == "Dashboard": dashboard()
    elif page == "Input Management": input_page()
    elif page == "Analysis Insights": analysis_page()
    elif page == "Forecasting Engine": prediction_page()
    elif page == "Smart Suggestions": suggestions_page()
    elif page == "Reports Export": report_page()

    if st.sidebar.button("Secure Logout"):
        st.session_state.login = False
        st.rerun()
