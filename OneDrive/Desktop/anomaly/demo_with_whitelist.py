import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from datetime import datetime
import json
import os
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Ignisyl - Insider Threat Detection",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Better UI ---
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    h1 {
        color: #FF4B4B;
        padding-bottom: 1rem;
    }
    h2 {
        color: #262730;
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }
    h3 {
        color: #4F4F4F;
        font-size: 1.2rem;
        padding-top: 0.5rem;
    }
    .whitelist-badge {
        background-color: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.8rem;
    }
    
    /* Welcome Page Styles */
    .welcome-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100vh;
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
    }
    .heartbeat-container {
        width: 80%;
        max-width: 800px;
        height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 30px;
    }
    .heartbeat {
        width: 100%;
        height: 200px;
        position: relative;
    }
    .heartbeat svg {
        width: 100%;
        height: 100%;
    }
    .heartbeat-line {
        stroke: #00FF00;
        stroke-width: 3;
        fill: none;
        filter: drop-shadow(0 0 5px #00FF00);
    }
    @keyframes pulse {
        0%, 100% { 
            stroke-width: 3;
            filter: drop-shadow(0 0 5px #00FF00);
        }
        50% { 
            stroke-width: 4;
            filter: drop-shadow(0 0 10px #00FF00) drop-shadow(0 0 20px #00FF00);
        }
    }
    .heartbeat-line {
        animation: pulse 1.5s ease-in-out infinite;
    }
    .brand-name {
        font-size: 4rem;
        font-weight: bold;
        color: #00FF00;
        text-align: center;
        font-family: 'Courier New', monospace;
        letter-spacing: 8px;
        text-shadow: 0 0 10px #00FF00, 0 0 20px #00FF00, 0 0 30px #00FF00;
        margin-top: 20px;
        animation: glow 2s ease-in-out infinite;
    }
    @keyframes glow {
        0%, 100% {
            text-shadow: 0 0 10px #00FF00, 0 0 20px #00FF00, 0 0 30px #00FF00;
        }
        50% {
            text-shadow: 0 0 20px #00FF00, 0 0 30px #00FF00, 0 0 40px #00FF00, 0 0 50px #00FF00;
        }
    }
    .loading-text {
        color: #00FF00;
        font-size: 1.2rem;
        font-family: 'Courier New', monospace;
        margin-top: 20px;
        animation: blink 1s ease-in-out infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .tagline {
        color: #00FF00;
        font-size: 1rem;
        font-family: 'Courier New', monospace;
        margin-top: 10px;
        opacity: 0.8;
    }
    </style>
""", unsafe_allow_html=True)

# --- Welcome/Loading Page ---
def show_welcome_page():
    """Display animated welcome page with heartbeat"""
    st.markdown("""
        <div class="welcome-container">
            <div class="heartbeat-container">
                <div class="heartbeat">
                    <svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg">
                        <polyline class="heartbeat-line" points="
                            0,100
                            100,100
                            120,100
                            130,60
                            140,140
                            150,40
                            160,100
                            200,100
                            300,100
                            320,100
                            330,60
                            340,140
                            350,40
                            360,100
                            400,100
                            500,100
                            520,100
                            530,60
                            540,140
                            550,40
                            560,100
                            600,100
                            700,100
                            720,100
                            730,60
                            740,140
                            750,40
                            760,100
                            800,100
                        "/>
                    </svg>
                </div>
            </div>
            <div class="brand-name">IGNISYL</div>
            <div class="tagline">AI-Powered Insider Threat Detection System</div>
            <div class="loading-text">⚡ Initializing Security Protocols...</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Simulate loading with progress
    progress_placeholder = st.empty()
    
    loading_steps = [
        "Loading AI Models...",
        "Scanning Activity Logs...",
        "Analyzing Patterns...",
        "Initializing Firewall...",
        "System Ready!"
    ]
    
    for i, step in enumerate(loading_steps):
        time.sleep(0.6)
        progress = (i + 1) / len(loading_steps)
    
    time.sleep(0.5)
    return True

# --- Whitelist Management Functions ---
WHITELIST_FILE = "whitelist.json"
FEEDBACK_FILE = "analyst_feedback.json"

def load_whitelist():
    """Load whitelist from JSON file"""
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r') as f:
            return json.load(f)
    return {"users": [], "activities": [], "user_activity_pairs": [], "user_pc_pairs": []}

def save_whitelist(whitelist):
    """Save whitelist to JSON file"""
    with open(WHITELIST_FILE, 'w') as f:
        json.dump(whitelist, f, indent=4)

def load_feedback():
    """Load analyst feedback history"""
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r') as f:
            return json.load(f)
    return []

def save_feedback(feedback_list):
    """Save analyst feedback history"""
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_list, f, indent=4)

def add_to_whitelist(whitelist_type, value, analyst_name, reason):
    """Add an item to whitelist with metadata"""
    whitelist = load_whitelist()
    feedback = load_feedback()
    
    entry = {
        "value": value,
        "added_by": analyst_name,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if whitelist_type not in whitelist:
        whitelist[whitelist_type] = []
    
    # Check if already whitelisted
    if not any(item["value"] == value for item in whitelist[whitelist_type]):
        whitelist[whitelist_type].append(entry)
        save_whitelist(whitelist)
        
        # Save to feedback history
        feedback.append({
            "type": "whitelist_add",
            "category": whitelist_type,
            "entry": entry
        })
        save_feedback(feedback)
        return True
    return False

def remove_from_whitelist(whitelist_type, value):
    """Remove an item from whitelist"""
    whitelist = load_whitelist()
    if whitelist_type in whitelist:
        whitelist[whitelist_type] = [item for item in whitelist[whitelist_type] if item["value"] != value]
        save_whitelist(whitelist)
        return True
    return False

def is_whitelisted(row, whitelist):
    """Check if an activity should be whitelisted"""
    user = row['user']
    activity = row['activity']
    pc = row['pc']
    
    # Check individual whitelists
    if any(item["value"] == user for item in whitelist.get("users", [])):
        return True
    if any(item["value"] == activity for item in whitelist.get("activities", [])):
        return True
    if any(item["value"] == f"{user}|{activity}" for item in whitelist.get("user_activity_pairs", [])):
        return True
    if any(item["value"] == f"{user}|{pc}" for item in whitelist.get("user_pc_pairs", [])):
        return True
    
    return False

# --- Main Function ---
def main():
    # Initialize session state for welcome page
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = False
    
    # Show welcome page on first load
    if not st.session_state.welcome_shown:
        show_welcome_page()
        st.session_state.welcome_shown = True
        st.rerun()
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔥 Ignisyl - Insider Threat Detection")
        st.markdown("**AI-Powered Security Monitoring System with Analyst Feedback**")
    with col2:
        st.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
        st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

    st.divider()

    # --- Sidebar ---
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/security-shield-green.png", width=80)
        st.title("Control Panel")
        st.divider()
        
        # Analyst Information
        st.subheader("👤 Analyst Info")
        analyst_name = st.text_input("Your Name", value="Security Analyst", help="Enter your name for audit trail")
        
        st.divider()
        
        st.subheader("📁 Data Source")
        data_file = st.text_input("Log File Path", value="logon.csv", help="Path to your CSV log file")
        
        st.divider()
        
        st.subheader("⚙️ Detection Settings")
        contamination = st.slider(
            "Anomaly Detection Sensitivity", 
            min_value=0.01, 
            max_value=0.10, 
            value=0.01, 
            step=0.01,
            help="Lower = More sensitive (more alerts)"
        )
        
        apply_whitelist = st.checkbox("Apply Whitelist Filter", value=True, help="Hide whitelisted activities from alerts")
        
        st.divider()
        
        st.subheader("🔍 View Options")
        show_high_only = st.checkbox("Show High-Risk Only", value=False)
        show_medium_only = st.checkbox("Show Medium-Risk Only", value=False)
        
        st.divider()
        
        # Navigation
        st.subheader("📋 Navigation")
        page = st.radio("Go to:", ["🏠 Dashboard", "✅ Whitelist Manager", "📊 Feedback History"])

    # Load whitelist
    whitelist = load_whitelist()

    # --- Load and Process Data ---
    @st.cache_data
    def load_and_process_data(file_path, contamination_level):
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            st.error(f"❌ Error: File '{file_path}' not found!")
            st.info("Please check the file path in the sidebar.")
            return None
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            return None

        # Preprocessing
        df['date'] = pd.to_datetime(df['date'])
        df['hour_of_day'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        
        # Encoding
        le_user = LabelEncoder()
        le_pc = LabelEncoder()
        le_activity = LabelEncoder()
        df['user_encoded'] = le_user.fit_transform(df['user'])
        df['pc_encoded'] = le_pc.fit_transform(df['pc'])
        df['activity_encoded'] = le_activity.fit_transform(df['activity'])

        # Model Training
        features_for_model = ['user_encoded', 'pc_encoded', 'activity_encoded', 'hour_of_day', 'day_of_week']
        X = df[features_for_model]
        
        model = IsolationForest(contamination=contamination_level, random_state=42)
        model.fit(X)
        df['anomaly_score'] = model.decision_function(X)
        
        # Risk Score Calculation
        scaler = MinMaxScaler(feature_range=(0, 100))
        scores = df['anomaly_score'].values.reshape(-1, 1)
        inverted_scores = -scores + max(scores)
        df['risk_score'] = scaler.fit_transform(inverted_scores).round(2)

        # Risk Level Assignment
        def assign_risk_level(score):
            if score > 85:
                return 'High'
            elif score > 60:
                return 'Medium'
            else:
                return 'Low'
        
        df['risk_level'] = df['risk_score'].apply(assign_risk_level)

        # Check whitelist status
        df['is_whitelisted'] = df.apply(lambda row: is_whitelisted(row, whitelist), axis=1)

        # Firewall Action
        def adaptive_firewall_action(row):
            if row['is_whitelisted']:
                return "✅ ALLOWED (Whitelisted)"
            elif row['risk_level'] == 'High':
                return "🚫 BLOCKED"
            elif row['risk_level'] == 'Medium':
                return "⚠️ RESTRICTED"
            else:
                return "✅ ALLOWED"
        
        df['firewall_action'] = df.apply(adaptive_firewall_action, axis=1)
        
        # Format date for display
        df['timestamp'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return df

    # Load Data
    with st.spinner("🔄 Loading and analyzing data..."):
        df_processed = load_and_process_data(data_file, contamination)

    if df_processed is not None:
        
        # --- PAGE ROUTING ---
        if page == "🏠 Dashboard":
            show_dashboard(df_processed, whitelist, apply_whitelist, show_high_only, show_medium_only, analyst_name)
        elif page == "✅ Whitelist Manager":
            show_whitelist_manager(df_processed, analyst_name)
        elif page == "📊 Feedback History":
            show_feedback_history()

# --- Dashboard Page ---
def show_dashboard(df_processed, whitelist, apply_whitelist, show_high_only, show_medium_only, analyst_name):
    # Filter out whitelisted items if enabled
    if apply_whitelist:
        df_display = df_processed[~df_processed['is_whitelisted']].copy()
        whitelisted_count = df_processed['is_whitelisted'].sum()
        if whitelisted_count > 0:
            st.info(f"ℹ️ {whitelisted_count} activities hidden (whitelisted). Disable 'Apply Whitelist Filter' to see them.")
    else:
        df_display = df_processed.copy()
    
    # --- Summary Metrics ---
    st.header("📊 Threat Overview")
    
    high_risk_count = ((df_display['risk_level'] == 'High') & (~df_display['is_whitelisted'])).sum()
    medium_risk_count = ((df_display['risk_level'] == 'Medium') & (~df_display['is_whitelisted'])).sum()
    low_risk_count = ((df_display['risk_level'] == 'Low') & (~df_display['is_whitelisted'])).sum()
    whitelisted_total = df_processed['is_whitelisted'].sum()
    total_logs = len(df_processed)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🔴 Critical Threats",
            value=high_risk_count,
            delta=f"{round(high_risk_count/total_logs*100, 1)}% of total"
        )
    
    with col2:
        st.metric(
            label="🟡 Medium Risk",
            value=medium_risk_count,
            delta=f"{round(medium_risk_count/total_logs*100, 1)}% of total"
        )
    
    with col3:
        st.metric(
            label="✅ Whitelisted",
            value=whitelisted_total,
            delta=f"{round(whitelisted_total/total_logs*100, 1)}% of total",
            delta_color="off"
        )
    
    with col4:
        st.metric(
            label="📈 Total Activities",
            value=f"{total_logs:,}",
            delta="Analyzed"
        )

    st.divider()

    # --- Alert Summary ---
    if high_risk_count > 0:
        st.error(f"⚠️ **ALERT:** {high_risk_count} high-risk threat(s) detected requiring immediate action!")
    elif medium_risk_count > 0:
        st.warning(f"⚠️ **NOTICE:** {medium_risk_count} medium-risk activity(ies) detected. Investigation recommended.")
    else:
        st.success("✅ **ALL CLEAR:** No significant threats detected. System operating normally.")

    st.divider()

    # --- High-Risk Alerts with Whitelist Option ---
    if high_risk_count > 0:
        st.header("🔴 Critical Threat Alerts")
        st.markdown("**Review and take action on these activities**")
        
        high_risk_df = df_display[
            (df_display['risk_level'] == 'High') & (~df_display['is_whitelisted'])
        ].sort_values(by='risk_score', ascending=False).reset_index(drop=True)
        
        for idx, row in high_risk_df.iterrows():
            with st.expander(f"🔴 Alert #{idx+1}: {row['user']} - {row['activity']} (Risk: {row['risk_score']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    **Details:**
                    - **User:** {row['user']}
                    - **Computer:** {row['pc']}
                    - **Activity:** {row['activity']}
                    - **Timestamp:** {row['timestamp']}
                    - **Risk Score:** {row['risk_score']}/100
                    - **Action:** {row['firewall_action']}
                    """)
                
                with col2:
                    st.markdown("**🛡️ Analyst Actions:**")
                    
                    action = st.radio(
                        "Mark as:",
                        ["Genuine Threat", "False Positive"],
                        key=f"action_high_{idx}",
                        help="Select if this is a real threat or false alarm"
                    )
                    
                    if action == "False Positive":
                        whitelist_type = st.selectbox(
                            "Whitelist:",
                            ["User + Activity", "User Only", "Activity Only", "User + PC"],
                            key=f"type_high_{idx}"
                        )
                        
                        reason = st.text_input(
                            "Reason for whitelisting:",
                            key=f"reason_high_{idx}",
                            placeholder="e.g., Authorized maintenance work"
                        )
                        
                        if st.button(f"✅ Whitelist & Allow", key=f"whitelist_high_{idx}"):
                            if reason.strip():
                                if whitelist_type == "User Only":
                                    success = add_to_whitelist("users", row['user'], analyst_name, reason)
                                elif whitelist_type == "Activity Only":
                                    success = add_to_whitelist("activities", row['activity'], analyst_name, reason)
                                elif whitelist_type == "User + Activity":
                                    success = add_to_whitelist("user_activity_pairs", f"{row['user']}|{row['activity']}", analyst_name, reason)
                                elif whitelist_type == "User + PC":
                                    success = add_to_whitelist("user_pc_pairs", f"{row['user']}|{row['pc']}", analyst_name, reason)
                                
                                if success:
                                    st.success(f"✅ Added to whitelist! Refresh to see changes.")
                                    st.rerun()
                                else:
                                    st.warning("Already whitelisted!")
                            else:
                                st.error("Please provide a reason for whitelisting.")
        
        st.divider()

    # --- Medium-Risk Alerts with Whitelist Option ---
    if medium_risk_count > 0:
        st.header("🟡 Medium-Risk Activities")
        st.markdown("**Review these activities for potential concerns**")
        
        medium_risk_df = df_display[
            (df_display['risk_level'] == 'Medium') & (~df_display['is_whitelisted'])
        ].sort_values(by='risk_score', ascending=False).reset_index(drop=True)
        
        # Show in a table with action buttons
        display_columns = ['timestamp', 'user', 'pc', 'activity', 'risk_score']
        st.dataframe(
            medium_risk_df[display_columns].head(20),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("**Quick Actions:**")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_idx = st.number_input(
                "Select row # to whitelist:",
                min_value=0,
                max_value=len(medium_risk_df)-1,
                value=0,
                key="medium_select"
            )
        
        with col2:
            if selected_idx < len(medium_risk_df):
                selected_row = medium_risk_df.iloc[selected_idx]
                st.info(f"Selected: {selected_row['user']} - {selected_row['activity']}")
        
        if selected_idx < len(medium_risk_df):
            col1, col2 = st.columns(2)
            
            with col1:
                whitelist_type_medium = st.selectbox(
                    "Whitelist type:",
                    ["User + Activity", "User Only", "Activity Only"],
                    key="type_medium"
                )
            
            with col2:
                reason_medium = st.text_input(
                    "Reason:",
                    key="reason_medium",
                    placeholder="Why is this safe?"
                )
            
            if st.button("✅ Whitelist Selected Activity", key="whitelist_medium"):
                if reason_medium.strip():
                    row = medium_risk_df.iloc[selected_idx]
                    if whitelist_type_medium == "User Only":
                        success = add_to_whitelist("users", row['user'], analyst_name, reason_medium)
                    elif whitelist_type_medium == "Activity Only":
                        success = add_to_whitelist("activities", row['activity'], analyst_name, reason_medium)
                    elif whitelist_type_medium == "User + Activity":
                        success = add_to_whitelist("user_activity_pairs", f"{row['user']}|{row['activity']}", analyst_name, reason_medium)
                    
                    if success:
                        st.success("✅ Successfully whitelisted!")
                        st.rerun()
                    else:
                        st.warning("Already whitelisted!")
                else:
                    st.error("Please provide a reason.")
        
        st.divider()

# --- Whitelist Manager Page ---
def show_whitelist_manager(df_processed, analyst_name):
    st.header("✅ Whitelist Management")
    st.markdown("**Manage trusted users, activities, and combinations**")
    
    whitelist = load_whitelist()
    
    tabs = st.tabs(["👤 Users", "📋 Activities", "🔗 User+Activity Pairs", "💻 User+PC Pairs"])
    
    # Users Tab
    with tabs[0]:
        st.subheader("Whitelisted Users")
        if whitelist.get("users"):
            for item in whitelist["users"]:
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.write(f"**{item['value']}**")
                with col2:
                    st.write(f"By: {item['added_by']}")
                with col3:
                    st.write(f"Reason: {item['reason']}")
                with col4:
                    if st.button("🗑️", key=f"del_user_{item['value']}"):
                        remove_from_whitelist("users", item['value'])
                        st.rerun()
        else:
            st.info("No users whitelisted yet.")
    
    # Activities Tab
    with tabs[1]:
        st.subheader("Whitelisted Activities")
        if whitelist.get("activities"):
            for item in whitelist["activities"]:
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.write(f"**{item['value']}**")
                with col2:
                    st.write(f"By: {item['added_by']}")
                with col3:
                    st.write(f"Reason: {item['reason']}")
                with col4:
                    if st.button("🗑️", key=f"del_activity_{item['value']}"):
                        remove_from_whitelist("activities", item['value'])
                        st.rerun()
        else:
            st.info("No activities whitelisted yet.")
    
    # User+Activity Pairs Tab
    with tabs[2]:
        st.subheader("Whitelisted User+Activity Combinations")
        if whitelist.get("user_activity_pairs"):
            for item in whitelist["user_activity_pairs"]:
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.write(f"**{item['value']}**")
                with col2:
                    st.write(f"By: {item['added_by']}")
                with col3:
                    st.write(f"Reason: {item['reason']}")
                with col4:
                    if st.button("🗑️", key=f"del_pair_{item['value']}"):
                        remove_from_whitelist("user_activity_pairs", item['value'])
                        st.rerun()
        else:
            st.info("No user+activity pairs whitelisted yet.")
    
    # User+PC Pairs Tab
    with tabs[3]:
        st.subheader("Whitelisted User+PC Combinations")
        if whitelist.get("user_pc_pairs"):
            for item in whitelist["user_pc_pairs"]:
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.write(f"**{item['value']}**")
                with col2:
                    st.write(f"By: {item['added_by']}")
                with col3:
                    st.write(f"Reason: {item['reason']}")
                with col4:
                    if st.button("🗑️", key=f"del_pc_{item['value']}"):
                        remove_from_whitelist("user_pc_pairs", item['value'])
                        st.rerun()
        else:
            st.info("No user+PC pairs whitelisted yet.")

# --- Feedback History Page ---
def show_feedback_history():
    st.header("📊 Analyst Feedback History")
    st.markdown("**Audit trail of all whitelist decisions**")
    
    feedback = load_feedback()
    
    if feedback:
        # Reverse to show newest first
        for idx, entry in enumerate(reversed(feedback)):
            with st.expander(f"Entry #{len(feedback)-idx}: {entry['entry']['timestamp']}"):
                st.markdown(f"""
                **Action:** {entry['type']}  
                **Category:** {entry['category']}  
                **Value:** {entry['entry']['value']}  
                **Analyst:** {entry['entry']['added_by']}  
                **Reason:** {entry['entry']['reason']}  
                **Timestamp:** {entry['entry']['timestamp']}
                """)
    else:
        st.info("No feedback history yet.")

if __name__ == '__main__':
    main()
