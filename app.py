import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile
import os
import uuid
from datetime import datetime

# --- CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A" 
COLOR_BG_BROKEN_WHITE = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="DPP Hub - Regulatory Compliance", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- HELPERS ---
def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- APP LOGICA ---
q_params = st.query_params
if "id" in q_params:
    # PASPOORT VIEW (PUBLIEK)
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        st.title(f"🔋 Digital Product Passport")
        st.subheader(f"Model: {d.get('name')}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Recycled Lithium", f"{d.get('rec_lithium_pct')}%")
        col2.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint')} kg")
        col3.metric("State of Health", f"{d.get('soh_pct')}%")
        
        with st.expander("📝 Volledige Specificaties (Wettelijk)"):
            st.write(f"**Fabrikant:** {d.get('manufacturer')}")
            st.write(f"**Productiedatum:** {d.get('production_date')}")
            st.write(f"**Gewicht:** {d.get('weight_kg')} kg")
            st.write(f"**Chemie:** {d.get('chemistry')}")
    else: st.error("Paspoort niet gevonden.")

else:
    # DASHBOARD VOOR FABRIKANTEN
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        st.title("Inloggen DPP Hub")
        u = st.text_input("Gebruikersnaam")
        p = st.text_input("Wachtwoord", type="password")
        if st.button("Login"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']
                st.rerun()
    else:
        user = st.session_state.company
        st.title(f"Compliance Dashboard: {user}")
        
        tab1, tab2 = st.tabs(["📋 Nieuwe Registratie", "📦 Mijn Producten"])
        
        with tab1:
            with st.form("wizard"):
                st.markdown("### 1. Product & Identificatie")
                c1, c2 = st.columns(2)
                f_name = c1.text_input("Model Naam")
                f_weight = c2.number_input("Gewicht (kg)", min_value=0.0)
                f_cap = c1.number_input("Nominale Capaciteit (kWh)", min_value=0.0)
                f_date = c2.date_input("Productie Datum")
                
                st.markdown("### 2. Recycled Content (%) - *EU 2027 Normen*")
                r1, r2, r3, r4 = st.columns(4)
                f_li = r1.number_input("Lithium", 0.0, 100.0, 6.0)
                f_co = r2.number_input("Kobalt", 0.0, 100.0, 16.0)
                f_ni = r3.number_input("Nikkel", 0.0, 100.0, 6.0)
                f_pb = r4.number_input("Lood", 0.0, 100.0, 85.0)
                
                st.markdown("### 3. Milieu & Conformiteit")
                f_co2 = st.number_input("Carbon Footprint (kg CO2-eq)", 0.0)
                f_origin = st.text_area("Herkomst Grondstoffen (Due Diligence)")
                
                if st.form_submit_button("Valideer & Publiceer naar DPP"):
                    # Compliance check
                    if f_li < 6.0:
                        st.error("❌ Lithium gehalte is lager dan de EU 2027 eis (6%).")
                    else:
                        payload = {
                            "id": str(uuid.uuid4()),
                            "name": f_name,
                            "manufacturer": user,
                            "weight_kg": f_weight,
                            "nominal_capacity_kwh": f_cap,
                            "production_date": str(f_date),
                            "rec_lithium_pct": f_li,
                            "rec_cobalt_pct": f_co,
                            "rec_nickel_pct": f_ni,
                            "rec_lead_pct": f_pb,
                            "carbon_footprint": f_co2,
                            "mineral_origin": f_origin,
                            "soh_pct": 100
                        }
                        with httpx.Client() as client:
                            resp = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if resp.status_code == 201:
                                st.success(f"✅ DPP voor {f_name} is live!")
                                st.balloons()
                            else: st.error(f"DB Fout: {resp.text}")

        with tab2:
            items = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
            if items:
                df = pd.DataFrame(items)
                st.dataframe(df[['name', 'production_date', 'weight_kg']])
            else: st.info("Nog geen producten geregistreerd.")
