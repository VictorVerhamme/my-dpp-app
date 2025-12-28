import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

# Kleuren
COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_BROKEN_WHITE = "#FDFBF7" # De kleur van jouw logo achtergrond

# JOUW LOGO LINK
LOGO_URL = "https://i.postimg.cc/sXHV1JHy/Chat-GPT-Image-28-dec-2025-14-50-31.png"

st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. VERFIJNDE STYLING (CSS) ---
st.markdown(f"""
    <style>
    /* De hele app krijgt de kleur van het logo */
    .stApp {{
        background-color: {COLOR_BG_BROKEN_WHITE}; 
    }}
    
    /* Titels in Saliegroen */
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; font-family: 'Inter', sans-serif; }}

    /* Inlog kaart zonder de groene balk */
    .login-container {{
        display: flex;
        justify-content: center;
        padding-top: 80px;
    }}
    
    .login-card {{
        background-color: {COLOR_BG_BROKEN_WHITE}; /* Zelfde kleur als logo */
        padding: 20px 40px;
        border-radius: 0px; /* Strakker design */
        text-align: center;
        max-width: 450px;
        width: 100%;
    }}
    
    /* Logo subtieler maken */
    .login-logo-img {{
        height: 120px; /* Kleiner en chiquer */
        width: auto;
        margin-bottom: 20px;
    }}

    /* Input velden styling */
    .stTextInput input, .stSelectbox div {{
        background-color: transparent !important;
        border: 1px solid #ddd !important;
        border-radius: 5px !important;
    }}

    /* Button styling */
    .stButton button {{
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        width: 100%;
        border-radius: 5px !important;
    }}

    /* Paspoort kaart (Consument) */
    .passport-card {{
        background-color: white;
        padding: 50px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        max-width: 700px;
        margin: auto;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPERS ---
def get_data(url):
    with httpx.Client() as client:
        r = client.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []

# --- 4. LOGICA ---
if 'qr_data' not in st.session_state: st.session_state.qr_data = None
if 'temp_name' not in st.session_state: st.session_state.temp_name = ""

query_params = st.query_params

if "id" in query_params:
    # --- PASPOORT VIEW (Consument) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"""
            <div class="passport-card">
                <img src="{LOGO_URL}" style="height: 60px; margin-bottom: 30px;">
                <h3 style="margin:0; opacity:0.6; font-size: 0.8em; letter-spacing: 2px;">PRODUCT PASPOORT</h3>
                <h1 style="margin-top: 5px;">{d['name']}</h1>
                <p style="font-size: 1.1em; color: #555;">Geverifieerde fabrikant: <strong>{d['manufacturer']}</strong></p>
                <div style="display: flex; gap: 60px; margin-top: 40px; border-top: 1px solid #eee; padding-top: 30px;">
                    <div><p style="font-size:0.8em; margin:0; color:#888;">CO2 IMPACT</p><h2 style="margin-top:5px;">{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.8em; margin:0; color:#888;">RECYCLED CONTENT</p><h2 style="margin-top:5px;">{d['recycled_content']}%</h2></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- LOGIN ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        companies = get_data(API_URL_COMPANIES)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f'<div class="login-container"><div class="login-card">', unsafe_allow_html=True)
            st.markdown(f'<img src="{LOGO_URL}" class="login-logo-img">', unsafe_allow_html=True)
            
            co_names = [c['name'] for c in companies]
            selected_co = st.selectbox("Kies uw organisatie", options=co_names)
            pwd_input = st.text_input("Wachtwoord", type="password")
            
            if st.button("Inloggen"):
                match = next((c for c in companies if c['name'] == selected_co), None)
                if match and match['password'] == pwd_input:
                    st.session_state.company = selected_co
                    st.rerun()
                else: st.error("Controleer uw gegevens.")
            
            st.markdown('</div></div>', unsafe_allow_html=True)

    else:
        # --- DASHBOARD (Admin / Bedrijf) ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=120)
        st.sidebar.write(f"Ingelogd: **{user}**")
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Systeem Data", "🏢 Bedrijven"])
            with t1:
                all_bats = get_data(API_URL_BATTERIES)
                if all_bats: st.dataframe(pd.DataFrame(all_bats), use_container_width=True)
            with t2:
                cos = get_data(API_URL_COMPANIES)
                st.table(pd.DataFrame(cos)[['name', 'password']])
                with st.form("new_co"):
                    n, p = st.text_input("Naam"), st.text_input("Wachtwoord")
                    if st.form_submit_button("Voeg Bedrijf Toe"):
                        httpx.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.rerun()
        else:
            st.title(f"Portaal: {user}")
            t1, t2 = st.tabs(["✨ Registratie", "📊 Voorraad"])
            with t1:
                with st.form("add"):
                    name = st.text_input("Model")
                    co2 = st.number_input("CO2 Impact", min_value=0.0)
                    rec = st.slider("Recycled %", 0, 100, 20)
                    if st.form_submit_button("Opslaan"):
                        payload = {"name": name, "manufacturer": user, "carbon_footprint": co2, "recycled_content": rec}
                        httpx.post(API_URL_BATTERIES, json=payload, headers=headers)
                        st.success("Geregistreerd!")
            with t2:
                my_bats = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if my_bats: st.dataframe(pd.DataFrame(my_bats), use_container_width=True)
