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
COLOR_BG_BROKEN_WHITE = "#FDFBF7" # Achtergrond van je logo

# LOGO LINK
LOGO_URL = "https://i.postimg.cc/sXHV1JHy/Chat-GPT-Image-28-dec-2025-14-50-31.png"

# We houden layout op "wide" zodat we via CSS de exacte controle hebben over het midden
st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. FOCUS & CENTRERING STYLING (CSS) ---
st.markdown(f"""
    <style>
    /* Achtergrond van de hele app */
    .stApp {{
        background-color: {COLOR_BG_BROKEN_WHITE};
    }}

    /* Verberg Streamlit menu/balken */
    header, footer {{visibility: hidden;}}
    
    /* Titels */
    h1, h2, h3 {{ 
        color: {COLOR_ACCENT} !important; 
        text-align: center;
        font-family: 'Inter', sans-serif;
    }}

    /* DE CENTRALE WRAPPER: Dit zorgt voor de lege ruimte aan de zijkanten */
    .central-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        max-width: 450px; /* Dit beperkt de breedte van de balken */
        padding-top: 8vh;
        width: 100%;
    }}
    
    /* Logo perfect centreren en grootte controleren */
    .centered-logo {{
        display: block;
        height: 220px; 
        width: auto;
        margin: 0 auto 30px auto; /* Centreert horizontaal en geeft ruimte eronder */
    }}

    /* Schone invoervelden zonder extra balken */
    div[data-baseweb="input"] {{
        background-color: white !important;
        border: 1px solid #e0ddd7 !important;
        border-radius: 12px !important;
        padding: 5px !important;
        margin-bottom: 10px;
    }}
    
    .stTextInput input {{
        background-color: white !important;
        border: none !important;
        font-size: 16px !important;
        text-align: center; /* Tekst in de balk ook centreren voor balans */
    }}

    /* De knop gecentreerd en compact */
    .stButton button {{
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        border: none !important;
        height: 50px !important;
        width: 100% !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        margin-top: 20px !important;
        transition: transform 0.2s ease;
    }}
    
    .stButton button:hover {{
        transform: scale(1.02);
        background-color: {COLOR_ACCENT};
        color: white;
    }}

    /* Paspoort kaart (Consument) ook centreren */
    .passport-card {{
        background-color: white;
        padding: 50px;
        border-radius: 25px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.02);
        text-align: center;
        max-width: 600px;
        margin: 40px auto;
        border: 1px solid #f2f0eb;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPERS ---
def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except:
        return []

# --- 4. LOGICA ---
if 'company' not in st.session_state: st.session_state.company = None

query_params = st.query_params

if "id" in query_params:
    # --- PASPOORT VIEW (PUBLIEK) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"""
            <div class="passport-card">
                <img src="{LOGO_URL}" style="height: 90px; margin-bottom: 25px;">
                <h1 style="margin-top: 0;">{d['name']}</h1>
                <p style="color: #666;">Geverifieerde fabrikant: <strong>{d['manufacturer']}</strong></p>
                <div style="display: flex; justify-content: space-around; margin-top: 40px; border-top: 1px solid #f5f5f5; padding-top: 30px;">
                    <div><p style="font-size:0.8em; margin:0; color:#999; letter-spacing:1px;">CO2 IMPACT</p><h2>{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.8em; margin:0; color:#999; letter-spacing:1px;">RECYCLED</p><h2>{d['recycled_content']}%</h2></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- INLOG SCHERM (CENTRALE KOLOM) ---
    if not st.session_state.company:
        # Start de centrale container
        st.markdown(f'<div class="central-container">', unsafe_allow_html=True)
        
        # Logo perfect bovenaan
        st.markdown(f'<img src="{LOGO_URL}" class="centered-logo">', unsafe_allow_html=True)
        
        # Inlogvelden (gebruikersnaam en wachtwoord)
        username = st.text_input("Username", placeholder="Gebruikersnaam", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        
        if st.button("Inloggen"):
            with httpx.Client() as client:
                resp = client.get(f"{API_URL_COMPANIES}?name=eq.{username}", headers=headers)
                if resp.status_code == 200 and len(resp.json()) > 0:
                    match = resp.json()[0]
                    if match['password'] == password:
                        st.session_state.company = match['name']
                        st.rerun()
                    else:
                        st.error("Wachtwoord onjuist.")
                else:
                    st.error("Gebruikersnaam niet herkend.")
        
        # Sluit de centrale container
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # --- DASHBOARD (Bedrijven / SuperAdmin) ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150)
        st.sidebar.divider()
        st.sidebar.write(f"Sessie: **{user}**")
        if st.sidebar.button("🚪 Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Global Overzicht", "🏢 Beheer Bedrijven"])
            with t1:
                all_bats = get_data(API_URL_BATTERIES)
                if all_bats: st.dataframe(pd.DataFrame(all_bats), use_container_width=True, hide_index=True)
            with t2:
                cos = get_data(API_URL_COMPANIES)
                if cos: st.table(pd.DataFrame(cos)[['name', 'password']])
                with st.form("new_co"):
                    n, p = st.text_input("Nieuw Bedrijf"), st.text_input("Wachtwoord")
                    if st.form_submit_button("Account aanmaken"):
                        httpx.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.rerun()
        else:
            st.title(f"Welkom, {user}")
            t1, t2 = st.tabs(["✨ Registratie", "📊 Mijn Voorraad"])
            with t1:
                with st.form("add_product"):
                    name = st.text_input("Modelnaam")
                    co2 = st.number_input("CO2 (kg)", min_value=0.0)
                    rec = st.slider("Recycled %", 0, 100, 25)
                    if st.form_submit_button("Product Opslaan"):
                        httpx.post(API_URL_BATTERIES, json={"name":name, "manufacturer":user, "carbon_footprint":co2, "recycled_content":rec}, headers=headers)
                        st.success("Product is succesvol geregistreerd!")
            with t2:
                my_bats = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if my_bats: st.dataframe(pd.DataFrame(my_bats)[['id','name','carbon_footprint','recycled_content']], use_container_width=True, hide_index=True)
