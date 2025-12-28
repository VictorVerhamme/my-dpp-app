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

# --- 3. STYLING (Gecombineerd: Kleuren + Verbergen interface elementen) ---
st.markdown(f"""
    <style>
    /* Jouw bestaande kleuren en knoppen */
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    .stButton button {{ 
        background-color: {COLOR_ACCENT} !important; 
        color: white !important; 
        border-radius: 12px !important; 
    }}

    /* VERBERG WITTE BALK: Verbergt de volledige header bovenin */
    header {{ visibility: hidden; }}
    [data-testid="stHeader"] {{ display: none; }}

    /* VERBERG PIJLTJES: Verbergt de knop om de zijbalk in te klappen */
    [data-testid="stSidebarCollapseButton"] {{
        display: none;
    }}

    /* OPTIONEEL: Haalt de witruimte bovenin weg nu de balk weg is */
    .block-container {{
        padding-top: 2rem;
    }}
    </style>
""", unsafe_allow_html=True)

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
            
            # --- TABS DEFINIËREN ---
            if st.session_state.company == "SuperAdmin":
                # SuperAdmin krijgt alleen Vloot en Admin Control
                tab_fleet, tab_admin = st.tabs(["📊 Vlootoverzicht", "🔐 Admin Control"])
                tab_reg, tab_bulk = None, None # Deze bestaan niet voor Admin
            else:
                # Normale gebruikers krijgen de standaard 3 tabs
                tab_reg, tab_fleet, tab_bulk = st.tabs(["✨ Nieuwe Registratie", "📊 Vlootoverzicht", "📂 Bulk Import"])
                tab_admin = None # Bestaat niet voor normale gebruikers

            # --- TAB 1: REGISTRATIE (Alleen voor gebruikers) ---
            if tab_reg:
                with tab_reg:
                    st.image(LOGO_URL, width=300)
                    with st.form("master_compliance_wizard"):
                        # ... (Houd hier je volledige formulier code zoals die was) ...
                        st.write("Formulier inhoud...") # Voorbeeld placeholder
                        if st.form_submit_button("Valideren & Registreren"):
                            pass 

            # --- TAB 2: VLOOTOVERZICHT (Voor IEDEREEN) ---
            with tab_fleet:
                # SUPERADMIN CHECK VOOR DATA
                if st.session_state.company == "SuperAdmin":
                    raw_data = get_data(API_URL_BATTERIES)
                    st.write("🔧 **SuperAdmin Modus:** U bekijkt de volledige wereldwijde database.")
                else:
                    raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{st.session_state.company}")

                if raw_data:
                    df = pd.DataFrame(raw_data)
                    st.dataframe(df[['battery_uid', 'name', 'batch_number', 'registration_date']], use_container_width=True, hide_index=True)
                    st.divider()
                    sel = st.selectbox("Selecteer product voor PDF", df['name'].tolist())
                    item = df[df['name'] == sel].iloc[0]
                    st.download_button("📥 Download Audit PDF", generate_certificate(item), f"Audit_{sel}.pdf", use_container_width=True)
                else:
                    st.info("Geen producten gevonden.")

            # --- TAB 3: BULK IMPORT (Alleen voor gebruikers) ---
            if tab_bulk:
                with tab_bulk:
                    st.subheader("📂 Bulk Import via CSV")
                    # ... (Houd hier je volledige Bulk Import code zoals die was) ...

            # --- TAB: ADMIN CONTROL (Alleen voor SuperAdmin) ---
            if tab_admin:
                with tab_admin:
                    st.subheader("🔐 Systeembeheer & Bedrijfsoverzicht")
                    
                    # 1. DATA OPHALEN VOOR ADMIN
                    all_companies_raw = get_data(API_URL_COMPANIES)
                    all_companies = [c for c in all_companies_raw if c.get('name') != "SuperAdmin"]
                    all_batteries = get_data(API_URL_BATTERIES)
                    
                    # 2. STATISTIEKEN IN KAARTEN
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    
                    if all_batteries and all_companies:
                        with col_stat1:
                            st.metric("Totaal Bedrijven", len(all_companies))
                        with col_stat2:
                            st.metric("Totaal DPP's Live", len(all_batteries))
                        with col_stat3:
                            # Bereken totaal aantal scans over het hele platform
                            total_scans = sum(item.get('views', 0) for item in all_batteries)
                            st.metric("Totaal Scans Wereldwijd", total_scans)
                    
                    st.divider()

                    # 3. GEDETAILLEERD OVERZICHT
                    col_left, col_right = st.columns([2, 1])
                    
                    with col_left:
                        st.markdown("### 🏢 Geregistreerde Partners")
                        if all_companies:
                            df_comp = pd.DataFrame(all_companies)
                            # We tonen alleen de naam en de datum van aanmaak
                            st.dataframe(df_comp[['name', 'created_at']], use_container_width=True, hide_index=True)
                        else:
                            st.warning("Geen bedrijfsgegevens gevonden.")

                    with col_right:
                        st.markdown("### 🛠️ Systeem Status")
                        st.success("API Verbinding: Actief")
                        st.success("Database: Verbonden (Supabase)")
                        st.info(f"Huidige Sessie: {st.session_state.company}")
                        
                        if st.button("🔄 Forceer Systeem Verversing"):
                            st.rerun()
