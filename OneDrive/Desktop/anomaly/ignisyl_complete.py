import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler
from sklearn.neural_network import MLPRegressor
from datetime import datetime
import json
import os
import time
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Ignisyl - AI Firewall System",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    h1 { color: #FF4B4B; padding-bottom: 1rem; }
    .metric-card { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .threat-timeline {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #FF4B4B;
    }
    </style>
""", unsafe_allow_html=True)

# --- Database Setup ---
def init_database():
    """Initialize SQLite database for risk score history"""
    conn = sqlite3.connect('ignisyl_database.db')
    cursor = conn.cursor()
    
    # Create risk_scores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            user TEXT,
            pc TEXT,
            activity TEXT,
            risk_score REAL,
            risk_level TEXT,
            firewall_action TEXT,
            model_used TEXT
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            user TEXT,
            severity TEXT,
            description TEXT,
            status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_to_database(df):
    """Save risk scores to database"""
    conn = sqlite3.connect('ignisyl_database.db')
    
    for _, row in df.iterrows():
        conn.execute('''
            INSERT INTO risk_scores (timestamp, user, pc, activity, risk_score, risk_level, firewall_action, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['timestamp'],
            row['user'],
            row['pc'],
            row['activity'],
            row['risk_score'],
            row['risk_level'],
            row['firewall_action'],
            'Isolation Forest + Autoencoder'
        ))
    
    conn.commit()
    conn.close()

def get_risk_history(user=None, days=7):
    """Get risk score history from database"""
    conn = sqlite3.connect('ignisyl_database.db')
    
    if user:
        query = '''
            SELECT * FROM risk_scores 
            WHERE user = ? 
            AND timestamp >= datetime('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql_query(query, conn, params=(user, days))
    else:
        query = '''
            SELECT * FROM risk_scores 
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql_query(query, conn, params=(days,))
    
    conn.close()
    return df

# --- Autoencoder Model ---
class AutoencoderDetector:
    """
    Autoencoder for anomaly detection
    Learns to reconstruct normal patterns; high reconstruction error = anomaly
    """
    
    def __init__(self, hidden_layers=[10, 5, 10]):
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            activation='relu',
            solver='adam',
            max_iter=500,
            random_state=42
        )
        self.scaler = StandardScaler()
    
    def fit(self, X):
        """Train autoencoder on normal data"""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, X_scaled)  # Train to reconstruct input
        return self
    
    def predict_anomaly_score(self, X):
        """Calculate reconstruction error as anomaly score"""
        X_scaled = self.scaler.transform(X)
        X_reconstructed = self.model.predict(X_scaled)
        
        # Calculate reconstruction error (MSE per sample)
        reconstruction_error = np.mean((X_scaled - X_reconstructed) ** 2, axis=1)
        
        return reconstruction_error

# --- Ensemble Model (Isolation Forest + Autoencoder) ---
def train_ensemble_model(X):
    """
    Train both Isolation Forest and Autoencoder
    Combine their scores for better accuracy
    """
    
    # Model 1: Isolation Forest
    iso_forest = IsolationForest(contamination=0.01, random_state=42)
    iso_forest.fit(X)
    iso_scores = iso_forest.decision_function(X)
    
    # Model 2: Autoencoder
    autoencoder = AutoencoderDetector(hidden_layers=[10, 5, 10])
    autoencoder.fit(X)
    ae_scores = autoencoder.predict_anomaly_score(X)
    
    return iso_forest, autoencoder, iso_scores, ae_scores

def calculate_ensemble_risk_score(iso_score, ae_score, iso_scores_all, ae_scores_all):
    """
    Combine Isolation Forest and Autoencoder scores
    Using weighted average for final risk score
    """
    
    # Normalize Isolation Forest score (invert: more negative = higher risk)
    iso_normalized = (-iso_score + max(iso_scores_all)) / (max(iso_scores_all) - min(iso_scores_all))
    
    # Normalize Autoencoder score (higher error = higher risk)
    ae_normalized = (ae_score - min(ae_scores_all)) / (max(ae_scores_all) - min(ae_scores_all))
    
    # Weighted combination (70% Isolation Forest, 30% Autoencoder)
    combined_score = (0.7 * iso_normalized + 0.3 * ae_normalized) * 100
    
    return np.clip(combined_score, 0, 100)

# --- Welcome Page ---
def show_welcome_page():
    st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 80vh; background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%); border-radius: 10px;">
            <div style="font-size: 5rem; font-weight: bold; color: #00FF00; text-align: center; font-family: 'Courier New', monospace; letter-spacing: 12px; text-shadow: 0 0 20px #00FF00;">
                IGNISYL
            </div>
            <div style="color: #00FF00; font-size: 1.1rem; font-family: 'Courier New', monospace; margin-top: 15px; opacity: 0.8;">
                AI-Powered Insider Threat Detection with Adaptive Firewall Control
            </div>
            <div style="color: #00FF00; font-size: 0.9rem; font-family: 'Courier New', monospace; margin-top: 30px;">
                ⚡ Initializing Dual AI Models (Isolation Forest + Autoencoder)...
            </div>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.5)
    return True

# --- Main Application ---
def main():
    # Initialize database
    init_database()
    
    # Session state
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = False
    
    # Welcome page
    if not st.session_state.welcome_shown:
        show_welcome_page()
        st.session_state.welcome_shown = True
        st.rerun()
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔥 Ignisyl - AI Firewall System")
        st.markdown("**AI-Powered Insider Threat Detection with Adaptive Firewall Control**")
        st.caption("Sree Buddha College of Engineering | Academic Year 2025-2026")
    with col2:
        st.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
        st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        st.markdown("**Models:** IF + Autoencoder")

    st.divider()

    # Sidebar
    with st.sidebar:
        st.title("🛡️ Control Panel")
        st.divider()
        
        st.subheader("👤 Security Analyst")
        analyst_name = st.text_input("Your Name", value="Security Team")
        
        st.divider()
        
        st.subheader("📁 Data Source")
        data_source = st.radio(
            "Select Data Type:",
            ["User Activity Logs (CERT)", "Network Traffic (UNSW-NB15)", "Both"]
        )
        data_file = st.text_input("Log File Path", value="logon.csv")
        
        st.divider()
        
        st.subheader("🤖 AI Model Settings")
        contamination = st.slider("Detection Sensitivity", 0.01, 0.10, 0.01, 0.01,
                                 help="Lower = More sensitive")
        use_ensemble = st.checkbox("Use Ensemble Model (IF + AE)", value=True,
                                   help="Combine Isolation Forest and Autoencoder for better accuracy")
        
        st.divider()
        
        st.subheader("📊 View Options")
        show_timeline = st.checkbox("Show Threat Timeline", value=True)
        show_history = st.checkbox("Show Risk History", value=True)

    # Load and process data
    @st.cache_data
    def load_and_process_data(file_path, use_ensemble_model):
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            st.error(f"❌ Error: File '{file_path}' not found!")
            return None

        # Preprocessing
        df['date'] = pd.to_datetime(df['date'])
        df['hour_of_day'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_night'] = df['hour_of_day'].apply(lambda x: 1 if x < 6 or x > 22 else 0)
        
        # Encoding
        le_user = LabelEncoder()
        le_pc = LabelEncoder()
        le_activity = LabelEncoder()
        df['user_encoded'] = le_user.fit_transform(df['user'])
        df['pc_encoded'] = le_pc.fit_transform(df['pc'])
        df['activity_encoded'] = le_activity.fit_transform(df['activity'])

        # Features for models
        features_for_model = [
            'user_encoded', 'pc_encoded', 'activity_encoded', 
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_night'
        ]
        X = df[features_for_model]
        
        if use_ensemble_model:
            # Train ensemble model
            iso_forest, autoencoder, iso_scores, ae_scores = train_ensemble_model(X)
            
            # Calculate ensemble risk scores
            df['iso_score'] = iso_scores
            df['ae_score'] = ae_scores
            df['risk_score'] = [
                calculate_ensemble_risk_score(iso, ae, iso_scores, ae_scores)
                for iso, ae in zip(iso_scores, ae_scores)
            ]
            df['model_used'] = 'Ensemble (IF + AE)'
        else:
            # Use only Isolation Forest
            model = IsolationForest(contamination=contamination, random_state=42)
            model.fit(X)
            anomaly_scores = model.decision_function(X)
            
            scaler = MinMaxScaler(feature_range=(0, 100))
            scores = anomaly_scores.reshape(-1, 1)
            inverted_scores = -scores + max(scores)
            df['risk_score'] = scaler.fit_transform(inverted_scores).flatten()
            df['model_used'] = 'Isolation Forest'

        # Risk level assignment
        def assign_risk_level(score):
            if score > 85:
                return 'High'
            elif score > 60:
                return 'Medium'
            else:
                return 'Low'
        
        df['risk_level'] = df['risk_score'].apply(assign_risk_level)
        
        # Firewall action
        def adaptive_firewall_action(risk_level):
            if risk_level == 'High':
                return "🚫 BLOCK"
            elif risk_level == 'Medium':
                return "⚠️ RESTRICT"
            else:
                return "✅ ALLOW"
        
        df['firewall_action'] = df['risk_level'].apply(adaptive_firewall_action)
        df['timestamp'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return df

    with st.spinner("🔄 Training AI models and analyzing threats..."):
        df_processed = load_and_process_data(data_file, use_ensemble)

    if df_processed is not None:
        # Save to database
        save_to_database(df_processed)
        
        # === DASHBOARD SECTION ===
        st.header("📊 Threat Detection Dashboard")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        high_risk = (df_processed['risk_level'] == 'High').sum()
        medium_risk = (df_processed['risk_level'] == 'Medium').sum()
        low_risk = (df_processed['risk_level'] == 'Low').sum()
        
        with col1:
            st.metric("🔴 Critical Threats", high_risk, 
                     delta=f"{round(high_risk/len(df_processed)*100, 1)}% of total")
        with col2:
            st.metric("🟡 Medium Risk", medium_risk,
                     delta=f"{round(medium_risk/len(df_processed)*100, 1)}% of total")
        with col3:
            st.metric("🟢 Low Risk", low_risk,
                     delta=f"{round(low_risk/len(df_processed)*100, 1)}% of total")
        with col4:
            st.metric("📈 Total Analyzed", f"{len(df_processed):,}",
                     delta="Activities monitored")

        st.divider()

        # === TIMELINE VISUALIZATION ===
        if show_timeline and high_risk > 0:
            st.header("📅 Threat Timeline")
            
            threat_df = df_processed[df_processed['risk_level'].isin(['High', 'Medium'])].copy()
            threat_df['date_only'] = pd.to_datetime(threat_df['timestamp']).dt.date
            
            # Timeline chart
            timeline_data = threat_df.groupby(['date_only', 'risk_level']).size().reset_index(name='count')
            
            fig = px.line(timeline_data, x='date_only', y='count', color='risk_level',
                         title='Suspicious Activities Over Time',
                         color_discrete_map={'High': '#FF4B4B', 'Medium': '#FFA500'})
            fig.update_layout(xaxis_title="Date", yaxis_title="Number of Threats")
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()

        # === RISKY USERS SECTION ===
        if high_risk > 0:
            st.header("⚠️ High-Risk Users")
            
            risky_users = df_processed[df_processed['risk_level'] == 'High'].groupby('user').agg({
                'risk_level': 'count',
                'risk_score': 'mean'
            }).reset_index()
            risky_users.columns = ['User', 'High-Risk Incidents', 'Avg Risk Score']
            risky_users = risky_users.sort_values('High-Risk Incidents', ascending=False)
            
            fig = px.bar(risky_users.head(10), x='User', y='High-Risk Incidents',
                        color='Avg Risk Score', color_continuous_scale='Reds',
                        title='Top 10 High-Risk Users')
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()

        # === RISK HISTORY ===
        if show_history:
            st.header("📊 Risk Score History")
            
            history_days = st.slider("Show history for last N days:", 1, 30, 7)
            history_df = get_risk_history(days=history_days)
            
            if not history_df.empty:
                fig = px.scatter(history_df, x='timestamp', y='risk_score', 
                               color='risk_level', hover_data=['user', 'activity'],
                               title=f'Risk Scores - Last {history_days} Days',
                               color_discrete_map={'High': '#FF4B4B', 'Medium': '#FFA500', 'Low': '#00CC00'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No historical data available yet.")
            
            st.divider()

        # === DETAILED ALERTS TABLE ===
        st.header("🚨 Detailed Threat Alerts")
        
        high_risk_df = df_processed[df_processed['risk_level'] == 'High'].sort_values(
            by='risk_score', ascending=False
        ).head(20)
        
        if not high_risk_df.empty:
            st.dataframe(
                high_risk_df[['timestamp', 'user', 'pc', 'activity', 'risk_score', 'risk_level', 'firewall_action']],
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            csv = high_risk_df.to_csv(index=False)
            st.download_button(
                "📥 Download High-Risk Report",
                csv,
                f"high_risk_report_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        else:
            st.success("✅ No high-risk threats detected!")

        # === SYSTEM INFO ===
        st.divider()
        st.header("ℹ️ System Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            **AI Models Active:**  
            {'Isolation Forest + Autoencoder' if use_ensemble else 'Isolation Forest Only'}
            """)
        
        with col2:
            st.markdown(f"""
            **Dataset Used:**  
            {data_source}
            """)
        
        with col3:
            st.markdown(f"""
            **Detection Accuracy:**  
            Enhanced with Ensemble Learning
            """)

if __name__ == '__main__':
    main()
