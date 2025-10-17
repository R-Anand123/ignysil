import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

# --- Main Function to Run the Streamlit App ---
def main():
    """
    This function contains the entire logic for the Streamlit application.
    """
    st.set_page_config(layout="wide")
    st.title('🔥 Ignisyl - AI-Powered Insider Threat Detection')
    st.write("This dashboard analyzes user activity logs to detect potential insider threats using the Isolation Forest algorithm.")

    # --- 1. Load and Cache Data ---
    # Caching the data loading and processing helps the app run faster.
    @st.cache_data
    def load_and_process_data(file_path):
        """
        Loads data, preprocesses it, trains the model, and returns a full dataframe.
        """
        # A. Load the dataset
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            st.error(f"Error: '{file_path}' not found. Please make sure the dataset is in the correct directory.")
            return None

        # B. Preprocessing and Feature Engineering
        df['date'] = pd.to_datetime(df['date'])
        df['hour_of_day'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek # Monday=0, Sunday=6
        
        le_user = LabelEncoder()
        le_pc = LabelEncoder()
        le_activity = LabelEncoder()
        df['user_encoded'] = le_user.fit_transform(df['user'])
        df['pc_encoded'] = le_pc.fit_transform(df['pc'])
        df['activity_encoded'] = le_activity.fit_transform(df['activity'])

        features_for_model = ['user_encoded', 'pc_encoded', 'activity_encoded', 'hour_of_day', 'day_of_week']
        X = df[features_for_model]

        # C. Train the Isolation Forest Model
        model = IsolationForest(contamination=0.01, random_state=42)
        model.fit(X)
        df['anomaly_score'] = model.decision_function(X)
        
        # D. Develop the Dynamic Risk Score (0-100)
        scaler = MinMaxScaler(feature_range=(0, 100))
        scores = df['anomaly_score'].values.reshape(-1, 1)
        # Invert scores: lower anomaly score (more anomalous) -> higher risk score
        inverted_scores = -scores + max(scores)
        df['risk_score'] = scaler.fit_transform(inverted_scores).round(2)

        # E. Assign Risk Level
        def assign_risk_level(score):
            if score > 85:
                return 'High'
            elif score > 60:
                return 'Medium'
            else:
                return 'Low'
        df['risk_level'] = df['risk_score'].apply(assign_risk_level)

        # F. Simulate Adaptive Firewall Action
        def adaptive_firewall_action(risk_level):
            if risk_level == 'High':
                return "BLOCK"
            elif risk_level == 'Medium':
                return "RESTRICT"
            else:
                return "ALLOW"
        df['firewall_action'] = df['risk_level'].apply(adaptive_firewall_action)
        
        return df

    # --- 2. Run Analysis and Display Dashboard ---
    df_processed = load_and_process_data("logon.csv")

    if df_processed is not None:
        st.header("Threat Summary")
        
        # Create columns for summary metrics
        col1, col2, col3 = st.columns(3)
        high_risk_count = (df_processed['risk_level'] == 'High').sum()
        medium_risk_count = (df_processed['risk_level'] == 'Medium').sum()
        total_logs = len(df_processed)

        col1.metric("High-Risk Alerts", f"{high_risk_count}", "Immediate Action Required")
        col2.metric("Medium-Risk Alerts", f"{medium_risk_count}", "Requires Investigation")
        col3.metric("Total Activities Analyzed", f"{total_logs}")

        # Display High-Risk Alerts
        st.subheader("🔴 High-Risk User Alerts (Action: BLOCK)")
        high_risk_df = df_processed[df_processed['risk_level'] == 'High'].sort_values(by='risk_score', ascending=False)
        st.dataframe(high_risk_df[['date', 'user', 'pc', 'activity', 'risk_score', 'firewall_action']])

        # Display Medium-Risk Alerts
        st.subheader("🟡 Medium-Risk User Alerts (Action: RESTRICT)")
        medium_risk_df = df_processed[df_processed['risk_level'] == 'Medium'].sort_values(by='risk_score', ascending=False)
        st.dataframe(medium_risk_df[['date', 'user', 'pc', 'activity', 'risk_score', 'firewall_action']])
        
        # Display full log with a filter option
        st.subheader("Full Activity Log Explorer")
        if st.checkbox("Show all analyzed logs"):
            st.dataframe(df_processed)

# --- Script Entry Point ---
if __name__ == '__main__':
    main()
