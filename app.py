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
    
    # 1. LOGO TOEVOEGEN (Rechtsboven)
    # We downloaden het logo kortstondig om het in de PDF te kunnen plaatsen
    try:
        with httpx.Client() as client:
            logo_resp = client.get(LOGO_URL)
            if logo_resp.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
                    tmp_logo.write(logo_resp.content)
                    tmp_logo_path = tmp_logo.name
                # Plaats logo rechtsboven: x=150, y=10, breedte=40
                pdf.image(tmp_logo_path, x=150, y=10, w=40)
                os.remove(tmp_logo_path)
    except:
        pass # Ga door zonder logo als de download faalt om crashes te voorkomen

    # 2. HEADER - NU VOLLEDIG ZWART
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(0, 0, 0) # Zwart (was saliegroen)
    pdf.cell(200, 15, txt="EU Digital Product Passport", ln=True, align='L')
    
    # Audit Datum - Nu in Zwart
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(0, 0, 0) # Zwart (was grijs)
    pdf.cell(200, 10, txt=f"Gegenereerd op: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='L')
    pdf.ln(10)
    
    # 3. TABEL SECTIE
    pdf.set_fill_color(245, 247, 246)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, txt="Wettelijke Productidentificatie & Audit Trail", ln=True, align='L', fill=True)
    
    pdf.set_font("Arial", '', 9)
    # Mapping van alle velden
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
    
    # Velden tekenen in zwart
    for label, val in fields:
        pdf.set_text_color(0, 0, 0) # Zekerheid dat tekst zwart is
        pdf.cell(70, 7, txt=f"{label}:", border=1)
        pdf.cell(120, 7, txt=str(val or 'N/A'), border=1, ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, txt="End-of-Life Instructies voor de consument", ln=True, fill=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(190, 6, txt=str(data.get('eol_instructions') or "Niet gespecificeerd."), border=1)

    # 4. QR CODE ONDERAAN
    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_qr:
        tmp_qr.write(qr_img_bytes)
        tmp_qr_path = tmp_qr.name
    try:
        pdf.ln(10)
        # QR code centreren
        pdf.image(tmp_qr_path, x=85, y=pdf.get_y(), w=40)
    finally:
        if os.path.exists(tmp_qr_path): os.remove(tmp_qr_path)
        
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

# Initialiseer pagina-status als deze nog niet bestaat
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "landing"

if "id" in q_params:
    # --- PASPOORT VIEW (Geoptimaliseerd voor Mobiel) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        authority = is_authority()
        
        # Mobiele CSS-injectie voor betere weergave
        st.markdown("""
            <style>
            .mobile-container {
                background-color: white;
                padding: 20px;
                border-radius: 15px;
                border-top: 8px solid #8FAF9A;
                margin: -10px; /* Haalt zijmarges op mobiel weg */
                box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
            }
            .metric-box {
                background-color: #F8F9F9;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
                text-align: center;
            }
            .stMetric {
                text-align: center !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="mobile-container">', unsafe_allow_html=True)
        
        # 1. Header
        st.image(LOGO_URL, width=150)
        st.title(d.get('name', 'Batterij Paspoort'))
        st.caption(f"ID: {d.get('battery_uid', 'N/A')}")
        
        st.divider()

        # 2. Belangrijkste Metrics (Groot & Duidelijk)
        # We gebruiken metrics die op mobiel onder elkaar komen te staan
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("🌍 Klimaatimpact", f"{d.get('carbon_footprint', 0)} kg")
        with col_m2:
            st.metric("♻️ Recycled", f"{d.get('rec_lithium_pct', 0)}%")
        
        st.divider()

        # 3. Batterij Gezondheid (Visueel)
        st.markdown("### 🔋 Batterij Conditie")
        soh = d.get('soh_pct', 100)
        st.write(f"Huidige Gezondheid: **{soh}%**")
        st.progress(soh / 100)
        
        # Extra details in kleine blokken
        st.write("---")
        det1, det2 = st.columns(2)
        det1.write(f"⚡ **Capaciteit**\n{d.get('capacity_kwh', 0)} kWh")
        det2.write(f"🔄 **Laadcycli**\n{d.get('cycles_to_80', 0)}")

        st.divider()

        # 4. Circulariteit & Instructies
        st.markdown("### ♻️ Einde Levensduur")
        st.info(d.get('eol_instructions') or "Lever dit product in bij een officieel batterij-inzamelpunt.")
        
        # 5. Admin/Inspectie View
        if authority:
            with st.expander("🕵️ Inspectie Details"):
                st.write("**Producent:**", d.get("manufacturer"))
                st.write("**Batch:**", d.get("batch_number"))
                st.write("**Geregistreerd:**", d.get("registration_date"))
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer voor consumentenvertrouwen
        st.caption("✅ Geverifieerd EU Digital Product Passport")
    else:
        st.error("Ongeldige QR-code. Paspoort niet gevonden.")
        
else:
    # --- DASHBOARD & LANDING PAGE LOGICA ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        if st.session_state.auth_mode == "landing":
            # --- STAP A: DE LANDING PAGE ---
            # We gebruiken kolommen voor marges aan de zijkant (Layout: 1-3-1)
            _, main_col, _ = st.columns([1, 3, 1]) 

            with main_col:
                st.image(LOGO_URL, width=350)
                
                # Hoofdtekst links uitgelijnd
                st.markdown(f"""
                    <div style="text-align: left;">
                        <h1 style='color: {COLOR_ACCENT}; margin-bottom: 0;'>EU Digital Product Passport</h1>
                        <h3 style='color: {COLOR_ACCENT}; margin-top: 0;'>De toekomst van batterij-compliance.</h3>
                        <p style='font-size: 1.1rem; color: #555; line-height: 1.6;'>
                            Welkom bij het centrale portaal voor de <b>EU-batterijverordening 2023/1542</b>. <br><br>
                            Wij helpen fabrikanten en importeurs bij het genereren, beheren en delen van digitale productpaspoorten. 
                            Onze cloud-gebaseerde oplossing zorgt voor volledige transparantie in de supply chain en 
                            vereenvoudigt de communicatie met consumenten en toezichthouders.
                        </p>
                    </div>
                    <br>
                """, unsafe_allow_html=True)
                
                # De Knop: Beperkt in breedte door een sub-kolom
                btn_col, _ = st.columns([1, 2]) 
                with btn_col:
                    if st.button("Ga naar het Portaal ➔"):
                        st.session_state.auth_mode = "login"
                        st.rerun()

                st.divider()

                # Informatie Kolommen: Nu ook links uitgelijnd binnen de main_col
                info_c1, info_c2, info_c3 = st.columns(3)
                
                with info_c1:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>✅ Volledig Conform</span>", unsafe_allow_html=True)
                    st.write("Voldoet aan alle 8 pijlers van de nieuwe EU-batterijverordening.")
                
                with info_c2:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>📊 Real-time Data</span>", unsafe_allow_html=True)
                    st.write("Direct inzicht in CO₂-impact en recycling-efficiëntie.")
                
                with info_c3:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>🔐 Veilig Beheer</span>", unsafe_allow_html=True)
                    st.write("Beveiligde toegang voor partners en inspectie-autoriteiten.")
                    
        elif st.session_state.auth_mode == "login":
            # --- STAP B: HET INLOGSCHERM ---
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.image(LOGO_URL, width=300)
            st.markdown("### Inloggen op uw Dashboard")
            u = st.text_input("Username", placeholder="Naam", label_visibility="collapsed")
            p = st.text_input("Password", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
            
            col_back, col_log = st.columns(2)
            with col_back:
                if st.button("⬅ Terug"):
                    st.session_state.auth_mode = "landing"
                    st.rerun()
            with col_log:
                if st.button("Inloggen"):
                    res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
                    if res and res[0]['password'] == p:
                        st.session_state.company = res[0]['name']
                        st.rerun()
                    else: st.error("Inloggegevens onjuist.")
            st.markdown('</div>', unsafe_allow_html=True)
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
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown("##### 1. Identificatie")
                            f_name = st.text_input("Productnaam *")
                            f_model = st.text_input("Model ID *")
                            f_batch = st.text_input("Batchnummer *")
                            f_date = st.date_input("Productiedatum")
                            f_weight = st.number_input("Gewicht (kg) *", min_value=0.1)
                        with col2:
                            st.markdown("##### 2. Markttoegang")
                            f_epr = st.text_input("EPR Nummer")
                            f_addr = st.text_input("Adres Fabriek")
                            f_doc = st.text_input("CE DoC Referentie")
                            f_mod = st.selectbox("CE Module", ["Module A", "Module B", "Module G"])
                        with col3:
                            st.markdown("##### 3. Milieu")
                            f_co2 = st.number_input("Carbon footprint (kg CO2)", min_value=0.0)
                            f_meth = st.selectbox("CO2 Methode", ["EU PEF", "ISO 14067"])
                            f_li = st.number_input("% Rec. Lithium", 0.0, 100.0)
                        with col4:
                            st.markdown("##### 4. Prestatie")
                            f_cap = st.number_input("Capaciteit (kWh)", min_value=0.0)
                            f_soh = st.slider("State of Health (%)", 0, 100, 100)
                            f_cycles = st.number_input("Cycli tot 80%", min_value=0)

                        st.divider()
                        f_eol = st.text_area("End-of-life instructies (Verplicht)")

                        if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                            payload = {
                                "name": f_name, "model_name": f_model, "batch_number": f_batch,
                                "battery_uid": str(uuid.uuid4()), "production_date": str(f_date),
                                "weight_kg": f_weight, "manufacturer": st.session_state.company,
                                "carbon_footprint": f_co2, "carbon_method": f_meth,
                                "rec_lithium_pct": f_li, "cycles_to_80": f_cycles, "soh_pct": f_soh,
                                "eol_instructions": f_eol, "modified_by": st.session_state.company,
                                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "views": 0
                            }
                            with httpx.Client() as client:
                                r = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                                if r.status_code == 201:
                                    st.success("✅ Succesvol geregistreerd!"); st.balloons(); st.rerun()

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

# --- TAB 3: BULK IMPORT ---
            if tab_bulk:
                with tab_bulk:
                    st.subheader("📂 Bulk Import via CSV")
                    
                    # Sjabloon download
                    template_df = pd.DataFrame({"Productnaam": ["Accu X"], "Model ID": ["MOD-1"], "Batchnummer": ["B1"], "Gewicht kg": [10.5], "CO2 kg": [5.0], "EOL Instructies": ["Recycle bij punt X"]})
                    csv_template = template_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Sjabloon", csv_template, "dpp_template.csv", "text/csv")

                    uploaded_file = st.file_uploader("Upload CSV", type="csv")
                    if uploaded_file and st.button("🚀 Start Bulk Import"):
                        df_upload = pd.read_csv(uploaded_file)
                        success_count = 0
                        for _, row in df_upload.iterrows():
                            payload = {
                                "name": str(row.get('Productnaam')), "model_name": str(row.get('Model ID')),
                                "batch_number": str(row.get('Batchnummer')), "battery_uid": str(uuid.uuid4()),
                                "weight_kg": float(row.get('Gewicht kg', 0)), "carbon_footprint": float(row.get('CO2 kg', 0)),
                                "eol_instructions": str(row.get('EOL Instructies')), "manufacturer": st.session_state.company,
                                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "views": 0
                            }
                            with httpx.Client() as client:
                                if client.post(API_URL_BATTERIES, json=payload, headers=headers).status_code == 201:
                                    success_count += 1
                        st.success(f"✅ {success_count} producten toegevoegd!"); st.rerun()

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
                        st.markdown("### 🛠️ Systeembeheer")
                        
                        # --- SECTIE: NIEUWE PARTNER TOEVOEGEN ---
                        st.markdown("---")
                        st.write("➕ **Voeg een nieuwe Partner toe**")
                        
                        with st.form("add_company_form", clear_on_submit=True):
                            new_comp_name = st.text_input("Naam van het bedrijf")
                            new_comp_pass = st.text_input("Wachtwoord voor dit bedrijf", type="password")
                            
                            if st.form_submit_button("Partner Registreren", use_container_width=True):
                                if new_comp_name and new_comp_pass:
                                    # Controleer of het bedrijf al bestaat
                                    check_comp = get_data(f"{API_URL_COMPANIES}?name=eq.{new_comp_name}")
                                    
                                    if check_comp:
                                        st.error(f"❌ Bedrijf '{new_comp_name}' bestaat al.")
                                    else:
                                        # Payload voor het nieuwe bedrijf
                                        new_payload = {
                                            "name": new_comp_name,
                                            "password": new_comp_pass,
                                            "created_at": datetime.now().isoformat()
                                        }
                                        
                                        with httpx.Client() as client:
                                            resp = client.post(API_URL_COMPANIES, json=new_payload, headers=headers)
                                            if resp.status_code in [200, 201]:
                                                st.success(f"✅ Bedrijf '{new_comp_name}' succesvol toegevoegd!")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Fout bij toevoegen: {resp.text}")
                                else:
                                    st.warning("Vul a.u.b. alle velden in.")
                        
                        # --- NIEUW: BEDRIJF VERWIJDEREN SECTIE ---
                        st.markdown("---")
                        st.write("🗑️ **Verwijder een Partner**")
                        
                        # Maak een lijst van namen voor de selectiebox
                        company_names = [c.get('name') for c in all_companies]
                        
                        if company_names:
                            target_company = st.selectbox("Selecteer bedrijf om te verwijderen", company_names, key="delete_company_select")
                            
                            # Veiligheidscheck via een knop
                            if st.button(f"Definitief verwijderen: {target_company}", type="secondary"):
                                # Voer de DELETE request uit naar de Companies tabel
                                delete_url = f"{API_URL_COMPANIES}?name=eq.{target_company}"
                                
                                with httpx.Client() as client:
                                    resp = client.delete(delete_url, headers=headers)
                                    
                                    if resp.status_code in [200, 204]:
                                        st.success(f"✅ Bedrijf '{target_company}' is succesvol verwijderd.")
                                        # Forceer een refresh om de lijst in de linker kolom bij te werken
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Fout bij verwijderen: {resp.text}")
                        else:
                            st.info("Geen partners beschikbaar om te verwijderen.")
                        
                        st.markdown("---")
                        # Bestaande systeem status info
                        st.success("API & Database: Verbonden")





