import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_BROKEN_WHITE = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- PDF GENERATOR ---
def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 20, txt="EU Digital Product Passport", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Product: {data['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Fabrikant: {data['manufacturer']}", ln=True)
    pdf.cell(200, 10, txt=f"CO2 Voetafdruk: {data['carbon_footprint']} kg", ln=True)
    pdf.cell(200, 10, txt=f"Recycled: {data['recycled_content']}%", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- HELPERS ---
def get_data(url):
    with httpx.Client() as client:
        r = client.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []

def delete_item(item_id):
    with httpx.Client() as client:
        # We gebruiken een specifieke DELETE request
        resp = client.delete(f"{API_URL_BATTERIES}?id=eq.{item_id}", headers=headers)
        if resp.status_code in [200, 204]:
            st.success("Verwijderd!")
            st.rerun()
        else:
            st.error(f"Fout bij verwijderen: {resp.text}")

# --- STYLING ---
st.markdown(f"<style>.stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }} header, footer {{visibility: hidden;}} h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}</style>", unsafe_allow_html=True)

# --- LOGICA ---
query_params = st.query_params

if "id" in query_params:
    # CONSUMENTEN VIEW
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        new_views = (d.get('views') or 0) + 1
        httpx.patch(f"{API_URL_BATTERIES}?id=eq.{d['id']}", json={"views": new_views}, headers=headers)
        st.markdown(f"<div style='background:white; padding:50px; border-radius:20px; text-align:center; border-top:8px solid {COLOR_ACCENT}'><h1>{d['name']}</h1><p>Fabrikant: {d['manufacturer']}</p><h2>{d['carbon_footprint']} kg CO2</h2></div>", unsafe_allow_html=True)
else:
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        # LOGIN SCHERM (Centraal)
        _, col, _ = st.columns([1.2, 1, 1.2])
        with col:
            st.image(LOGO_URL)
            u = st.text_input("Username", placeholder="Naam")
            p = st.text_input("Password", type="password")
            if st.button("Inloggen"):
                res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
                if res and res[0]['password'] == p:
                    st.session_state.company = res[0]['name']
                    st.rerun()
    else:
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150)
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Systeem Data", "🏢 Bedrijven"])
            with t1:
                df = pd.DataFrame(get_data(API_URL_BATTERIES))
                if not df.empty:
                    st.dataframe(df[['id', 'name', 'manufacturer', 'views']], use_container_width=True)
                    target = st.text_input("ID om te wissen")
                    if st.button("Wis uit database"): delete_item(target)
            with t2:
                st.table(pd.DataFrame(get_data(API_URL_COMPANIES))[['name', 'password']])
        else:
            # BEDRIJFS DASHBOARD
            st.title(f"Welkom, {user}")
            t1, t2 = st.tabs(["✨ Registratie", "📊 Voorraadbeheer"])
            
            with t1:
                with st.form("add"):
                    n = st.text_input("Model")
                    c = st.number_input("CO2 Impact", min_value=0.0)
                    r = st.slider("Recycled %", 0, 100)
                    if st.form_submit_button("Opslaan"):
                        httpx.post(API_URL_BATTERIES, json={"name":n, "manufacturer":user, "carbon_footprint":c, "recycled_content":r}, headers=headers)
                        st.success("Geregistreerd!")
            
            with t2:
                # 1. SNEL OVERZICHT (Tabel)
                data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if data:
                    df = pd.DataFrame(data)
                    st.subheader("Uw Batterijen")
                    st.dataframe(df[['id', 'name', 'carbon_footprint', 'recycled_content', 'views']], use_container_width=True, hide_index=True)
                    
                    # 2. ACTIES (Selecteer één batterij voor PDF of Verwijderen)
                    st.divider()
                    st.subheader("Acties")
                    selected_name = st.selectbox("Kies een batterij voor acties", options=df['name'].tolist())
                    selected_item = df[df['name'] == selected_name].iloc[0]
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        pdf_bytes = generate_certificate(selected_item)
                        st.download_button(f"📥 Download PDF: {selected_name}", pdf_bytes, f"{selected_name}.pdf")
                    with col_b:
                        if st.button(f"🗑️ Verwijder {selected_name}"):
                            delete_item(selected_item['id'])
                else:
                    st.info("Nog geen voorraad.")
