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

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"
COLOR_BG = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/43LQn3qG/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="DPP Compliance Master 2025", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. HELPERS ---
def is_authority():
    return st.query_params.get("role") == "inspectie"

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
    pdf.ln(5)
    
    pdf.set_fill_color(245, 247, 246)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, txt="Wettelijke Productidentificatie & Audit Trail", ln=True, fill=True)
    
    pdf.set_font("Arial", '', 8)
    # Alle velden in het PDF document
    fields = [
        ("Batterij UUID", data.get('battery_uid')),
        ("Naam / Model", data.get('name')),
        ("Batchnummer", data.get('batch_number')),
        ("Productiedatum", data.get('production_date')),
        ("Gewicht (kg)", data.get('weight_kg')),
        ("Batterij Type", data.get('battery_type')),
        ("CO2 Voetafdruk", f"{data.get('carbon_footprint')} kg"),
        ("CO2 Methode", data.get('carbon_method')),
        ("EPR Nummer", data.get('epr_number')),
        ("CE DoC Referentie", data.get('ce_doc_reference')),
        ("CE Module", data.get('ce_module')),
        ("Recycled Li (%)", data.get('rec_lithium_pct')),
        ("Recycled Co (%)", data.get('rec_cobalt_pct')),
        ("Recycled Ni (%)", data.get('rec_nickel_pct')),
        ("Recycled Pb (%)", data.get('rec_lead_pct')),
        ("Laadcycli tot 80%", data.get('cycles_to_80')),
        ("Capaciteitsretentie (%)", data.get('capacity_retention_pct')),
        ("State of Health (SoH)", f"{data.get('soh_pct')}%"),
        ("Geregistreerd door", data.get('modified_by')),
        ("Registratie Datum", data.get('registration_date'))
    ]
    
    for label, val in fields:
        pdf.cell(70, 6, txt=f"{label}:", border=1)
        pdf.cell(120, 6, txt=str(val or 'N/A'), border=1, ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 7, txt="End-of-Life Instructies voor de consument", ln=True, fill=True)
    pdf.set_font("Arial", '', 8)
    pdf.multi_cell(190, 5, txt=str(data.get('eol_instructions') or "Niet gespecificeerd."), border=1)

    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img_bytes)
        tmp_path = tmp.name
    try:
        pdf.ln(5)
        pdf.image(tmp_path, x=85, y=pdf.get_y(), w=40)
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. STYLING ---
st.markdown(f"<style>.stApp {{ background-color: {COLOR_BG}; }} h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }} .stButton button {{ background-color: {COLOR_ACCENT} !important; color: white !important; border-radius: 12px !important; }}</style>", unsafe_allow_html=True)

# --- 4. APP LOGICA ---
q_params = st.query_params

if "id" in q_params:
    # --- PASPOORT VIEW (SCAN) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        authority = is_authority()
        st.markdown(f"<div style='background:white; padding:40px; border-radius:25px; text-align:center; border-top:10px solid {COLOR_ACCENT};'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=200)
        st.title(d.get('name'))
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint', 0)} kg", help=f"Methode: {d.get('carbon_method')}")
        c2.metric("Gewicht", f"{d.get('weight_kg', 0)} kg")
        c3.metric("State of Health", f"{d.get('soh_pct', 100)}%")
        
        st.subheader("♻️ End-of-Life Instructies")
        st.info(d.get('eol_instructions') or "Geen instructies opgegeven.")
        
        if authority:
            st.divider(); st.subheader("🕵️ Vertrouwelijke Audit Gegevens")
            st.json({"UUID": d.get("battery_uid"), "Batch": d.get("batch_number"), "Geregistreerd door": d.get("modified_by"), "Datum": d.get("registration_date")})
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- DASHBOARD & NAVIGATIE ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        # LOGIN
        st.markdown('<div style="text-align:center; padding-top:10vh;">', unsafe_allow_html=True)
        st.image(LOGO_URL, width=350)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Inloggen"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']; st.rerun()
    else:
        # SIDEBAR
        st.sidebar.image(LOGO_URL, width=150)
        st.sidebar.title(f"Welkom, {st.session_state.company}")
        nav = st.sidebar.radio("Navigatie", ["🏠 Dashboard", "📖 Compliance Gids"])
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None; st.rerun()

        if nav == "📖 Compliance Gids":
            st.title("📖 Compliance Gids & Definities")
            st.markdown("""
            ### 1. Identificatie
            
            * **Productnaam (verplicht):** Naam van het product, bijv. “EV Accu 10Ah”.
            * **Model ID (verplicht):** Interne of externe modelidentificatie, bijv. “EV-1000X”.
            * **Batchnummer (verplicht):** Productiebatchnummer, bijv. “BATCH-20251228-01”.
            * **Productiedatum:** Datum van productie, bijv. “2025/12/28”.
            * **Gewicht (kg) (verplicht):** Gewicht van het product, bijv. “0,10”.
            * **Batterijtype:** Type batterij, bijv. “EV”.
            * **Chemie:** Chemische samenstelling, bijv. “NMC” of “LFP”.
            
            ### 2. Markttoegang
            
            * **EPR-nummer:** Nummer voor Extended Producer Responsibility.
            * **Adres fabriek:** Locatie van productie.
            * **CE DoC referentie:** Nummer van de CE Declaration of Conformity, bijv. “CE-DoC-2025-001”.
            * **CE module:** CE-certificeringsmodule, bijv. “Module A”.
            
            ### 3. Milieu & Recycling
            
            * **Carbon footprint (kg CO2):** CO2-uitstoot van het product, bijv. “0,00”.
            * **CO2 methode:** Methode voor CO2-berekening, bijv. “EU PEF”.
            * **% gerecycled lithium:** Percentage lithium uit recycling.
            * **% gerecycled kobalt:** Percentage kobalt uit recycling.
            * **% gerecycled nikkel:** Percentage nikkel uit recycling.
            * **% gerecycled lood:** Percentage lood uit recycling.
            * **Referentiejaar content:** Jaar van de milieugegevens, bijv. “2025”.
            
            ### 4. Prestatie
            
            * **Capaciteit (kWh):** Energiecapaciteit, bijv. “0,00”.
            * **Huidige State of Health (%):** Gezondheidstoestand van de batterij, 0–100.
            * **Cycli tot 80%:** Aantal laadcycli tot 80% capaciteit, bijv. “0”.
            * **Capaciteitsretentie (%):** Percentage van oorspronkelijke capaciteit dat behouden blijft, bijv. “0”.
            * **DPP versie:** Versie van het Data/Product Performance Protocol, bijv. “1.0.0”.
            * **End-of-life instructies (verplicht):** Instructies voor correcte afvoer door de consument.
            * **Herkomst kritieke grondstoffen (Due Diligence):** Bronnen van kritieke grondstoffen, inclusief due diligence, bijv. “NMC: Democratische Republiek Congo, LFP: China”.
            """)
        else:
            st.title("Digital Passport Management")
            tab1, tab2 = st.tabs(["✨ Nieuwe Registratie", "📊 Vlootoverzicht"])

            with tab1:
                st.image(LOGO_URL, width=300)
                with st.form("master_compliance_wizard"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown("##### 1. Identificatie")
                        f_name = st.text_input("Productnaam *")
                        f_model = st.text_input("Model ID *")
                        f_batch = st.text_input("Batchnummer *")
                        f_date = st.date_input("Productiedatum")
                        f_weight = st.number_input("Gewicht (kg) *", min_value=0.1)
                        f_type = st.selectbox("Batterij Type", ["EV", "LMT", "Industrieel", "Draagbaar"])
                        f_chem = st.text_input("Chemie (bijv. NMC, LFP)")
                    with col2:
                        st.markdown("##### 2. Markttoegang")
                        f_epr = st.text_input("EPR Nummer")
                        f_addr = st.text_input("Adres Fabriek")
                        f_doc = st.text_input("CE DoC Referentie")
                        f_mod = st.selectbox("CE Module", ["Module A", "Module A1", "Module B", "Module G"])
                        f_ce = st.checkbox("CE Bevestigd", value=True)
                    with col3:
                        st.markdown("##### 3. Milieu & Recycling")
                        f_co2 = st.number_input("Carbon footprint (kg CO2)", min_value=0.0)
                        f_meth = st.selectbox("CO2 Methode", ["EU PEF", "ISO 14067"])
                        f_li = st.number_input("% Rec. Lithium", 0.0, 100.0)
                        f_co = st.number_input("% Rec. Kobalt", 0.0, 100.0)
                        f_ni = st.number_input("% Rec. Nikkel", 0.0, 100.0)
                        f_pb = st.number_input("% Rec. Lood", 0.0, 100.0)
                        f_ry = st.number_input("Referentiejaar Content", 2020, 2030, 2025)
                    with col4:
                        st.markdown("##### 4. Prestatie")
                        f_cap = st.number_input("Capaciteit (kWh)", min_value=0.0)
                        f_soh = st.slider("Huidige State of Health (%)", 0, 100, 100)
                        f_cycles = st.number_input("Cycli tot 80%", min_value=0)
                        f_ret = st.number_input("Capaciteitsretentie (%)", 0, 100)
                        f_ver = st.text_input("DPP Versie", "1.0.0")

                    st.divider()
                    col_ext1, col_ext2 = st.columns(2)
                    with col_ext1:
                        f_eol = st.text_area("End-of-life instructies voor de consument (Verplicht)")
                    with col_ext2:
                        f_origin = st.text_area("Herkomst kritieke grondstoffen (Due Diligence)")

                    if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                        check_url = f"{API_URL_BATTERIES}?model_name=eq.{f_model}&batch_number=eq.{f_batch}"
                        if get_data(check_url):
                            st.error(f"❌ Fout: Product met Model '{f_model}' en Batch '{f_batch}' bestaat al.")
                        elif f_li < 6.0:
                            st.error("❌ Lithium-gehalte te laag (min. 6% vereist).")
                        else:
                            payload = {
                                "name": f_name, "model_name": f_model, "batch_number": f_batch,
                                "battery_uid": str(uuid.uuid4()), "production_date": str(f_date),
                                "weight_kg": f_weight, "battery_type": f_type, "chemistry": f_chem,
                                "manufacturer": st.session_state.company, "manufacturer_address": f_addr,
                                "epr_number": f_epr, "ce_doc_reference": f_doc, "ce_module": f_mod,
                                "ce_status": f_ce, "carbon_footprint": f_co2, "carbon_method": f_meth,
                                "rec_lithium_pct": f_li, "rec_cobalt_pct": f_co, "rec_nickel_pct": f_ni,
                                "rec_lead_pct": f_pb, "rec_reference_year": f_ry, "capacity_kwh": f_cap,
                                "soh_pct": f_soh, "cycles_to_80": f_cycles, "capacity_retention_pct": f_ret,
                                "eol_instructions": f_eol, "mineral_origin": f_origin,
                                "modified_by": st.session_state.company,
                                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "views": 0
                            }
                            with httpx.Client() as client:
                                r = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                                if r.status_code == 201:
                                    st.success("✅ Succesvol geregistreerd!"); st.balloons(); st.rerun()

            with tab2:
                raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{st.session_state.company}")
                if raw_data:
                    df = pd.DataFrame(raw_data)
                    st.dataframe(df[['battery_uid', 'name', 'batch_number', 'registration_date']], use_container_width=True, hide_index=True)
                    st.divider()
                    sel = st.selectbox("Selecteer product voor PDF", df['name'].tolist())
                    item = df[df['name'] == sel].iloc[0]
                    st.download_button("📥 Download Audit PDF", generate_certificate(item), f"Audit_{sel}.pdf", use_container_width=True)
                else: st.info("Geen producten gevonden.")


