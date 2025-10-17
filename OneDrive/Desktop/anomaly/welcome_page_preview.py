import streamlit as st
import time

st.set_page_config(page_title="Ignisyl Loading", layout="wide")

# Hide Streamlit default elements
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main {
        padding: 0;
        margin: 0;
    }
    
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
        stroke: #9D00FF;
        stroke-width: 3;
        fill: none;
        filter: drop-shadow(0 0 5px #9D00FF);
        animation: pulse 1.5s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { 
            stroke-width: 3;
            filter: drop-shadow(0 0 5px #9D00FF);
        }
        50% { 
            stroke-width: 4;
            filter: drop-shadow(0 0 10px #9D00FF) drop-shadow(0 0 20px #9D00FF);
        }
    }
    .brand-name {
        font-size: 5rem;
        font-weight: bold;
        color: #9D00FF;
        text-align: center;
        font-family: 'Courier New', monospace;
        letter-spacing: 12px;
        text-shadow: 0 0 10px #9D00FF, 0 0 20px #9D00FF, 0 0 30px #9D00FF;
        margin-top: 20px;
        animation: glow 2s ease-in-out infinite;
    }
    @keyframes glow {
        0%, 100% {
            text-shadow: 0 0 10px #9D00FF, 0 0 20px #9D00FF, 0 0 30px #9D00FF;
        }
        50% {
            text-shadow: 0 0 20px #9D00FF, 0 0 30px #9D00FF, 0 0 40px #9D00FF, 0 0 50px #9D00FF;
        }
    }
    .loading-text {
        color: #9D00FF;
        font-size: 1.2rem;
        font-family: 'Courier New', monospace;
        margin-top: 30px;
        animation: blink 1s ease-in-out infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .tagline {
        color: #9D00FF;
        font-size: 1.1rem;
        font-family: 'Courier New', monospace;
        margin-top: 15px;
        opacity: 0.8;
        letter-spacing: 2px;
    }
    .progress-bar-container {
        width: 400px;
        height: 4px;
        background-color: #1a1a1a;
        border-radius: 2px;
        margin-top: 30px;
        overflow: hidden;
        border: 1px solid #9D00FF;
    }
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #9D00FF, #00CC00);
        animation: progress 3s ease-in-out forwards;
        box-shadow: 0 0 10px #9D00FF;
    }
    @keyframes progress {
        0% { width: 0%; }
        100% { width: 100%; }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="welcome-container">
        <div class="heartbeat-container">
            <div class="heartbeat">
                <svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg">
                    <polyline class="heartbeat-line" points="
                        0,100
                        80,100
                        100,100
                        110,60
                        120,140
                        130,40
                        140,100
                        160,100
                        240,100
                        260,100
                        270,60
                        280,140
                        290,40
                        300,100
                        320,100
                        400,100
                        420,100
                        430,60
                        440,140
                        450,40
                        460,100
                        480,100
                        560,100
                        580,100
                        590,60
                        600,140
                        610,40
                        620,100
                        640,100
                        720,100
                        740,100
                        750,60
                        760,140
                        770,40
                        780,100
                        800,100
                    "/>
                </svg>
            </div>
        </div>
        <div class="brand-name">IGNISYL</div>
        <div class="tagline">AI-Powered Insider Threat Detection System</div>
        <div class="loading-text">⚡ Initializing Security Protocols...</div>
        <div class="progress-bar-container">
            <div class="progress-bar"></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Simulate loading
time.sleep(3)
st.success("✅ System Loaded! Redirecting to dashboard...")
time.sleep(1)
