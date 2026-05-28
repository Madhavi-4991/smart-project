from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import numpy as np
import json
import os
import hashlib
import secrets
from typing import List, Dict

app = FastAPI(title="EcoWatt Backend API")
USER_FILE = "users.json"

# --- Models ---
class UserAuth(BaseModel):
    username: str
    password: str

class DataRow(BaseModel):
    Date: str
    Usage: float

class AnalysisRequest(BaseModel):
    data: List[DataRow]

# --- Helper Functions ---
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(stored, password):
    try:
        salt, hashed = stored.split(":")
        return hashed == hashlib.sha256((password + salt).encode()).hexdigest()
    except Exception:
        return False

def load_users():
    if not os.path.exists(USER_FILE): 
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_user_to_db(u, p):
    users = load_users()
    if u in users: 
        return False
    users[u] = hash_password(p)
    with open(USER_FILE, "w") as f:
        json.dump(users, f)
    return True

# --- API Endpoints ---
@app.post("/signup")
def signup(user: UserAuth):
    if save_user_to_db(user.username, user.password):
        return {"status": "success", "message": "User created successfully"}
    raise HTTPException(status_code=400, detail="User already exists")

@app.post("/login")
def login(user: UserAuth):
    users = load_users()
    if user.username in users and verify_password(users[user.username], user.password):
        return {"status": "success", "token": f"mock-jwt-token-for-{user.username}"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/analyze")
def analyze_data(payload: AnalysisRequest, cost_per_kwh: float = 7.5, co2_per_kwh: float = 0.82):
    if not payload.data:
        raise HTTPException(status_code=400, detail="No data provided")
    
    df = pd.DataFrame([item.dict() for item in payload.data])
    df["Date"] = pd.to_datetime(df["Date"])
    
    total = float(df["Usage"].sum())
    cost = total * cost_per_kwh
    co2 = total * co2_per_kwh
    
    peak_idx = df["Usage"].idxmax()
    peak_usage = float(df.loc[peak_idx, "Usage"])
    peak_date = str(df.loc[peak_idx, "Date"].strftime('%Y-%m-%d'))
    
    return {
        "total_usage": total,
        "cost": cost,
        "co2": co2,
        "peak_usage": peak_usage,
        "peak_date": peak_date
    }

@app.post("/predict")
def predict_data(payload: AnalysisRequest):
    if len(payload.data) < 2:
        raise HTTPException(status_code=400, detail="At least 2 data points required for trend-prediction.")
        
    df = pd.DataFrame([item.dict() for item in payload.data])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(by="Date").reset_index(drop=True)
    
    df["t"] = np.arange(len(df))
    coef = np.polyfit(df["t"], df["Usage"], 1)
    
    future_t = [df["t"].max() + i for i in range(1, 8)]
    preds = [float(coef[0] * t + coef[1]) for t in future_t]
    
    last_date = df["Date"].max()
    future_dates = [(last_date + pd.Timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
    
    return {
        "future_dates": future_dates,
        "predictions": preds
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
