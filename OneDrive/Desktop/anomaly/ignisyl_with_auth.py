"""
IGNISYL - COMPLETE SYSTEM WITH AUTHENTICATION
AI-Powered Insider Threat Detection with Role-Based Access Control

Academic Year 2025-2026
Sree Buddha College of Engineering Autonomous, Pattoor
Team: Ayswaria Lekshmi, R Anand, Sruthi G S, Vrinda V
Guide: Dr. Divya Mohan
"""

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from datetime import datetime
import json
import sqlite3
import hashlib
import plotly.express as px

# ==========================================
# AUTHENTICATION SYSTEM
# ==========================================

class AuthenticationSystem:
    """Complete authentication with role-based access control"""
    
    def __init__(self, db_path='ignisyl_database.db'):
        self.db_path = db_path
        self.init_auth_database()
    
    def init_auth_database(self):
        """Initialize authentication tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL,
                last_login DATETIME,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_name TEXT PRIMARY KEY,
                permissions TEXT
            )
        ''')
        
        conn.commit()
        self._init_defaults(conn)
        conn.close()
    
    def _init_defaults(self, conn):
        """Create default roles and users"""
        cursor = conn.cursor()
        
        # Default roles with permissions
        roles = [
            ('Admin', json.dumps({'all': True})),
            ('Security_Analyst', json.dumps({'view': True, 'whitelist': True, 'download': True})),
            ('Viewer', json.dumps({'view': True}))
        ]
        
        for role_name, perms in roles:
            cursor.execute('INSERT OR IGNORE INTO roles (role_name, permissions) VALUES (?, ?)', 
                          (role_name, perms))
        
        # Default users (only if no users exist)
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            users = [
                ('admin', 'admin123', 'System Administrator', 'admin@ignisyl.com', 'Admin'),
                ('analyst', 'analyst123', 'Security Analyst', 'analyst@ignisyl.com', 'Security_Analyst'),
                ('viewer', 'viewer123', 'Read Only User', 'viewer@ignisyl.com', 'Viewer')
            ]
            
            for username, password, full_name, email, role in users:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, full_name, email, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password_hash, full_name, email, role))
        
        conn.commit()
    
    def authenticate(self, username, password):
        """Authenticate user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, password_hash, full_name, email, role, is_active
            FROM users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return False, "Invalid username or password", None
        
        username_db, password_hash, full_name, email, role, is_active = user
        
        if not is_active:
            conn.close()
            return False, "Account is disabled", None
        
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if input_hash != password_hash:
            conn.close()
            return False, "Invalid username or password", None
        
        # Update last login
        cursor.execute('UPDATE users SET last_login = ? WHERE username = ?', 
                      (datetime.now().isoformat(), username))
        conn.commit()
        
        # Get permissions
        cursor.execute('SELECT permissions FROM roles WHERE role_name = ?', (role,))
        permissions_json = cursor.fetchone()[0]
        permissions = json.loads(permissions_json)
        
        user_data = {
            'username': username_db,
            'full_name': full_name,
            'email': email,
            'role': role,
            'permissions': permissions
        }
        
        conn.close()
        return True, "Login successful", user_data
    
    def has_permission(self, user_data, permission):
        """Check if user has specific permission"""
        if not user_data:
            return False
        permissions = user_data.get('permissions', {})
        return permissions.get('all', False) or permissions.get(permission, False)


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Ignisyl - AI Firewall",
    page_icon="🔥",
    layout="wide"
)

st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    h1 { color: #FF4B4B; }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# LOGIN PAGE
# ==========================================

def show_login_page():
    """Display login interface"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 3rem 0;">
                <h1 style="font-size: 4rem; color: #00FF00; font-family: 'Courier New', monospace; letter-spacing: 10px;">
                    IGNISYL
                </h1>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    AI-Powered Insider Threat Detection
                </p>
                <p style="color: #999; font-size: 0.9rem;">
                    Sree Buddha College of Engineering Autonomous
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔐 Secure Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                else:
                    auth = AuthenticationSystem()
                    success, message, user_data = auth.authenticate(username, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_data = user_data
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # Demo credentials
        with st.expander("🔑 Demo Credentials (For Testing)"):
            st.info("""
            **Full Access (Admin):**  
            Username: `admin` | Password: `admin123`
            
            **Security Analyst:**  
            Username: `analyst` | Password: `analyst123`
            
            **Read-Only (Viewer):**  
            Username: `viewer` | Password: `viewer123`
            """)
        
        st.markdown("---")
        st.caption("Academic Year 2025-2026 | Team: Ayswaria Lekshmi, R Anand, Sruthi G S, Vrinda V")


# ==========================================
# MAIN DASHBOARD
# ==========================================

def show_user_info():
    """Display user info in sidebar"""
    user = st.session_state.user_data
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 User Profile")
    st.sidebar.markdown(f"**{user['full_name']}**")
    st.sidebar.markdown(f"Role: `{user['role']}`")
    st.sidebar.markdown(f"User: `{user['username']}`")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.rerun()
    
    st.sidebar.markdown("---")


def main_dashboard():
    """Main application dashboard"""
    
    show_user_info()
    
    user = st.session_state.user_data
    auth = AuthenticationSystem()
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔥 Ignisyl - AI Firewall System")
        st.markdown("**AI-Powered Insider Threat Detection with Adaptive Firewall Control**")
    with col2:
        st.markdown(f"**User:** {user['full_name']}")
        st.markdown(f"**Role:** `{user['role']}`")
        st.markdown(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")
    
    st.divider()
    
    # Permission check
    if not auth.has_permission(user, 'view'):
        st.error("❌ Access Denied: You don't have permission to view this dashboard")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.subheader("⚙️ System Settings")
        
        data_file = st.text_input("Log File", value="logon.csv")
        
        # Settings (locked for non-admins)
        if auth.has_permission(user, 'all'):
            sensitivity = st.slider("Detection Sensitivity", 0.01, 0.10, 0.01, 0.01)
        else:
            st.info("🔒 Settings locked for your role")
            sensitivity = 0.01
        
        show_timeline = st.checkbox("Show Timeline", value=True)
    
    # Load and process data
    @st.cache_data
    def load_data(file_path, sens):
        try:
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            df['hour_of_day'] = df['date'].dt.hour
            df['day_of_week'] = df['date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['is_night'] = df['hour_of_day'].apply(lambda x: 1 if x < 6 or x > 22 else 0)
            
            le_user = LabelEncoder()
            le_pc = LabelEncoder()
            le_activity = LabelEncoder()
            df['user_encoded'] = le_user.fit_transform(df['user'])
            df['pc_encoded'] = le_pc.fit_transform(df['pc'])
            df['activity_encoded'] = le_activity.fit_transform(df['activity'])
            
            features = ['user_encoded', 'pc_encoded', 'activity_encoded', 
                       'hour_of_day', 'day_of_week', 'is_weekend', 'is_night']
            X = df[features]
            
            model = IsolationForest(contamination=sens, random_state=42)
            model.fit(X)
            scores = model.decision_function(X)
            
            scaler = MinMaxScaler(feature_range=(0, 100))
            inverted = -scores.reshape(-1, 1) + max(scores)
            df['risk_score'] = scaler.fit_transform(inverted).flatten()
            
            df['risk_level'] = df['risk_score'].apply(
                lambda x: 'High' if x > 85 else ('Medium' if x > 60 else 'Low')
            )
            
            df['firewall_action'] = df['risk_level'].apply(
                lambda x: "🚫 BLOCK" if x == 'High' else ("⚠️ RESTRICT" if x == 'Medium' else "✅ ALLOW")
            )
            
            df['timestamp'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None
    
    with st.spinner("🔄 AI analyzing threats..."):
        df = load_data(data_file, sensitivity)
    
    if df is not None:
        # Metrics
        st.header("📊 Threat Detection Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        high = (df['risk_level'] == 'High').sum()
        medium = (df['risk_level'] == 'Medium').sum()
        low = (df['risk_level'] == 'Low').sum()
        
        with col1:
            st.metric("🔴 Critical Threats", high, 
                     delta=f"{round(high/len(df)*100, 1)}%")
        with col2:
            st.metric("🟡 Medium Risk", medium,
                     delta=f"{round(medium/len(df)*100, 1)}%")
        with col3:
            st.metric("🟢 Low Risk", low,
                     delta=f"{round(low/len(df)*100, 1)}%")
        with col4:
            st.metric("📈 Total Analyzed", f"{len(df):,}")
        
        st.divider()
        
        # Timeline
        if show_timeline and high > 0:
            st.header("📅 Threat Timeline")
            threat_df = df[df['risk_level'].isin(['High', 'Medium'])].copy()
            threat_df['date_only'] = pd.to_datetime(threat_df['timestamp']).dt.date
            timeline = threat_df.groupby(['date_only', 'risk_level']).size().reset_index(name='count')
            
            fig = px.line(timeline, x='date_only', y='count', color='risk_level',
                         title='Suspicious Activities Over Time',
                         color_discrete_map={'High': '#FF4B4B', 'Medium': '#FFA500'})
            st.plotly_chart(fig, use_container_width=True)
            st.divider()
        
        # Risky users
        if high > 0:
            st.header("⚠️ High-Risk Users")
            risky = df[df['risk_level'] == 'High'].groupby('user').agg({
                'risk_level': 'count',
                'risk_score': 'mean'
            }).reset_index()
            risky.columns = ['User', 'Incidents', 'Avg Score']
            risky = risky.sort_values('Incidents', ascending=False)
            
            fig = px.bar(risky.head(10), x='User', y='Incidents',
                        color='Avg Score', color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
            st.divider()
        
        # Alerts table
        st.header("🚨 Detailed Threat Alerts")
        
        alerts = df[df['risk_level'] == 'High'].sort_values('risk_score', ascending=False).head(20)
        
        if not alerts.empty:
            st.dataframe(
                alerts[['timestamp', 'user', 'pc', 'activity', 'risk_score', 'risk_level', 'firewall_action']],
                use_container_width=True,
                hide_index=True
            )
            
            # Download (permission check)
            if auth.has_permission(user, 'download'):
                csv = alerts.to_csv(index=False)
                st.download_button(
                    "📥 Download Report",
                    csv,
                    f"threats_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            else:
                st.info("🔒 Download requires Analyst or Admin role")
        else:
            st.success("✅ No high-risk threats detected!")


# ==========================================
# MAIN
# ==========================================

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        main_dashboard()


if __name__ == '__main__':
    main()
