import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile
import os

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

# --- 2. HELPERS (QR & PDF FIX) ---
def make_qr(id):
    url = f"https://digitalpassport.streamlit.app/?id={id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 15, txt="EU Digital Product Passport - Compliance Audit", ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Tabel met alle data
    pdf.set_fill_color(245, 247, 246)
    pdf.cell(190, 8, txt="Wettelijke Productgegevens", ln=True, align='L', fill=True)
    pdf.set_font("Arial", '', 9)
    
    fields = [
        ("Naam / Model", data.get('name')),
        ("Type", data.get('battery_type')),
        ("Chemie", data.get('chemistry')),
        ("CO2 Impact", f"{data.get('carbon_footprint')} kg CO2-eq"),
        ("EPR Nummer", data.get('epr_number')),
        ("CE Status", "Gecertificeerd" if data.get('ce_status') else "Niet Gecertificeerd"),
        ("Recycled Lithium", f"{data.get('rec_lithium_pct')}%"),
        ("State of Health", f"{data.get('soh_pct')}%"),
        ("Grondstof Herkomst", data.get('mineral_origin'))
    ]
    
    for label, val in fields:
        pdf.cell(60, 7, txt=f"{label}:", border=1)
        pdf.cell(130, 7, txt=str(val or 'N/A'), border=1, ln=True)

    # QR Code FIX: Veilig wegschrijven en sluiten voor FPDF
    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img_bytes)
        tmp_path = tmp.name
    
    try:
        pdf.ln(10)
        pdf.image(tmp_path, x=75, y=pdf.get_y(), w=50)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. STYLING (Gecentreerd & Schoon) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }}
    header, footer {{visibility: hidden;}}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    
    /* Login Centering */
    .login-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        max-width: 400px;
        margin: 0 auto;
        padding-top: 10vh;
    }}
    
    /* Button Centering */
    .stButton {{ display: flex; justify-content: center; }}
    .stButton button {{
        background-color: {COLOR_ACCENT} !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100% !important;
        max-width: 400px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. APP LOGICA ---
q_params = st.query_params
if "id" in q_params:
    # --- PASPOORT VIEW (Consument) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"<div style='background:white; padding:40px; border-radius:20px; text-align:center; border-top:8px solid {COLOR_ACCENT}'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=150)
        st.title(d.get('name', 'Product Paspoort'))
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint', 0)} kg")
        c2.metric("Lithium Recycled", f"{d.get('rec_lithium_pct', 0)}%")
        st.markdown("</div>", unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        # --- LOGIN SCHERM ---
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image(LOGO_URL, width=350)
        u = st.text_input("Gebruikersnaam", placeholder="Gebruikersnaam", label_visibility="collapsed")
        p = st.text_input("Wachtwoord", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        if st.button("Inloggen"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']
                st.rerun()
            else: st.error("Inloggegevens onjuist.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # --- DASHBOARD ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL)
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        st.title(f"Dashboard {user}")
        tab1, tab2 = st.tabs(["✨ Nieuwe Registratie", "📊 Voorraad & Export"])

        with tab1:
            st.info("Gebruik de Wizard om een product conform de EU-wetgeving aan te maken.")
            with st.form("compliance_wizard"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("##### 1. Identificatie")
                    f_name = st.text_input("Productnaam")
                    f_model = st.text_input("Model ID")
                    f_type = st.selectbox("Type", ["EV", "LMT", "Industrieel", "Draagbaar"])
                    f_chem = st.text_input("Chemie")
                with col2:
                    st.markdown("##### 2. Producent")
                    f_addr = st.text_input("Adres Fabriek")
                    f_epr = st.text_input("EPR Nummer")
                    f_ce = st.checkbox("CE Status", value=True)
                with col3:
                    st.markdown("##### 3. Milieu")
                    f_co2 = st.number_input("kg CO2-eq", min_value=0.0)
                    f_scope = st.selectbox("Scope", ["Cradle-to-gate", "Cradle-to-grave"])
                with col4:
                    st.markdown("##### 4. Recycled")
                    f_li = st.number_input("% Rec. Lithium", 0.0, 100.0)
                    f_co = st.number_input("% Rec. Kobalt", 0.0, 100.0)

                st.divider()
                col5, col6, col7, col8 = st.columns(4)
                with col5:
                    st.markdown("##### 5. Prestatie")
                    f_cap = st.number_input("Capaciteit (kWh)", min_value=0.0)
                    f_soh = st.slider("SoH (%)", 0, 100, 100)
                with col6:
                    st.markdown("##### 6. Circulariteit")
                    f_rem = st.checkbox("Verwijderbaar", value=True)
                    f_eol = st.selectbox("EOL Route", ["Recycling", "Reuse"])
                with col7:
                    st.markdown("##### 7. Due Diligence")
                    f_origin = st.text_area("Grondstof herkomst")
                    f_audit = st.checkbox("Audit uitgevoerd")
                with col8:
                    st.markdown("##### 8. DPP")
                    f_ver = st.text_input("Versie", "1.0.0")

                if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                    # Compliance Check
                    if f_li < 6.0:
                        st.error("❌ Lithium gehalte te laag (min. 6% vereist).")
                    else:
                        payload = {
                            "name": f_name, "manufacturer": user, "model_name": f_model,
                            "battery_type": f_type, "chemistry": f_chem, "carbon_footprint": f_co2,
                            "rec_lithium_pct": f_li, "rec_cobalt_pct": f_co, "ce_status": f_ce,
                            "epr_number": f_epr, "soh_pct": f_soh, "is_removable": f_rem,
                            "eol_route": f_eol, "mineral_origin": f_origin, "due_diligence_audit": f_audit,
                            "dpp_version": f_ver, "views": 0
                        }
                        with httpx.Client() as client:
                            resp = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if resp.status_code == 201:
                                st.success(f"✅ {f_name} geregistreerd!")
                                st.balloons()
                            else: st.error(f"Fout: {resp.text}")

        with tab2:
            st.subheader("Overzicht Geregistreerde Producten")
            raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
            
            if raw_data:
                df = pd.DataFrame(raw_data)
                
                # Uitgebreide lijst van kolommen voor een volledig overzicht
                display_cols = [
                    'id', 'name', 'model_name', 'battery_type', 'chemistry', 
                    'weight_kg', 'carbon_footprint', 'rec_lithium_pct', 
                    'rec_cobalt_pct', 'soh_pct', 'cycle_count', 
                    'ce_status', 'dpp_version', 'views'
                ]
                
                # We tonen alleen de kolommen die daadwerkelijk in de dataframe zitten
                existing_cols = [c for c in display_cols if c in df.columns]
                
                # De tabel met alle info
                st.dataframe(df[existing_cols], use_container_width=True, hide_index=True)
                
                st.divider()
                st.subheader("Acties & Detailaudit")
                
                # Selectie voor specifieke acties
                sel_name = st.selectbox("Product selecteren voor export of inspectie", df['name'].tolist())
                item = df[df['name'] == sel_name].iloc[0]
                
                col_info, col_qr = st.columns([2, 1])
                with col_info:
                    st.write(f"**Geselecteerd:** {sel_name}")
                    st.write(f"**Uniek ID (UUID):** {item.get('battery_uid', 'N/A')}")
                    st.write(f"**Productielocatie:** {item.get('manufacturer_address', 'N/A')}")
                    
                    st.markdown("---")
                    c_pdf, c_json, c_del = st.columns(3)
                    
                    # PDF Export
                    pdf_bytes = generate_certificate(item)
                    c_pdf.download_button("📥 Audit PDF", pdf_bytes, f"Audit_{sel_name}.pdf")
                    
                    # JSON Export
                    c_json.download_button("🤖 Machine JSON", df[df['name']==sel_name].to_json(), f"DPP_{sel_name}.json")
                    
                    # Verwijderen
                    if c_del.button("🗑️ Verwijderen"):
                        with httpx.Client() as client:
                            client.delete(f"{API_URL_BATTERIES}?id=eq.{item['id']}", headers=headers)
                        st.rerun()

                with col_qr:
                    # Toon de QR code die bij dit specifieke ID hoort
                    st.image(make_qr(item['id']), width=180, caption="Scanbare QR-Code")
            else:
                st.info("Nog geen producten gevonden in de database.")
