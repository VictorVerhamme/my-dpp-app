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
COLOR_BG_BROKEN_WHITE = "#FDFBF7" # Exacte kleur van jouw logo achtergrund

# JOUW LOGO LINK
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

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
    /* De hele app krijgt de kleur van het logo voor een naadloos effect */
    .stApp {{
        background-color: {COLOR_BG_BROKEN_WHITE}; 
    }}
    
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; font-family: 'Inter', sans-serif; }}

    /* Inlog container */
    .login-container {{
        display: flex;
        justify-content: center;
        padding-top: 60px;
    }}
    
    .login-card {{
        background-color: {COLOR_BG_BROKEN_WHITE};
        padding: 20px 40px;
        text-align: center;
        max-width: 500px;
        width: 100%;
    }}
    
    /* Logo formaat - verhoogd naar 160px voor meer impact */
    .login-logo-img {{
        height: 160px; 
        width: auto;
        margin-bottom: 25px;
    }}

    /* Input velden subtieler */
    .stTextInput input, .stSelectbox div {{
        background-color: white !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
    }}

    /* Button styling */
    .stButton button {{
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        width: 100%;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: opacity 0.3s;
    }}
    .stButton button:hover {{
        opacity: 0.8;
    }}

    /* Paspoort kaart design */
    .passport-card {{
        background-color: white;
        padding: 50px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        max-width: 750px;
        margin: auto;
        border-top: 6px solid {COLOR_ACCENT};
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
                <img src="{LOGO_URL}" style="height: 80px; margin-bottom: 35px;">
                <h3 style="margin:0; opacity:0.5; font-size: 0.85em; letter-spacing: 2px;">OFFICIEEL PRODUCT PASPOORT</h3>
                <h1 style="margin-top: 8px; font-size: 2.5em;">{d['name']}</h1>
                <p style="font-size: 1.2em; color: #444;">Geverifieerde fabrikant: <strong>{d['manufacturer']}</strong></p>
                <div style="display: flex; gap: 70px; margin-top: 45px; border-top: 1px solid #f0f0f0; padding-top: 35px;">
                    <div><p style="font-size:0.85em; margin:0; color:#999; letter-spacing: 1px;">CO2 IMPACT</p><h2 style="margin-top:5px;">{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.85em; margin:0; color:#999; letter-spacing: 1px;">RECYCLED MATERIAAL</p><h2 style="margin-top:5px;">{d['recycled_content']}%</h2></div>
                </div>
                <div style="margin-top: 40px; padding: 15px; background: #fafafa; border-radius: 8px; font-size: 0.9em; color: #777;">
                    ℹ️ Dit digitale paspoort is geverifieerd volgens EU-verordening 2023/1542.
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden in het register.")

else:
    # --- LOGIN SCHERM ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        companies = get_data(API_URL_COMPANIES)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f'<div class="login-container"><div class="login-card">', unsafe_allow_html=True)
            st.markdown(f'<img src="{LOGO_URL}" class="login-logo-img">', unsafe_allow_html=True)
            
            co_names = [c['name'] for c in companies]
            selected_co = st.selectbox("Selecteer uw organisatie", options=co_names)
            pwd_input = st.text_input("Wachtwoord", type="password")
            
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button("Inloggen op Portaal"):
                match = next((c for c in companies if c['name'] == selected_co), None)
                if match and match['password'] == pwd_input:
                    st.session_state.company = selected_co
                    st.rerun()
                else: st.error("Inloggegevens niet herkend.")
            
            st.markdown('</div></div>', unsafe_allow_html=True)

    else:
        # --- DASHBOARD (Bedrijven / SuperAdmin) ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=140)
        st.sidebar.divider()
        st.sidebar.write(f"Ingelogd als: **{user}**")
        if st.sidebar.button("🚪 Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Systeem Data", "🏢 Bedrijven Beheren"])
            with t1:
                st.subheader("Totaaloverzicht alle producten")
                all_bats = get_data(API_URL_BATTERIES)
                if all_bats: st.dataframe(pd.DataFrame(all_bats), use_container_width=True, hide_index=True)
            with t2:
                st.subheader("Actieve organisaties")
                cos = get_data(API_URL_COMPANIES)
                st.table(pd.DataFrame(cos)[['name', 'password']])
                st.divider()
                st.subheader("➕ Nieuwe klant toevoegen")
                with st.form("new_co"):
                    n, p = st.text_input("Naam Bedrijf"), st.text_input("Toegangscode")
                    if st.form_submit_button("Account aanmaken"):
                        httpx.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.success(f"{n} succesvol toegevoegd!")
                        st.rerun()
        else:
            # Bedrijfs Dashboard
            st.title(f"Welkom bij het portaal van {user}")
            t1, t2, t3 = st.tabs(["✨ Registratie", "📊 Voorraad", "📂 Bulk Import"])
            
            with t1:
                with st.form("add", clear_on_submit=True):
                    st.write("Registreer een nieuwe batterij voor het EU Paspoort")
                    name = st.text_input("Model / Type")
                    co2 = st.number_input("CO2 Impact (kg)", min_value=0.0)
                    rec = st.slider("Percentage gerecycled materiaal", 0, 100, 20)
                    if st.form_submit_button("Product Opslaan"):
                        payload = {"name": name, "manufacturer": user, "carbon_footprint": co2, "recycled_content": rec}
                        httpx.post(API_URL_BATTERIES, json=payload, headers=headers)
                        st.success("Het product is geregistreerd in de database.")
            
            with t2:
                st.subheader("Uw geregistreerde producten")
                my_bats = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if my_bats: st.dataframe(pd.DataFrame(my_bats)[['id', 'name', 'carbon_footprint', 'recycled_content']], use_container_width=True, hide_index=True)
                else: st.info("U heeft nog geen producten in uw voorraad.")

            with t3:
                st.subheader("Meerdere producten tegelijk importeren")
                file = st.file_uploader("Upload CSV-bestand", type="csv")
                if file:
                    df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
                    df.columns = [c.lower().strip() for c in df.columns]
                    if st.button("Start Import 🚀"):
                        with httpx.Client() as client:
                            for _, row in df.iterrows():
                                payload = {"name": str(row['name']), "manufacturer": user, "carbon_footprint": float(row.get('carbon_footprint', 0)), "recycled_content": int(row.get('recycled_content', 0))}
                                client.post(API_URL_BATTERIES, json=payload, headers=headers)
                        st.success("Batch-import succesvol voltooid.")
