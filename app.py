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
COLOR_BG_BROKEN_WHITE = "#FDFBF7" # Exacte kleur van jouw logo

# JOUW LOGO LINK
LOGO_URL = "https://i.postimg.cc/sXHV1JHy/Chat-GPT-Image-28-dec-2025-14-50-31.png"

st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. ELIMINEER DE "BARS" (CSS) ---
st.markdown(f"""
    <style>
    /* Achtergrond overal gelijk maken aan logo */
    .stApp {{
        background-color: {COLOR_BG_BROKEN_WHITE};
    }}

    /* Verberg Streamlit UI elementen voor een app-ervaring */
    header, footer {{visibility: hidden;}}
    
    /* Titels */
    h1, h2, h3 {{ 
        color: {COLOR_ACCENT} !important; 
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
    }}

    /* LOGIN WRAPPER: Geen kaarten of extra randen, gewoon schone flow */
    .login-wrapper {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        max-width: 400px;
        padding-top: 5vh;
    }}
    
    /* Logo nog groter en perfect gecentreerd */
    .login-logo-img {{
        display: block;
        height: 240px; 
        width: auto;
        margin-bottom: 20px;
    }}

    /* Verwijder de "balk-in-een-balk" effecten van Streamlit */
    div[data-baseweb="input"] {{
        background-color: white !important;
        border: 1px solid #e8e6e1 !important;
        border-radius: 12px !important;
        padding: 4px !important;
    }}
    
    .stTextInput input {{
        background-color: white !important;
        border: none !important;
        font-size: 16px !important;
    }}

    /* De knop - Strakker en zonder randen */
    .stButton button {{
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        border: none !important;
        height: 50px !important;
        width: 100% !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        margin-top: 10px !important;
        box-shadow: 0 4px 15px rgba(143, 175, 154, 0.2);
    }}

    /* PASPOORT KAART (Consument) */
    .passport-card {{
        background-color: white;
        padding: 50px;
        border-radius: 24px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.03);
        text-align: center;
        max-width: 600px;
        margin: 50px auto;
        border: 1px solid #f0efeb;
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
    # --- PASPOORT VIEW (Consument) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"""
            <div class="passport-card">
                <img src="{LOGO_URL}" style="height: 100px; margin-bottom: 20px;">
                <h3 style="margin:0; opacity:0.4; font-size: 0.8em; letter-spacing: 3px;">DIGITAL PRODUCT PASSPORT</h3>
                <h1 style="margin-top: 15px; font-size: 2.8em;">{d['name']}</h1>
                <p style="color: #666; font-size: 1.2em;">Fabrikant: <strong>{d['manufacturer']}</strong></p>
                <div style="display: flex; justify-content: space-around; margin-top: 40px; border-top: 1px solid #f0f0f0; padding-top: 30px;">
                    <div><p style="font-size:0.8em; margin:0; color:#999; letter-spacing:1px;">CO2 VOETAFDRUK</p><h2>{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.8em; margin:0; color:#999; letter-spacing:1px;">RECYCLED</p><h2>{d['recycled_content']}%</h2></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Informatie niet gevonden.")

else:
    # --- INLOG SCHERM (ZONDER DROPDOWN) ---
    if not st.session_state.company:
        st.markdown(f'<div class="login-wrapper">', unsafe_allow_html=True)
        st.markdown(f'<img src="{LOGO_URL}" class="login-logo-img">', unsafe_allow_html=True)
        
        # Geen selectbox meer, maar een directe username input
        username_input = st.text_input("Username", placeholder="Gebruikersnaam", label_visibility="collapsed")
        pwd_input = st.text_input("Wachtwoord", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        
        if st.button("Inloggen"):
            # We zoeken in de database naar het bedrijf dat MATCHT met de ingevoerde naam
            with httpx.Client() as client:
                resp = client.get(f"{API_URL_COMPANIES}?name=eq.{username_input}", headers=headers)
                if resp.status_code == 200 and len(resp.json()) > 0:
                    match = resp.json()[0]
                    if match['password'] == pwd_input:
                        st.session_state.company = match['name']
                        st.rerun()
                    else:
                        st.error("Wachtwoord onjuist.")
                else:
                    st.error("Gebruikersnaam niet bekend.")
        
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
                if cos: st.table(pd.DataFrame(cos)[['name', 'password']])
                with st.form("new_co"):
                    n, p = st.text_input("Nieuw Bedrijf"), st.text_input("Wachtwoord")
                    if st.form_submit_button("Voeg Bedrijf Toe"):
                        httpx.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.rerun()
        else:
            st.title(f"Welkom, {user}")
            t1, t2 = st.tabs(["✨ Registratie", "📊 Voorraad"])
            with t1:
                with st.form("add"):
                    name = st.text_input("Model")
                    co2 = st.number_input("CO2 Impact (kg)", min_value=0.0)
                    rec = st.slider("Recycled %", 0, 100, 25)
                    if st.form_submit_button("Opslaan"):
                        httpx.post(API_URL_BATTERIES, json={"name":name, "manufacturer":user, "carbon_footprint":co2, "recycled_content":rec}, headers=headers)
                        st.success("Product geregistreerd!")
            with t2:
                my_bats = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if my_bats: st.dataframe(pd.DataFrame(my_bats)[['id','name','carbon_footprint','recycled_content']], use_container_width=True, hide_index=True)
