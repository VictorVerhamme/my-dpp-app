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

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_BROKEN_WHITE = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="DPP Compliance Engine", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. HELPERS ---
def make_qr(battery_id):
    url = f"https://digitalpassport.streamlit.app/?id={battery_id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 10, txt="EU Digital Product Passport - Compliance Audit", ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Identificatie blok
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 8, txt="Wettelijke Product-Identificatie", ln=True, fill=True)
    
    fields = [
        ("Unieke Batterij ID (UUID)", data.get('id')),
        ("Model Naam", data.get('name')),
        ("Fabrikant", data.get('manufacturer')),
        ("Productie Datum", data.get('production_date')),
        ("Gewicht (kg)", data.get('weight_kg')),
        ("Capaciteit (kWh)", data.get('nominal_capacity_kwh')),
        ("Chemie", data.get('chemistry')),
        ("CO2 Voetafdruk", f"{data.get('carbon_footprint')} kg CO2-eq"),
        ("Recycled Lithium", f"{data.get('rec_lithium_pct')}%"),
        ("EPR Nummer", data.get('epr_number')),
        ("CE Conformiteit", "JA" if data.get('ce_status') else "NEE")
    ]
    
    for label, val in fields:
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(60, 7, txt=f"{label}:", border=1)
        pdf.set_font("Arial", '', 9)
        pdf.cell(130, 7, txt=str(val or 'N/A'), border=1, ln=True)

    # QR Code toevoegen
    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img_bytes)
        tmp_path = tmp.name
    
    try:
        pdf.ln(10)
        pdf.image(tmp_path, x=75, y=pdf.get_y(), w=40)
        pdf.ln(45)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(190, 5, txt=f"Gegenereerd op: {datetime.now().strftime('%Y-%m-%d %H:%M')} | DPP Versie: {data.get('dpp_version')}", align='C')
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except:
        return []

# --- 3. STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    .stButton button {{
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        border-radius: 8px !important;
    }}
    .compliance-card {{
        background: white; padding: 25px; border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 5px solid {COLOR_ACCENT};
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. APP LOGICA ---
q_params = st.query_params
if "id" in q_params:
    # --- PASPOORT VIEW (Consument & Autoriteit) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        st.markdown('<div class="compliance-card">', unsafe_allow_html=True)
        col_logo, col_title = st.columns([1, 4])
        with col_logo: st.image(LOGO_URL, width=100)
        with col_title: st.title(f"Digitaal Paspoort: {d.get('name')}")
        
        st.divider()
        
        # Keuze tussen Consument en Autoriteit (Simulatie van Role-Based Access)
        view_mode = st.radio("Weergave modus", ["Consument", "Inspectie / Autoriteit"], horizontal=True)
        
        if view_mode == "Consument":
            c1, c2, c3 = st.columns(3)
            c1.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint')} kg")
            c2.metric("Lithium Recycled", f"{d.get('rec_lithium_pct')}%")
            c3.metric("State of Health", f"{d.get('soh_pct')}%")
            
            st.info(f"**Herkomst materialen:** {d.get('mineral_origin')}")
            st.success(f"**Circulariteit:** Dit product is geclassificeerd voor: {d.get('eol_route')}")
        
        else:
            st.warning("⚠️ U bekijkt nu de wettelijk verplichte data voor markttoezicht.")
            st.json(d)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("Ongeldige QR-code of Paspoort niet gevonden.")

else:
    # --- LOGIN & DASHBOARD ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        st.markdown('<div style="max-width:400px; margin: 0 auto; padding-top:100px;">', unsafe_allow_html=True)
        st.image(LOGO_URL)
        u = st.text_input("Fabrikant Naam")
        p = st.text_input("Wachtwoord", type="password")
        if st.button("Inloggen", use_container_width=True):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']
                st.rerun()
            else: st.error("Inloggegevens onjuist.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        user = st.session_state.company
        st.sidebar.image(LOGO_URL)
        st.sidebar.title(f"Welkom, {user}")
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        st.title(f"DPP Management Dashboard")
        tab1, tab2 = st.tabs(["🆕 Nieuwe Registratie", "📊 Inventaris & Export"])

        with tab1:
            with st.form("compliance_wizard"):
                st.subheader("Wettelijk Verplichte Velden (EU 2023/1542)")
                c1, c2 = st.columns(2)
                with c1:
                    f_name = st.text_input("Productnaam / Model")
                    f_weight = st.number_input("Gewicht Batterij (kg)", min_value=0.0)
                    f_cap = st.number_input("Nominale Capaciteit (kWh)", min_value=0.0)
                    f_type = st.selectbox("Batterij Categorie", ["EV", "LMT", "Industrieel", "Draagbaar"])
                    f_chem = st.text_input("Chemische Samenstelling (bijv. Li-NMC)")
                with c2:
                    f_prod_date = st.date_input("Productie Datum")
                    f_epr = st.text_input("EPR Registratienummer")
                    f_co2 = st.number_input("Carbon Footprint (kg CO2-eq)", min_value=0.0)
                    f_li = st.slider("% Recycled Lithium", 0, 100, 6)
                    f_audit = st.checkbox("Due Diligence Audit Voltooid")

                st.divider()
                if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                    if f_li < 6:
                        st.error("❌ Validatiefout: Minimum 6% recycled Lithium vereist voor EU-conformiteit (2027 norm).")
                    else:
                        payload = {
                            "id": str(uuid.uuid4()),
                            "name": f_name,
                            "manufacturer": user,
                            "weight_kg": f_weight,
                            "nominal_capacity_kwh": f_cap,
                            "battery_type": f_type,
                            "chemistry": f_chem,
                            "production_date": str(f_prod_date),
                            "carbon_footprint": f_co2,
                            "rec_lithium_pct": f_li,
                            "epr_number": f_epr,
                            "due_diligence_audit": f_audit,
                            "soh_pct": 100,
                            "dpp_version": "1.1.0"
                        }
                        with httpx.Client() as client:
                            resp = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if resp.status_code == 201:
                                st.success("✅ Product succesvol geregistreerd in de blockchain/database!")
                                st.balloons()
                            else: st.error(f"Fout: {resp.text}")

        with tab2:
            raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}&order=created_at.desc")
            if raw_data:
                df = pd.DataFrame(raw_data)
                st.dataframe(df[['id', 'name', 'production_date', 'weight_kg']], use_container_width=True)
                
                sel_name = st.selectbox("Selecteer product voor acties", df['name'].tolist())
                item = df[df['name'] == sel_name].iloc[0]
                
                c_pdf, c_json, c_del = st.columns(3)
                c_pdf.download_button("📥 Download Audit PDF", generate_certificate(item), f"DPP_Audit_{sel_name}.pdf")
                c_json.download_button("🤖 Download JSON (Inspectie)", df[df['name']==sel_name].to_json(), f"DPP_{sel_name}.json")
                if c_del.button("🗑️ Verwijder uit Systeem"):
                    httpx.delete(f"{API_URL_BATTERIES}?id=eq.{item['id']}", headers=headers)
                    st.rerun()
            else: st.info("Geen producten gevonden.")
