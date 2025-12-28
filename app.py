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
COLOR_BG_BROKEN_WHITE = "#FDFBF7" # De kleur van jouw logo

# JOUW LOGO LINK
LOGO_URL = "https://i.postimg.cc/sXHV1JHy/Chat-GPT-Image-28-dec-2025-14-50-31.png"

st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="centered")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. PIXEL-PERFECT STYLING (CSS) ---
st.markdown(f"""
    <style>
    /* Achtergrond overal gelijk maken */
    .stApp {{
        background-color: {COLOR_BG_BROKEN_WHITE};
    }}

    /* Verberg Streamlit rommel (zoals de bovenbalk) voor een cleanere look */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Titels */
    h1, h2, h3 {{ 
        color: {COLOR_ACCENT} !important; 
        text-align: center;
        font-family: 'Inter', sans-serif;
    }}

    /* LOGIN CONTAINER: voorkomt scrollen en centreert alles */
    .login-wrapper {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        max-width: 420px; /* Vaste breedte tegen scrollen */
        padding-top: 20px;
    }}
    
    .login-logo-img {{
        display: block;
        margin-left: auto;
        margin-right: auto;
        height: 200px; /* Iets groter, maar in verhouding */
        width: auto;
        margin-bottom: 10px;
    }}

    /* Input velden aanpassen aan de breedte */
    .stTextInput, .stSelectbox {{
        width: 100% !important;
    }}

    .stTextInput input, .stSelectbox div {{
        background-color: white !important;
        border: 1px solid #e8e6e1 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }}

    /* De inlogknop */
    .stButton button {{
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        border: none !important;
        height: 45px !important;
        width: 100% !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        margin-top: 20px !important;
    }}

    /* PASPOORT KAART (Consument) */
    .passport-card {{
        background-color: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.03);
        text-align: center;
        border-top: 8px solid {COLOR_ACCENT};
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPERS ---
def get_data(url):
    with httpx.Client() as client:
        r = client.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []

# --- 4. LOGICA ---
if 'company' not in st.session_state: st.session_state.company = None

query_params = st.query_params

if "id" in query_params:
    # --- PASPOORT VIEW (Consument) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"""
            <div class="passport-card">
                <img src="{LOGO_URL}" style="height: 80px; margin-bottom: 20px;">
                <h3 style="margin:0; opacity:0.5; font-size: 0.8em; letter-spacing: 2px;">PRODUCT PASPOORT</h3>
                <h1 style="margin-top: 10px;">{d['name']}</h1>
                <p style="color: #666;">Fabrikant: <strong>{d['manufacturer']}</strong></p>
                <div style="display: flex; justify-content: space-around; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    <div><p style="font-size:0.8em; margin:0; color:#999;">CO2 IMPACT</p><h2>{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.8em; margin:0; color:#999;">RECYCLED</p><h2>{d['recycled_content']}%</h2></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- INLOG SCHERM ---
    if not st.session_state.company:
        companies = get_data(API_URL_COMPANIES)
        
        # We gebruiken geen kolommen meer voor centering, maar de CSS wrapper
        st.markdown(f'<div class="login-wrapper">', unsafe_allow_html=True)
        st.markdown(f'<img src="{LOGO_URL}" class="login-logo-img">', unsafe_allow_html=True)
        
        co_names = [c['name'] for c in companies]
        selected_co = st.selectbox("Selecteer uw organisatie", options=co_names, label_visibility="collapsed")
        pwd_input = st.text_input("Wachtwoord", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        
        if st.button("Inloggen op Portaal"):
            match = next((c for c in companies if c['name'] == selected_co), None)
            if match and match['password'] == pwd_input:
                st.session_state.company = selected_co
                st.rerun()
            else: st.error("Wachtwoord onjuist.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # --- DASHBOARD (Bedrijven / SuperAdmin) ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150)
        st.sidebar.divider()
        st.sidebar.write(f"Ingelogd: **{user}**")
        if st.sidebar.button("🚪 Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Global Data", "🏢 Bedrijven"])
            with t1:
                all_bats = get_data(API_URL_BATTERIES)
                if all_bats: st.dataframe(pd.DataFrame(all_bats), use_container_width=True, hide_index=True)
            with t2:
                cos = get_data(API_URL_COMPANIES)
                st.table(pd.DataFrame(cos)[['name', 'password']])
                with st.form("new_co"):
                    n, p = st.text_input("Naam Bedrijf"), st.text_input("Wachtwoord")
                    if st.form_submit_button("Voeg Bedrijf Toe"):
                        httpx.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.rerun()
        else:
            st.title(f"Portaal {user}")
            t1, t2, t3 = st.tabs(["✨ Registratie", "📊 Mijn Voorraad", "📂 Bulk Import"])
            # ... (Rest van de bekende code voor registratie en voorraad)
