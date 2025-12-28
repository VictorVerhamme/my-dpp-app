import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile
import uuid
import os
from datetime import datetime

# --- 1. CONFIGURATIE & STYLING ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG = "#FDFBF7"      # Broken White
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="DPP Compliance Master 2025", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. JURIDISCHE & TECHNISCHE HELPERS ---

def is_authority():
    """Detecteert of een kijker een inspecteur is via de URL: ?id=...&role=inspectie"""
    return st.query_params.get("role") == "inspectie"

def make_qr(id):
    """Genereert een QR-code voor de unieke paspoort-URL"""
    url = f"https://digitalpassport.streamlit.app/?id={id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    """Genereert een formeel PDF certificaat conform EU 2023/1542"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 15, txt="EU Digital Product Passport - Compliance Certificate", ln=True, align='C')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(200, 10, txt=f"Audit Datum: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_fill_color(245, 247, 246)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, txt="Wettelijke Productidentificatie & Audit Trail", ln=True, align='L', fill=True)
    
    pdf.set_font("Arial", '', 9)
    fields = [
        ("Uniek Batterij ID (UUID)", data.get('battery_uid')),
        ("Productnaam / Model", data.get('name')),
        ("Batch / Serienummer", data.get('batch_number')),
        ("Productiedatum", data.get('production_date')),
        ("Gewicht (kg)", data.get('weight_kg')),
        ("Batterij Type", data.get('battery_type')),
        ("Chemie", data.get('chemistry')),
        ("CO2 Voetafdruk", f"{data.get('carbon_footprint')} kg"),
        ("CO2 Methode", data.get('carbon_method')),
        ("EPR Registratienummer", data.get('epr_number')),
        ("CE DoC Referentie", data.get('ce_doc_reference')),
        ("Recycled Li (%)", data.get('rec_lithium_pct')),
        ("Recycled Co (%)", data.get('rec_cobalt_pct')),
        ("Recycled Ni (%)", data.get('rec_nickel_pct')),
        ("State of Health (SoH)", f"{data.get('soh_pct')}%"),
        ("Laadcycli tot 80%", data.get('cycles_to_80')),
        ("Capaciteitsretentie (%)", data.get('capacity_retention_pct')),
        ("Geregistreerd door", data.get('modified_by')),
        ("Audit Trail Timestamp", data.get('registration_date'))
    ]
    
    for label, val in fields:
        pdf.cell(75, 7, txt=f"{label}:", border=1)
        pdf.cell(115, 7, txt=str(val or 'N/A'), border=1, ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, txt="End-of-Life & Recycling Instructies", ln=True, fill=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(190, 7, txt=str(data.get('eol_instructions') or "Niet gespecificeerd."), border=1)

    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img_bytes)
        tmp_path = tmp.name
    try:
        pdf.ln(10)
        pdf.image(tmp_path, x=75, y=pdf.get_y(), w=50)
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
        
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. INTERFACE STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    header, footer {{visibility: hidden;}}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    .login-container {{ display: flex; flex-direction: column; align-items: center; max-width: 400px; margin: 0 auto; padding-top: 10vh; }}
    .stButton button {{ background-color: {COLOR_ACCENT} !important; color: white !important; border-radius: 12px !important; width: 100% !important; border: none; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. APP LOGICA ---
q_params = st.query_params

if "id" in q_params:
    # --- PASPOORT PAGINA (SCAN VIEW) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        authority = is_authority()
        httpx.patch(f"{API_URL_BATTERIES}?id=eq.{d['id']}", json={"views": (d.get('views') or 0) + 1}, headers=headers)

        st.markdown(f"<div style='background:white; padding:40px; border-radius:25px; text-align:center; border-top:10px solid {COLOR_ACCENT}; box-shadow: 0 10px 30px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=200) # Groter logo op paspoort
        st.title(d.get('name', 'Product Paspoort'))
        st.divider()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint', 0)} kg", help=f"Methode: {d.get('carbon_method')}")
        c2.metric("Gewicht", f"{d.get('weight_kg', 0)} kg")
        c3.metric("State of Health", f"{d.get('soh_pct', 100)}%")
        
        if authority:
            st.divider()
            st.subheader("🕵️ Vertrouwelijke Inspectie Gegevens")
            st.json({"UUID": d.get("battery_uid"), "Batch": d.get("batch_number"), "CE DoC": d.get("ce_doc_reference"), "Timestamp": d.get("registration_date")})
        st.markdown("</div>", unsafe_allow_html=True)
    else: st.error("ID niet gevonden.")

else:
    # --- DASHBOARD & LOGIN ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image(LOGO_URL, width=350)
        st.markdown("### Compliance Portaal Inloggen")
        u = st.text_input("Username", placeholder="Naam", label_visibility="collapsed")
        p = st.text_input("Password", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        if st.button("Inloggen"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']
                st.rerun()
            else: st.error("Inloggegevens onjuist.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=130)
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        st.title(f"Management Dashboard")
        tab1, tab2 = st.tabs(["✨ Nieuwe Registratie", "📊 Vlootoverzicht & Audit Logs"])

        with tab1:
            # --- VERGROOT LOGO BOVENAAN WIZARD ---
            st.image(LOGO_URL, width=280) 
            st.info("Vul alle velden in om een conform EU 2023/1542 paspoort te genereren.")
            
            with st.form("master_compliance_wizard"):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown("##### 1. Identificatie")
                    f_name = st.text_input("Productnaam *")
                    f_model = st.text_input("Model ID *")
                    f_batch = st.text_input("Batch / Serienummer *")
                    f_date = st.date_input("Productiedatum")
                    f_weight = st.number_input("Gewicht (kg) *", min_value=0.0)
                with c2:
                    st.markdown("##### 2. Markttoegang")
                    f_epr = st.text_input("EPR Nummer")
                    f_doc = st.text_input("CE DoC Referentie")
                    f_ce = st.checkbox("CE Bevestigd", value=True)
                with c3:
                    st.markdown("##### 3. Milieu")
                    f_co2 = st.number_input("Carbon footprint (kg CO2)", min_value=0.0)
                    f_meth = st.selectbox("CO2 Methode", ["EU PEF", "ISO 14067"])
                    f_li = st.number_input("% Rec. Lithium", 0.0, 100.0)
                with c4:
                    st.markdown("##### 4. Levensduur")
                    f_cycles = st.number_input("Cycli tot 80%", min_value=0)
                    f_ret = st.number_input("Capaciteitsretentie (%)", 0, 100)
                    f_soh = st.slider("State of Health (%)", 0, 100, 100)

                st.divider()
                st.markdown("##### 5. Circulariteit & Instructies")
                f_eol = st.text_area("End-of-life instructies voor de consument (Verplicht)")

                if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                    check_url = f"{API_URL_BATTERIES}?model_name=eq.{f_model}&batch_number=eq.{f_batch}"
                    if get_data(check_url):
                        st.error(f"❌ Fout: Combinatie Model '{f_model}' en Batch '{f_batch}' bestaat al.")
                    elif f_li < 6.0:
                        st.error("❌ Compliance Fout: Lithium gehalte moet minstens 6% zijn (EU 2027).")
                    else:
                        payload = {
                            "name": f_name, "model_name": f_model, "batch_number": f_batch,
                            "battery_uid": str(uuid.uuid4()), "production_date": str(f_date),
                            "weight_kg": f_weight, "manufacturer": user, "ce_doc_reference": f_doc,
                            "ce_status": f_ce, "carbon_footprint": f_co2, "carbon_method": f_meth,
                            "rec_lithium_pct": f_li, "cycles_to_80": f_cycles, "capacity_retention_pct": f_ret,
                            "soh_pct": f_soh, "eol_instructions": f_eol, "modified_by": user,
                            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "views": 0
                        }
                        with httpx.Client() as client:
                            resp = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if resp.status_code == 201:
                                st.success("✅ Batterij succesvol geregistreerd!")
                                st.balloons()
                                st.rerun()

        with tab2:
            st.subheader("Geregistreerde Vloot")
            raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
            if raw_data:
                df = pd.DataFrame(raw_data)
                cols = ['battery_uid', 'name', 'model_name', 'batch_number', 'registration_date', 'views']
                st.dataframe(df[cols], use_container_width=True, hide_index=True)
                
                st.divider()
                sel_name = st.selectbox("Selecteer product voor Audit-acties", df['name'].tolist())
                item = df[df['name'] == sel_name].iloc[0]
                
                c_pdf, c_json, c_del = st.columns(3)
                with c_pdf:
                    st.download_button("📥 Audit PDF", generate_certificate(item), f"Audit_{sel_name}.pdf", use_container_width=True)
                with c_json:
                    st.download_button("🤖 Machine JSON", df[df['name']==sel_name].to_json(), f"DPP_{sel_name}.json", use_container_width=True)
                with c_del:
                    if st.button(f"🗑️ Verwijder {sel_name}", use_container_width=True):
                        httpx.delete(f"{API_URL_BATTERIES}?id=eq.{item['id']}", headers=headers)
                        st.rerun()
            else: st.info("Nog geen producten geregistreerd.")
