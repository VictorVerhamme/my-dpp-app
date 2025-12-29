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
import bcrypt

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
def update_data(endpoint, item_id, payload):
    url = f"{endpoint}?id=eq.{item_id}"
    with httpx.Client() as client:
        # PATCH zorgt ervoor dat we alleen sturen wat we willen veranderen
        response = client.patch(url, json=payload, headers=headers)
        return response.status_code
        
def hash_password(password):
    # Maak een veilig "gehashed" wachtwoord
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed):
    try:
        # Probeer eerst op de veilige manier (bcrypt)
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        # Als dit faalt (bijv. 'Invalid salt'), is het een oud plat-tekst wachtwoord
        # We vergelijken het dan gewoon direct
        return password == hashed
    
def is_authority():
    return st.query_params.get("role") == "inspectie"

def make_qr(id):
    # Verander de link naar je nieuwe GitHub Pages locatie
    # Vergeet de '.html' en de '?id=' aan het einde niet!
    url = f"https://victorverhamme.github.io/my-dpp-app/passport.html?id={id}"
    
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

# 1. INITIALISATIE: Zorg dat deze variabelen altijd bestaan in het geheugen
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "landing"

if 'company' not in st.session_state:
    st.session_state.company = None

# Haal de parameters uit de URL op
q_params = st.query_params

# 2. ROUTING: Ben je een consument (scan) of een beheerder (portaal)?
if "id" in q_params:
    # SNELLE REDIRECT: Stuur gsm-gebruikers direct naar de snelle GitHub-pagina
    st.info("Scan voltooid. U wordt doorverwezen naar het snelle mobiele portaal...")
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://victorverhamme.github.io/my-dpp-app/passport.html?id={q_params["id"]}\'" />', unsafe_allow_html=True)
    st.stop() # Stop de rest van de app hier voor consumenten
    
else:
    # --- DASHBOARD & LANDING PAGE LOGICA ---
    if not st.session_state.company:
        if st.session_state.auth_mode == "landing":
            # Optioneel: Haal het totaal aantal batterijen op voor de 'social proof'
            all_batts = get_data(API_URL_BATTERIES)
            total_count = len(all_batts) if all_batts else "1.250+" # Placeholder als database leeg is

            _, main_col, _ = st.columns([1, 3, 1]) 

            with main_col:
                st.image(LOGO_URL, width=350)
                
                # Impact-georiënteerde koptekst
                st.markdown(f"""
                    <div style="text-align: left;">
                        <h1 style='color: {COLOR_ACCENT}; margin-bottom: 0;'>Vertrouwen in elke cel.</h1>
                        <h3 style='color: #555; margin-top: 0;'>Reeds <b>{total_count} batterijen</b> veilig gedigitaliseerd conform EU 2023/1542.</h3>
                        <p style='font-size: 1.1rem; color: #666; line-height: 1.6; margin-top: 20px;'>
                            Wij zijn de drijvende kracht achter de circulaire batterij-economie. Fabrikanten en importeurs 
                            vertrouwen op ons platform voor het real-time valideren, beheren en delen van digitale productpaspoorten. 
                            <b>Voorkom boetes, versnel uw audit-proces en bied volledige transparantie aan uw eindgebruiker.</b>
                        </p>
                    </div>
                    <br>
                """, unsafe_allow_html=True)
                
                # De Knop
                btn_col, _ = st.columns([1, 2]) 
                with btn_col:
                    if st.button("Start met Digitaliseren ➔"):
                        st.session_state.auth_mode = "login"
                        st.rerun()

                st.divider()

                # Informatie Kolommen met focus op resultaat
                info_c1, info_c2, info_c3 = st.columns(3)
                
                with info_c1:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>🛡️ Audit-Proof</span>", unsafe_allow_html=True)
                    st.write("Gegarandeerde naleving van de 8 wettelijke pijlers voor markttoegang in de EU.")
                
                with info_c2:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>📈 Schaalbaar</span>", unsafe_allow_html=True)
                    st.write("Van prototype tot bulk-import van tienduizenden eenheden in enkele seconden.")
                
                with info_c3:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>🤝 Partner Netwerk</span>", unsafe_allow_html=True)
                    st.write("Verbind fabrikanten, overheden en consumenten in één veilig ecosysteem.")
                    
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
                    if res:
                        stored_hash = res[0]['password']
                        # Gebruik de helper functie om te verifiëren
                        if check_password(p, stored_hash):
                            st.session_state.company = res[0]['name']
                            st.rerun()
                        else:
                            st.error("Wachtwoord onjuist.")
                    else:
                        st.error("Gebruiker niet gevonden.")
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
                    # --- STAP 2: BATTERIJ BEWERKEN (Toevoeging) ---
                    if st.session_state.company != "SuperAdmin":
                        st.divider()
                        with st.expander("📝 Status Update (SOH / Cycli aanpassen)"):
                            st.write("Pas hier de actuele status van een batterij aan na inspectie.")
                            
                            # We maken een lijst van UID's zodat de gebruiker de juiste batterij kiest
                            batt_list = {f"{b['name']} (ID: {b['battery_uid']})": b for b in raw_data}
                            selected_uid_label = st.selectbox("Welke batterij wilt u bijwerken?", options=list(batt_list.keys()), key="edit_selector")
                            
                            selected_batt = batt_list[selected_uid_label]

                            # Bewerk-formulier
                            with st.form(f"edit_form_{selected_batt['battery_uid']}"):
                                col_e1, col_e2 = st.columns(2)
                                with col_e1:
                                    up_soh = st.slider("Actuele State of Health (%)", 0, 100, int(selected_batt.get('soh_pct', 100)))
                                with col_e2:
                                    up_cycles = st.number_input("Nieuw aantal laadcycli", value=int(selected_batt.get('cycles_to_80', 0)))
                                
                                up_eol = st.text_area("Update End-of-life instructies", value=selected_batt.get('eol_instructions', ""))
                                
                                if st.form_submit_button("Wijzigingen Opslaan", use_container_width=True):
                                    update_payload = {
                                        "soh_pct": up_soh,
                                        "cycles_to_80": up_cycles,
                                        "eol_instructions": up_eol,
                                        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M") # Update timestamp
                                    }
                                    
                                    status = update_data(API_URL_BATTERIES, selected_batt['id'], update_payload)
                                    
                                    if status in [200, 204]:
                                        st.success(f"✅ Status voor {selected_batt['battery_uid']} bijgewerkt!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Fout bij het bijwerken van de database.")
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
                    st.subheader("🔐 Systeembeheer & Partneroverzicht")
                    
                    # 1. DATA OPHALEN
                    all_companies_raw = get_data(API_URL_COMPANIES)
                    all_companies = [c for c in all_companies_raw if c.get('name') != "SuperAdmin"]
                    all_batteries = get_data(API_URL_BATTERIES)
                    
                    # 2. STATISTIEKEN (Bovenaan)
                    c_st1, c_st2 = st.columns(2)
                    c_st1.metric("Geregistreerde Partners", len(all_companies))
                    
                    # Hier hebben we de tekst aangepast zoals gevraagd
                    c_st2.metric("Totaal geregistreerde batterijen", len(all_batteries))
                    
                    st.divider()

                    # 3. LAYOUT IN TWEE KOLOMMEN
                    col_left, col_right = st.columns([2, 1])

                    with col_left:
                        st.markdown("### 🏢 Partner Overzicht")
                        if all_companies and all_batteries:
                            # Maak DataFrames
                            df_comp = pd.DataFrame(all_companies)
                            df_batt = pd.DataFrame(all_batteries)
                            
                            # CORRECTIE: value_counts() ipv value_value_counts()
                            counts = df_batt['manufacturer'].value_counts().reset_index()
                            counts.columns = ['name', 'Batterijen']
                            
                            # Voeg data samen
                            df_final = pd.merge(df_comp[['name', 'created_at']], counts, on='name', how='left').fillna(0)
                            df_final['Batterijen'] = df_final['Batterijen'].astype(int)
                            
                            st.dataframe(
                                df_final.rename(columns={'name': 'Bedrijf', 'created_at': 'Lid sinds'}), 
                                use_container_width=True, 
                                hide_index=True
                            )
                        else:
                            st.info("Nog geen partnerdata beschikbaar.")

                    with col_right:
                        st.markdown("### 🛠️ Acties")
                        
                        # --- FORMULIER: PARTNER TOEVOEGEN ---
                        st.write("➕ **Voeg Partner toe**")
                        with st.form("add_company_form", clear_on_submit=True):
                            new_comp_name = st.text_input("Naam van het bedrijf")
                            new_comp_pass = st.text_input("Wachtwoord", type="password")
                            
                            # Belangrijk: Gebruik form_submit_button binnen een form
                            submit_add = st.form_submit_button("Opslaan", use_container_width=True)
                            
                            if submit_add:
                                if new_comp_name and new_comp_pass:
                                    secure_password = hash_password(new_comp_pass) 
                                    new_payload = {
                                        "name": new_comp_name, 
                                        "password": secure_password, 
                                        "created_at": datetime.now().isoformat()
                                    }
                                    with httpx.Client() as client:
                                        resp = client.post(API_URL_COMPANIES, json=new_payload, headers=headers)
                                        if resp.status_code in [200, 201]:
                                            st.success(f"✅ {new_comp_name} toegevoegd!")
                                            st.rerun()
                                        else:
                                            st.error("Fout bij opslaan.")
                        
                        st.divider()

                        # --- VERWIJDEREN (BUITEN HET FORMULIER) ---
                        st.write("🗑️ **Verwijder Partner**")
                        company_names = [c.get('name') for c in all_companies]
                        if company_names:
                            target_company = st.selectbox("Selecteer bedrijf", company_names, key="del_select_admin")
                            if st.button(f"Verwijder {target_company}", type="secondary", use_container_width=True):
                                with httpx.Client() as client:
                                    resp = client.delete(f"{API_URL_COMPANIES}?name=eq.{target_company}", headers=headers)
                                    if resp.status_code in [200, 204]:
                                        st.success(f"{target_company} verwijderd.")
                                        st.rerun()
                                    else:
                                        st.error("Fout bij verwijderen.")



