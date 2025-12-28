import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile
from datetime import datetime

# --- 1. CONFIGURATIE & NORMAN ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"
COLOR_BG_BROKEN_WHITE = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

# EU WETTELIJKE MINIMA (Voorbeeld voor 2027/2031 normen)
MIN_RECYCLED_LI = 6.0  # %
MIN_RECYCLED_CO = 16.0 # %
MIN_RECYCLED_NI = 6.0  # %

st.set_page_config(page_title="DPP | Compliance Engine", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. COMPLIANCE CHECK FUNCTIE ---
def check_compliance(data):
    errors = []
    warnings = []
    
    # Check Recycled Lithium
    if data['rec_li'] < MIN_RECYCLED_LI:
        errors.append(f"❌ Lithium gehalte ({data['rec_li']}%) is lager dan de EU-norm voor 2027 ({MIN_RECYCLED_LI}%).")
    
    # Check Recycled Cobalt
    if data['rec_co'] < MIN_RECYCLED_CO:
        errors.append(f"❌ Kobalt gehalte ({data['rec_co']}%) voldoet niet aan de minimale eis van {MIN_RECYCLED_CO}%.")

    # Check Carbon Footprint status
    if data['co2'] > 150.0: # Fictieve drempelwaarde
        warnings.append("⚠️ Let op: De CO2-voetafdruk is hoog. Dit kan leiden tot extra belastingen of beperkingen.")

    if not data['ce_status']:
        errors.append("❌ CE-Conformiteit is verplicht voor markttoelating in de EU.")

    return errors, warnings

# --- 3. HELPERS (QR, PDF, DATA) ---
def make_qr(id):
    url = f"https://digitalpassport.streamlit.app/?id={id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 20, txt="EU Compliance Certificate - DPP", ln=True, align='C')
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(100, 8, txt=f"Product: {data.get('name', 'N/A')}", ln=True)
    pdf.cell(100, 8, txt=f"Fabrikant: {data.get('manufacturer', 'N/A')}", ln=True)
    pdf.cell(100, 8, txt=f"CO2 Impact: {data.get('carbon_footprint', '0')} kg CO2e", ln=True)
    
    qr_img = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img)
        pdf.image(tmp.name, x=70, y=pdf.get_y()+10, w=60)
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 4. STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }}
    header, footer {{visibility: hidden;}}
    .central-container {{ max-width: 420px; margin: 0 auto; padding-top: 10vh; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGICA ---
if 'company' not in st.session_state: st.session_state.company = None

q_params = st.query_params
if "id" in q_params:
    # --- CONSUMENTEN VIEW ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"<div style='background:white; padding:50px; border-radius:25px; text-align:center; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-top:8px solid {COLOR_ACCENT}'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=150)
        st.title(d['name'])
        st.subheader(f"Geregistreerd door {d['manufacturer']}")
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint', 0)} kg")
        c2.metric("Recycled Content", f"{d.get('recycled_content', 0)}%")
        st.markdown("</div>", unsafe_allow_html=True)
    else: st.error("ID niet gevonden.")

else:
    if not st.session_state.company:
        # LOGIN
        st.markdown('<div class="central-container">', unsafe_allow_html=True)
        st.image(LOGO_URL, width=350)
        u = st.text_input("Username", placeholder="Naam organisatie", label_visibility="collapsed")
        p = st.text_input("Password", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        if st.button("Inloggen op Portaal", use_container_width=True):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # DASHBOARD
        user = st.session_state.company
        st.sidebar.image(LOGO_URL)
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        st.title(f"Compliance Portaal: {user}")
        t_reg, t_stock = st.tabs(["✨ Nieuwe Registratie", "📊 Voorraad & Audit"])

        with t_reg:
            with st.form("compliance_form"):
                st.subheader("Stap 1: Basisgegevens & Identificatie")
                f_name = st.text_input("Modelnaam")
                f_chem = st.text_input("Chemische samenstelling (LFP, NMC, etc.)")
                
                st.divider()
                st.subheader("Stap 2: Milieu & Recycling")
                c1, c2, c3 = st.columns(3)
                f_co2 = c1.number_input("Carbon footprint (kg CO2-eq)", min_value=0.0)
                f_li = c2.number_input("% Recycled Lithium", min_value=0.0, max_value=100.0)
                f_co = c3.number_input("% Recycled Kobalt", min_value=0.0, max_value=100.0)
                
                st.divider()
                st.subheader("Stap 3: Juridische status")
                f_ce = st.checkbox("Ik bevestig de CE-conformiteit van dit product")
                f_epr = st.text_input("EPR Registratienummer")

                if st.form_submit_button("Product Valideren & Registreren", use_container_width=True):
                    # DATA VOOR DE CHECK
                    input_data = {
                        "rec_li": f_li,
                        "rec_co": f_co,
                        "co2": f_co2,
                        "ce_status": f_ce
                    }
                    
                    # UITVOEREN VAN DE COMPLIANCE CHECK
                    errs, warns = check_compliance(input_data)
                    
                    if errs:
                        for e in errs: st.error(e)
                        st.warning("⚠️ Registratie geblokkeerd: Het product voldoet niet aan de EU-minimumvereisten.")
                    else:
                        if warns: 
                            for w in warns: st.warning(w)
                        
                        # Payload voor database
                        payload = {
                            "name": f_name, "manufacturer": user, "chemistry": f_chem,
                            "carbon_footprint": f_co2, "recycled_content": (f_li + f_co)/2, # Vereenvoudigd
                            "ce_status": f_ce, "epr_number": f_epr, "views": 0
                        }
                        with httpx.Client() as client:
                            resp = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if resp.status_code == 201:
                                st.success("✅ Product gevalideerd en succesvol geregistreerd!")
                                st.balloons()

        with t_stock:
            data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df[['id', 'name', 'carbon_footprint', 'views']], use_container_width=True)
