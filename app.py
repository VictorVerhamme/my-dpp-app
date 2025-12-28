import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO

# --- CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_CARD = "#E3ECE6" # Lichtgroen

st.set_page_config(page_title="EU Battery Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #fdfdfd; }}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    .passport-card {{ background-color: {COLOR_BG_CARD}; border-radius: 12px; padding: 40px; border-left: 8px solid {COLOR_ACCENT}; }}
    .login-box {{ background-color: {COLOR_BG_CARD}; padding: 30px; border-radius: 15px; border: 1px solid {COLOR_ACCENT}; }}
    </style>
""", unsafe_allow_html=True)

# --- FUNCTIE: HAAL BEDRIJVEN OP ---
def get_all_companies():
    with httpx.Client() as client:
        resp = client.get(API_URL_COMPANIES, headers=headers)
        return resp.json() if resp.status_code == 200 else []

# --- LOGICA ---
query_params = st.query_params

if "id" in query_params:
    # --- CONSUMENTEN VIEW ---
    battery_id = query_params["id"]
    with httpx.Client() as client:
        resp = client.get(f"{API_URL_BATTERIES}?id=eq.{battery_id}", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            data = resp.json()[0]
            st.markdown(f"""
                <div class="passport-card">
                    <p style="color:{COLOR_ACCENT}; font-weight:bold; margin-bottom:0;">OFFICIEEL EU PASPOORT</p>
                    <h1>🔋 {data['name']}</h1>
                    <p>Fabrikant: <strong>{data['manufacturer']}</strong></p>
                    <hr style="border: 0.5px solid {COLOR_ACCENT}; opacity: 0.3;">
                    <div style="display: flex; gap: 50px; margin-top: 20px;">
                        <div><p style="margin:0; font-size: 0.8em;">CO2 IMPACT</p><h2>{data['carbon_footprint']} kg</h2></div>
                        <div><p style="margin:0; font-size: 0.8em;">RECYCLED</p><h2>{data['recycled_content']}%</h2></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

else:
    # --- LOGIN LOGICA ---
    if 'logged_in_company' not in st.session_state:
        st.session_state.logged_in_company = None

    if not st.session_state.logged_in_company:
        companies = get_all_companies()
        company_names = [c['name'] for c in companies]
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.subheader("Bedrijfs Portaal")
            selected_co = st.selectbox("Selecteer uw bedrijf", options=company_names)
            pwd_input = st.text_input("Wachtwoord", type="password")
            if st.button("Inloggen"):
                # Check wachtwoord in de database lijst
                match = next((c for c in companies if c['name'] == selected_co), None)
                if match and match['password'] == pwd_input:
                    st.session_state.logged_in_company = selected_co
                    st.rerun()
                else:
                    st.error("Onjuist wachtwoord")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        # --- DASHBOARD ---
        user = st.session_state.logged_in_company
        st.sidebar.title(f"👤 {user}")
        if st.sidebar.button("Uitloggen"):
            st.session_state.logged_in_company = None
            st.rerun()

        # SUPER ADMIN VS GEWOON BEDRIJF
        if user == "SuperAdmin":
            tabs = st.tabs(["📊 Global Overzicht", "🏢 Bedrijven Beheren", "✨ Nieuwe Batterij"])
            
            with tabs[0]:
                st.subheader("Alle batterijen van alle bedrijven")
                with httpx.Client() as client:
                    resp = client.get(API_URL_BATTERIES, headers=headers)
                    if resp.status_code == 200:
                        st.dataframe(pd.DataFrame(resp.json()), use_container_width=True)

            with tabs[1]:
                st.subheader("Bedrijfsbeheer")
                # Lijst van bedrijven en wachtwoorden
                companies = get_all_companies()
                st.table(pd.DataFrame(companies)[['name', 'password']])
                
                st.divider()
                st.subheader("➕ Nieuw Bedrijf Toevoegen")
                with st.form("add_company"):
                    new_co_name = st.text_input("Naam Bedrijf")
                    new_co_pwd = st.text_input("Wachtwoord voor dit bedrijf")
                    if st.form_submit_button("Opslaan"):
                        with httpx.Client() as client:
                            client.post(API_URL_COMPANIES, json={"name": new_co_name, "password": new_co_pwd}, headers=headers)
                        st.success(f"{new_co_name} is toegevoegd!")
                        st.rerun()

        else:
            # Dashboard voor gewone bedrijven
            tabs = st.tabs(["✨ Nieuwe Batterij", "📊 Mijn Voorraad", "📂 Bulk Upload"])
            # ... (Rest van de bekende code voor batterijen toevoegen)
