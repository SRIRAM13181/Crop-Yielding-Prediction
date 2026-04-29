"""
User Authentication & Session Management
Handles user login, registration, and prediction history tracking.
"""

import streamlit as st
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import hashlib


class UserDatabase:
    """SQLite database for user management and prediction history."""
    
    def __init__(self, db_path: str = "models/users.db"):
        """Initialize database connection."""
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()
    
    def _initialize_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    crop TEXT NOT NULL,
                    state TEXT NOT NULL,
                    rainfall REAL,
                    temperature REAL,
                    humidity REAL,
                    nitrogen REAL,
                    phosphorus REAL,
                    potassium REAL,
                    pH REAL,
                    soil_type TEXT,
                    predicted_yield REAL,
                    total_acres REAL,
                    market_price REAL,
                    cost_per_acre REAL,
                    total_profit REAL,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
    
    def register_user(self, username: str, email: str, password: str) -> bool:
        """
        Register new user.
        
        Args:
            username: Username
            email: Email address
            password: Password (will be hashed)
        
        Returns:
            True if successful, False if user exists
        """
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verify_user(self, username: str, password: str) -> bool:
        """
        Verify user credentials.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            True if credentials valid
        """
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            result = cursor.fetchone()
        
        return result is not None
    
    def get_user_id(self, username: str) -> Optional[int]:
        """Get user ID by username."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
        
        return result[0] if result else None
    
    def save_prediction(
        self,
        user_id: int,
        crop: str,
        state: str,
        rainfall: float,
        temperature: float,
        humidity: float,
        nitrogen: float,
        phosphorus: float,
        potassium: float,
        pH: float,
        soil_type: str,
        predicted_yield: float,
        total_acres: float,
        market_price: float,
        cost_per_acre: float,
        total_profit: float,
        notes: str = ""
    ) -> int:
        """
        Save prediction to database.
        
        Returns:
            Prediction ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO predictions (
                    user_id, crop, state, rainfall, temperature, humidity,
                    nitrogen, phosphorus, potassium, pH, soil_type,
                    predicted_yield, total_acres, market_price, cost_per_acre,
                    total_profit, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, crop, state, rainfall, temperature, humidity,
                nitrogen, phosphorus, potassium, pH, soil_type,
                predicted_yield, total_acres, market_price, cost_per_acre,
                total_profit, notes
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_predictions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get user's prediction history.
        
        Args:
            user_id: User ID
            limit: Max number of predictions to retrieve
        
        Returns:
            List of prediction dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM predictions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            results = cursor.fetchall()
        
        return [dict(row) for row in results]
    
    def get_prediction_by_id(self, prediction_id: int) -> Optional[Dict]:
        """Get specific prediction."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
            result = cursor.fetchone()
        
        return dict(result) if result else None
    
    def delete_prediction(self, prediction_id: int) -> bool:
        """Delete prediction."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM predictions WHERE id = ?", (prediction_id,))
            conn.commit()
        
        return cursor.rowcount > 0
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM predictions WHERE user_id = ?",
                (user_id,)
            )
            total_predictions = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT AVG(predicted_yield) FROM predictions WHERE user_id = ?",
                (user_id,)
            )
            avg_yield = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT SUM(total_profit) FROM predictions WHERE user_id = ?",
                (user_id,)
            )
            total_profit = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT AVG(total_profit) FROM predictions WHERE user_id = ?",
                (user_id,)
            )
            avg_profit = cursor.fetchone()[0]
        
        return {
            "total_predictions": total_predictions,
            "avg_yield": avg_yield or 0,
            "total_profit": total_profit or 0,
            "avg_profit": avg_profit or 0
        }


def initialize_auth():
    """Initialize authentication in Streamlit session."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.db = UserDatabase()


def show_login_page() -> bool:
    """
    Display login/register page.
    
    Returns:
        True if user authenticated
    """
    st.markdown('<h1 style="text-align: center;">🌾 Crop Yield Predictor</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Login to your account</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if st.session_state.db.verify_user(username, password):
                    user_id = st.session_state.db.get_user_id(username)
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_id = user_id
                    st.success(f"Welcome back, {username}! 🌾")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        
        with tab2:
            st.subheader("Create Account")
            new_username = st.text_input("Create username", key="reg_username")
            new_email = st.text_input("Email address", key="reg_email")
            new_password = st.text_input("Create password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm password", type="password", key="reg_confirm")
            
            if st.button("Register", use_container_width=True):
                if not new_username or not new_email or not new_password:
                    st.error("❌ Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                elif st.session_state.db.register_user(new_username, new_email, new_password):
                    st.success("✅ Account created! Now login with your credentials")
                else:
                    st.error("❌ Username or email already exists")
    
    return False
