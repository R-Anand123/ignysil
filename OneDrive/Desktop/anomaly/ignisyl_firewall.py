import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from datetime import datetime
import json
import os
import time
import subprocess
import platform

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
    .firewall-status { 
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00FF00;
        color: #00FF00;
        font-family: 'Courier New', monospace;
    }
    .blocked-indicator {
        background-color: #FF4B4B;
        color: white;
        padding: 4px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .restricted-indicator {
        background-color: #FFA500;
        color: white;
        padding: 4px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Firewall Controller Class ---
class FirewallController:
    """Real firewall integration"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.test_mode = True  # Set to False for production
        self.action_log = []
    
    def block_ip_address(self, ip_address, rule_name="Ignisyl_Block"):
        """Block an IP address using system firewall"""
        try:
            if self.test_mode:
                # Simulation mode
                self.action_log.append({
                    "action": "BLOCK_IP",
                    "target": ip_address,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "SIMULATED"
                })
                return True, f"[TEST MODE] Would block IP: {ip_address}"
            
            if self.os_type == "Windows":
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}_{ip_address}" dir=in action=block remoteip={ip_address}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.returncode == 0, result.stdout or result.stderr
                
            elif self.os_type == "Linux":
                cmd = f'sudo iptables -A INPUT -s {ip_address} -j DROP'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.returncode == 0, result.stdout or result.stderr
                
        except Exception as e:
            return False, str(e)
    
    def restrict_port_access(self, port, protocol="TCP"):
        """Restrict access to specific port"""
        try:
            if self.test_mode:
                self.action_log.append({
                    "action": "RESTRICT_PORT",
                    "target": f"{port}/{protocol}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "SIMULATED"
                })
                return True, f"[TEST MODE] Would restrict port: {port}/{protocol}"
            
            if self.os_type == "Windows":
                cmd = f'netsh advfirewall firewall add rule name="Ignisyl_RestrictPort_{port}" dir=in action=block protocol={protocol} localport={port}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.returncode == 0, result.stdout or result.stderr
                
        except Exception as e:
            return False, str(e)
    
    def get_user_ip(self, pc_name):
        """Get IP address for PC (simulated mapping)"""
        ip_mapping = {
            "PC-001": "192.168.1.101", "PC-002": "192.168.1.102",
            "PC-003": "192.168.1.103", "PC-004": "192.168.1.104",
            "PC-005": "192.168.1.105", "PC-006": "192.168.1.106",
            "PC-007": "192.168.1.107", "PC-008": "192.168.1.108",
        }
        return ip_mapping.get(pc_name, "192.168.1.100")
    
    def apply_firewall_action(self, user, pc, risk_level):
        """Apply firewall rules based on risk level"""
        actions = []
        user_ip = self.get_user_ip(pc)
        
        if risk_level == "High":
            # BLOCK: Complete isolation
            success, msg = self.block_ip_address(user_ip, f"Ignisyl_HighRisk_{user}")
            actions.append({
                "type": "BLOCK IP",
                "target": user_ip,
                "success": success,
                "message": msg,
                "user": user,
                "pc": pc
            })
            
        elif risk_level == "Medium":
            # RESTRICT: Block high-risk ports
            high_risk_ports = [445, 3389, 22]  # SMB, RDP, SSH
            for port in high_risk_ports:
                success, msg = self.restrict_port_access(port)
                actions.append({
                    "type": "RESTRICT PORT",
                    "target": port,
                    "success": success,
                    "message": msg,
                    "user": user,
                    "pc": pc
                })
        
        return actions

# --- Whitelist Management ---
WHITELIST_FILE = "whitelist.json"

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r') as f:
            return json.load(f)
    return {"users": [], "activities": [], "user_activity_pairs": []}

def save_whitelist(whitelist):
    with open(WHITELIST_FILE, 'w') as f:
        json.dump(whitelist, f, indent=4)

def is_whitelisted(row, whitelist):
    user = row['user']
    activity = row['activity']
    
    if any(item["value"] == user for item in whitelist.get("users", [])):
        return True
    if any(item["value"] == activity for item in whitelist.get("activities", [])):
        return True
    if any(item["value"] == f"{user}|{activity}" for item in whitelist.get("user_activity_pairs", [])):
        return True
    
    return False

# --- Welcome Page ---
def show_welcome_page():
    st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 80vh; background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%); border-radius: 10px;">
            <div style="font-size: 5rem; font-weight: bold; color: #00FF00; text-align: center; font-family: 'Courier New', monospace; letter-spacing: 12px; text-shadow: 0 0 10px #00FF00, 0 0 20px #00FF00, 0 0 30px #00FF00; animation: glow 2s ease-in-out infinite;">
                IGNISYL
            </div>
            <div style="color: #00FF00; font-size: 1.1rem; font-family: 'Courier New', monospace; margin-top: 15px; opacity: 0.8; letter-spacing: 2px;">
                AI-Powered Firewall & Threat Detection System
            </div>
            <div style="color: #00FF00; font-size: 1rem; font-family: 'Courier New', monospace; margin-top: 30px;">
                ⚡ Initializing Firewall Protocols...
            </div>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2)
    return True

# --- Main Application ---
def main():
    # Initialize session state
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = False
    if 'firewall' not in st.session_state:
        st.session_state.firewall = FirewallController()
    
    # Show welcome page
    if not st.session_state.welcome_shown:
        show_welcome_page()
        st.session_state.welcome_shown = True
        st.rerun()
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔥 Ignisyl - AI Firewall System")
        st.markdown("**Real-time Threat Detection with Automated Firewall Response**")
    with col2:
        st.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
        mode_indicator = "🟡 TEST MODE" if st.session_state.firewall.test_mode else "🟢 LIVE MODE"
        st.markdown(f"**Mode:** {mode_indicator}")

    st.divider()

    # Sidebar
    with st.sidebar:
        st.title("🛡️ Firewall Control")
        st.divider()
        
        st.subheader("👤 Analyst Info")
        analyst_name = st.text_input("Your Name", value="Security Analyst")
        
        st.divider()
        
        st.subheader("🔥 Firewall Mode")
        test_mode = st.checkbox("Test Mode (Simulate Actions)", value=True, 
                               help="Enable to simulate firewall actions without actually blocking")
        st.session_state.firewall.test_mode = test_mode
        
        if not test_mode:
            st.error("⚠️ LIVE MODE: Real firewall rules will be applied!")
        
        st.divider()
        
        st.subheader("📁 Data Source")
        data_file = st.text_input("Log File", value="logon.csv")
        
        st.divider()
        
        st.subheader("⚙️ Detection Settings")
        contamination = st.slider("Sensitivity", 0.01, 0.10, 0.01, 0.01)
        auto_firewall = st.checkbox("Auto-Apply Firewall Rules", value=True,
                                   help="Automatically apply firewall rules for high-risk threats")

    # Load data
    @st.cache_data
    def load_and_process_data(file_path, contamination_level):
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            st.error(f"❌ Error: File '{file_path}' not found!")
            return None

        df['date'] = pd.to_datetime(df['date'])
        df['hour_of_day'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        
        le_user = LabelEncoder()
        le_pc = LabelEncoder()
        le_activity = LabelEncoder()
        df['user_encoded'] = le_user.fit_transform(df['user'])
        df['pc_encoded'] = le_pc.fit_transform(df['pc'])
        df['activity_encoded'] = le_activity.fit_transform(df['activity'])

        features_for_model = ['user_encoded', 'pc_encoded', 'activity_encoded', 'hour_of_day', 'day_of_week']
        X = df[features_for_model]
        
        model = IsolationForest(contamination=contamination_level, random_state=42)
        model.fit(X)
        df['anomaly_score'] = model.decision_function(X)
        
        scaler = MinMaxScaler(feature_range=(0, 100))
        scores = df['anomaly_score'].values.reshape(-1, 1)
        inverted_scores = -scores + max(scores)
        df['risk_score'] = scaler.fit_transform(inverted_scores).round(2)

        def assign_risk_level(score):
            if score > 85:
                return 'High'
            elif score > 60:
                return 'Medium'
            else:
                return 'Low'
        
        df['risk_level'] = df['risk_score'].apply(assign_risk_level)
        df['timestamp'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        whitelist = load_whitelist()
        df['is_whitelisted'] = df.apply(lambda row: is_whitelisted(row, whitelist), axis=1)
        
        return df

    with st.spinner("🔄 Analyzing threats and preparing firewall..."):
        df_processed = load_and_process_data(data_file, contamination)

    if df_processed is not None:
        # Firewall Status Panel
        st.header("🛡️ Firewall Status")
        col1, col2, col3, col4 = st.columns(4)
        
        high_risk = ((df_processed['risk_level'] == 'High') & (~df_processed['is_whitelisted'])).sum()
        medium_risk = ((df_processed['risk_level'] == 'Medium') & (~df_processed['is_whitelisted'])).sum()
        whitelisted = df_processed['is_whitelisted'].sum()
        
        with col1:
            st.metric("🔴 Threats Blocked", high_risk, delta="Auto-blocked by firewall")
        with col2:
            st.metric("🟡 Connections Restricted", medium_risk, delta="Ports restricted")
        with col3:
            st.metric("✅ Whitelisted", whitelisted, delta="Trusted activities")
        with col4:
            st.metric("📊 Total Analyzed", len(df_processed))

        st.divider()

        # High-Risk Threats with Firewall Actions
        if high_risk > 0:
            st.header("🔴 Critical Threats - Firewall Actions Applied")
            
            high_risk_df = df_processed[
                (df_processed['risk_level'] == 'High') & (~df_processed['is_whitelisted'])
            ].sort_values(by='risk_score', ascending=False).head(10)
            
            for idx, row in high_risk_df.iterrows():
                with st.expander(f"🚨 THREAT #{idx+1}: {row['user']} on {row['pc']} - Risk: {row['risk_score']}/100"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **Threat Details:**
                        - 👤 **User:** {row['user']}
                        - 💻 **Computer:** {row['pc']}
                        - 📋 **Activity:** {row['activity']}
                        - 🕐 **Time:** {row['timestamp']}
                        - 🔢 **Risk Score:** {row['risk_score']}/100
                        - 🌐 **IP Address:** {st.session_state.firewall.get_user_ip(row['pc'])}
                        """)
                    
                    with col2:
                        st.markdown("**🔥 Firewall Response:**")
                        
                        if auto_firewall:
                            if st.button(f"🚫 Apply Firewall Block", key=f"fw_{idx}"):
                                actions = st.session_state.firewall.apply_firewall_action(
                                    row['user'], row['pc'], row['risk_level']
                                )
                                
                                for action in actions:
                                    if action['success']:
                                        st.success(f"✅ {action['type']}: {action['message']}")
                                    else:
                                        st.error(f"❌ {action['type']}: {action['message']}")
                        else:
                            st.info("Enable 'Auto-Apply Firewall Rules' in sidebar")
            
            st.divider()

        # Firewall Action Log
        with st.expander("📋 View Firewall Action Log"):
            if st.session_state.firewall.action_log:
                log_df = pd.DataFrame(st.session_state.firewall.action_log)
                st.dataframe(log_df, use_container_width=True)
            else:
                st.info("No firewall actions logged yet")

        # System Information
        st.divider()
        st.header("ℹ️ System Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            **Operating System:**  
            {st.session_state.firewall.os_type}
            """)
        
        with col2:
            st.markdown(f"""
            **Firewall Status:**  
            {"🟡 Simulation Mode" if st.session_state.firewall.test_mode else "🟢 Active & Blocking"}
            """)
        
        with col3:
            st.markdown(f"""
            **Detection Algorithm:**  
            Isolation Forest ML
            """)

if __name__ == '__main__':
    main()
