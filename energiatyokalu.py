import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- SIVUN ASETUKSET ---
st.set_page_config(page_title="Talotekniikan Energiatyökalu", layout="wide")

# Sivuvalikko
st.sidebar.title("Valitse työkalu")
tyokalu = st.sidebar.radio("Työkalut:", 
    ["LTO-vikalaskuri", "Puhallinmuutos", "Vuotava venttiili", "SFP-laskuri", "Osatehokäyttö (Puhallinlait)", "LTO-uusinta (Hyötysuhde)"])

# ==========================================
# 1. LTO-VIKALASKURI
# ==========================================
if tyokalu == "LTO-vikalaskuri":
    st.title("LTO-vikalaskuri: Reaaliaikainen kustannus")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ilmavirta = st.number_input("Tuloilmavirta (m³/s)", min_value=0.0, value=2.5, step=0.1, format="%.1f")
    with col2:
        ulko_t = st.number_input("Ulkolämpötila nyt (°C)", value=-5.0, step=1.0, format="%.1f")
        tulo_t = st.number_input("Tuloilman asetus (°C)", value=19.0, step=1.0, format="%.1f")
    with col3:
        energia_tyyppi = st.radio("Lämmitystapa:", ["Kaukolämpö", "Sähkö"])
        hinta = st.number_input("Hinta (€/kWh)", min_value=0.0, value=0.10 if energia_tyyppi == "Kaukolämpö" else 0.20, step=0.01, format="%.2f")

    dt = max(0, tulo_t - ulko_t)
    teho_kw = ilmavirta * 1.2 * 1.0 * dt
    
    paiva_kwh = teho_kw * 24
    viikko_kwh = paiva_kwh * 7
    kk_kwh = paiva_kwh * 30

    st.subheader("Ylimääräinen energiankulutus ja kustannus")
    c1, c2, c3 = st.columns(3)
    
    c1.metric("Päivä", f"{paiva_kwh * hinta:.0f} €", f"{paiva_kwh:.0f} kWh lisäkulutus", delta_color="inverse")
    c2.metric("Viikko", f"{viikko_kwh * hinta:.0f} €", f"{viikko_kwh:.0f} kWh lisäkulutus", delta_color="inverse")
    c3.metric("Kuukausi", f"{kk_kwh * hinta:.0f} €", f"{kk_kwh:.0f} kWh lisäkulutus", delta_color="inverse")

    with st.expander("Näytä laskennan perusteet ja kaavat"):
        st.markdown(r"""
        **Ilmapuolen tehokaava:**
        $P = q_v \cdot \rho \cdot c_p \cdot \Delta T$
        """)

    with st.expander("💼 Sisäinen muistio"):
        st.info(f"LTO on rikki. Kone vaatii {teho_kw:.1f} kW lisätehoa.")


# ==========================================
# 2. PUHALLINMUUTOS
# ==========================================
elif tyokalu == "Puhallinmuutos":
    st.title("Puhallinmuutos: Investointilaskelma")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Puhaltimien tiedot")
        p_vanha = st.number_input("Vanhan puhaltimen ottoteho (kW)", min_value=0.0, value=5.5, step=0.1, format="%.1f")
        p_uusi = st.number_input("Uuden EC-puhaltimen ottoteho (kW)", min_value=0.0, value=3.0, step=0.1, format="%.1f")
        
        st.subheader("Koneen käyttöaika")
        kaytto_tapa = st.selectbox("Valitse käyttöprofiili:", ["Jatkuva 24/7 (8760 h/v)", "Päiväkäyttö (esim. toimistot/koulut)", "Syötä vuosittaiset tunnit käsin"])
        
        if kaytto_tapa == "Jatkuva 24/7 (8760 h/v)":
            tunnit = 8760
            st.caption("Kone on aina päällä (esim. asuinkerrostalot, sairaalat).")
        elif kaytto_tapa == "Päiväkäyttö (esim. toimistot/koulut)":
            c_h, c_d = st.columns(2)
            tunnit_pv = c_h.number_input("Tuntia / vuorokausi", min_value=1, max_value=24, value=12, step=1)
            paivat_vko = c_d.number_input("Päivää / viikko", min_value=1, max_value=7, value=5, step=1)
            tunnit = tunnit_pv * paivat_vko * 52
            st.success(f"Laskennalliset käyntitunnit yhteensä: **{tunnit} tuntia vuodessa**")
        else:
            tunnit = st.number_input("Käyntitunnit (h/vuosi)", min_value=1, value=4000, step=100)
            
    with col2:
        st.subheader("Investointi ja tarkastelu")
        investointi = st.number_input("Investoinnin hinta (€)", min_value=0.0, value=4000.0, step=500.0, format="%.0f")
        sahko_hinta = st.number_input("Sähkön hinta (€/kWh)", min_value=0.0, value=0.15, step=0.01, format="%.2f")
        arviointi_aika = st.slider("Tarkastelujakso (Vuosia)", 1, 25, 5)

    vuosi_saasto_eur = (p_vanha - p_uusi) * tunnit * sahko_hinta
    vuosi_saasto_kwh = (p_vanha - p_uusi) * tunnit
    roi = investointi / vuosi_saasto_eur if vuosi_saasto_eur > 0 else 0

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Vuotuinen säästö", f"{vuosi_saasto_eur:.0f} €", f"-{vuosi_saasto_kwh:.0f} kWh kulutusta", delta_color="inverse")
    c2.metric("Investoinnin takaisinmaksuaika", f"{roi:.1f} vuotta")

    st.subheader(f"Elinkaarikustannusten vertailu {arviointi_aika} vuoden jaksolla")
    
    kokonais_vanha = p_vanha * tunnit * sahko_hinta * arviointi_aika
    kokonais_uusi = investointi + (p_uusi * tunnit * sahko_hinta * arviointi_aika)
    kokonais_saasto = kokonais_vanha - kokonais_uusi

    v1, v2, v3 = st.columns(3)
    with v1:
        st.markdown("<h5 style='color: #d62728;'>Kulut vanhalla hihnakoneella</h5>", unsafe_allow_html=True)
        st.metric("", f"{kokonais_vanha:.0f} €")
    with v2:
        st.markdown("<h5 style='color: #2ca02c;'>Kulut uudella EC-koneella</h5>", unsafe_allow_html=True)
        st.metric("", f"{kokonais_uusi:.0f} €")
    with v3:
        st.markdown("<h5>Kumulatiivinen taloudellinen hyöty</h5>", unsafe_allow_html=True)
        st.metric("", f"{kokonais_saasto:.0f} €", "Verrattuna nykytilaan", delta_color="normal")

    vuodet = np.arange(0, arviointi_aika + 1)
    df = pd.DataFrame({
        "Vuosi": vuodet,
        "Vanha kone": p_vanha * tunnit * sahko_hinta * vuodet,
        "Uusi EC-kone": investointi + (p_uusi * tunnit * sahko_hinta * vuodet)
    })
    
    fig = px.line(df, x="Vuosi", y=["Vanha kone", "Uusi EC-kone"], 
                  labels={"value": "Kustannukset (€)", "variable": "Vaihtoehto"},
                  color_discrete_map={"Vanha kone": "#d62728", "Uusi EC-kone": "#2ca02c"})
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Näytä laskennan perusteet ja kaavat"):
        st.markdown(r"""
        **Säästetty energia:**
        $E = (P_{vanha} - P_{uusi}) \cdot t$
        
        **Takaisinmaksuaika (ROI):**
        $\text{ROI} = \frac{\text{Investointi}}{\text{Vuotuinen säästö (€)}}$
        """)

    with st.expander("💼 Sisäinen muistio"):
        st.info(f"Päivitys maksaa {investointi} €. Säästö tarkastelujaksolla on netto {kokonais_saasto:.0f} €.")


# ==========================================
# 3. VUOTAVA VENTTIILI
# ==========================================
elif tyokalu == "Vuotava venttiili":
    st.title("Vuotava venttiili: Tuplahukan laskenta")
    
    col1, col2 = st.columns(2)
    with col1:
        vuoto_tyyppi = st.radio("Mikä venttiili vuotaa?", ["Lämmitysventtiili", "Jäähdytysventtiili"])
        qv = st.number_input("Ilmavirta (m³/s)", min_value=0.0, value=2.0, step=0.1, format="%.1f")
        leak_dt = st.number_input("Vuodon lämpötilamuutos ilmassa (°C)", min_value=0.0, value=3.0, step=0.5, format="%.1f")
    with col2:
        h_hinta = st.number_input("Lämmityksen hinta (€/kWh)", min_value=0.0, value=0.10, step=0.01, format="%.2f")
        c_hinta = st.number_input("Jäähdytyksen hinta (€/kWh)", min_value=0.0, value=0.15, step=0.01, format="%.2f")

    teho_kw = qv * 1.2 * 1.0 * leak_dt
    kk_hukka_kwh = teho_kw * 24 * 30
    kk_hukka_eur = kk_hukka_kwh * (h_hinta + c_hinta)
    
    st.subheader("Tuplahukan kustannukset (24/7 käynti)")
    c1, c2 = st.columns(2)
    c1.metric("Vuototeho", f"{teho_kw:.1f} kW")
    c2.metric("Kustannus (Kuukausi)", f"{kk_hukka_eur:.0f} €", f"{kk_hukka_kwh * 2:.0f} kWh ylimääräistä energiaa", delta_color="inverse")

    with st.expander("Näytä laskennan perusteet ja kaavat"):
        st.markdown(r"**Tuplahukka:** $P \cdot \text{lämmityshinta} + P \cdot \text{jäähdytyshinta}$")

    with st.expander("💼 Sisäinen muistio"):
        st.info("Automaatio kompensoi vuodon vastakkaisella energialla.")


# ==========================================
# 4. SFP-LASKURI
# ==========================================
elif tyokalu == "SFP-laskuri":
    st.title("SFP-laskuri (Specific Fan Power)")
    
    col1, col2 = st.columns(2)
    with col1:
        p_summa = st.number_input("Puhaltimien yhteisteho (kW)", min_value=0.0, value=4.5, step=0.1, format="%.1f")
        qv_max = st.number_input("Suurin ilmavirta (m³/s)", min_value=0.0, value=2.5, step=0.1, format="%.1f")
    
    if qv_max > 0:
        sfp = p_summa / qv_max
        st.subheader(f"SFP-luku: {sfp:.2f}")
        
        if sfp < 1.5: st.success("Erinomainen")
        elif sfp < 2.5: st.warning("Välttävä")
        else: st.error("Heikko")
    else:
        st.warning("Syötä nollaa suurempi ilmavirta laskeaksesi SFP-luvun.")
        sfp = 0.0

    with st.expander("Näytä laskennan perusteet ja kaavat"):
        st.markdown(r"$SFP = \frac{P_{summa}}{q_{v,max}}$")

    with st.expander("💼 Sisäinen muistio"):
        if sfp > 0:
            st.info(f"Kohteen SFP-luku on {sfp:.2f}.")
        else:
            st.info("Syötä arvot nähdäksesi arvion.")


# ==========================================
# 5. OSATEHOKÄYTTÖ (PUHALLINLAIT)
# ==========================================
elif tyokalu == "Osatehokäyttö":
    st.title("Osatehokäyttö: Säästöpotentiaali")
    
    col1, col2 = st.columns(2)
    with col1:
        p_nimellinen = st.number_input("Teho 100% ilmavirralla (kW)", min_value=0.0, value=5.0, step=0.1, format="%.1f")
        pudotus_prosentti = st.slider("Ilmavirran pudotus osateholla (%)", 0, 50, 20, help="Esimerkiksi yöaikaan tai viikonloppuisin tehtävä osatehoajo.")
    with col2:
        tunnit_vrk = st.number_input("Osatehoajon kesto (t/vrk)", min_value=1, max_value=24, value=12, step=1)
        hinta = st.number_input("Sähkön hinta (€/kWh)", min_value=0.0, value=0.15, step=0.01, format="%.2f")

    uusi_nopeus_suhde = (100 - pudotus_prosentti) / 100
    uusi_teho = p_nimellinen * (uusi_nopeus_suhde**3)
    saasto_kw = p_nimellinen - uusi_teho
    
    saasto_eur_vrk = saasto_kw * tunnit_vrk * hinta

    st.subheader(f"Säästöpotentiaali")
    c1, c2, c3 = st.columns(3)
    c1.metric("Säästö (Viikko)", f"{saasto_eur_vrk * 7:.0f} €", delta_color="inverse")
    c2.metric("Säästö (Kuukausi)", f"{saasto_eur_vrk * 30:.0f} €", delta_color="inverse")
    c3.metric("Säästö (Vuosi)", f"{saasto_eur_vrk * 365:.0f} €", delta_color="inverse")

    # Dynaaminen Plotly-käyrä
    x_prosentit = np.arange(50, 101, 1)
    y_tehot = p_nimellinen * ((x_prosentit / 100) ** 3)
    fig2 = px.line(pd.DataFrame({"Ilmavirta (%)": x_prosentit, "Teho (kW)": y_tehot}), 
                  x="Ilmavirta (%)", y="Teho (kW)")
    fig2.add_scatter(x=[100 - pudotus_prosentti], y=[uusi_teho], marker=dict(color="red", size=15))
    fig2.update_layout(showlegend=False, xaxis_title="Ilmavirta (%)", yaxis_title="Tehonkulutus (kW)")
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Näytä laskennan perusteet ja kaavat"):
        st.markdown(r"$P_2 = P_1 \cdot \left(\frac{q_{v2}}{q_{v1}}\right)^3$")

    with st.expander("💼 Sisäinen muistio"):
        st.info("Osatehokäyttö (nopeuden pudotus) leikkaaa tehonkulutusta radikaalisti eksponentiaalisen suhteen vuoksi.")

# ==========================================
# 6. LTO-UUSINTA (HYÖTYSUHTEEN NOSTO)
# ==========================================
elif tyokalu == "LTO-uusinta (Hyötysuhde)":
    st.title("LTO-uusinta: Investointilaskelma")
    st.write("Laskee energiansäästön, kun vanha lämmöntalteenotto (esim. neste-LTO) vaihdetaan tehokkaampaan (esim. pyörivä LTO).")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Koneen tiedot")
        qv = st.number_input("Ilmavirta (m³/s)", min_value=0.0, value=3.0, step=0.1, format="%.1f")
        eta_vanha = st.number_input("Vanhan LTO hyötysuhde (%)", min_value=0, max_value=100, value=40, step=1)
        eta_uusi = st.number_input("Uuden LTO hyötysuhde (%)", min_value=0, max_value=100, value=80, step=1)
        
        st.subheader("Sijainti ja käyttö")
        sijainti = st.selectbox("Kohteen sijainti (Lämmitystarveluku S17):", 
                                ["Helsinki/Etelä-Suomi (4000 Kd)", 
                                 "Jyväskylä/Keski-Suomi (4800 Kd)", 
                                 "Oulu/Pohjois-Pohjanmaa (5500 Kd)", 
                                 "Rovaniemi/Lappi (6000 Kd)"])
        
        if "Helsinki" in sijainti: s17 = 4000
        elif "Jyväskylä" in sijainti: s17 = 4800
        elif "Oulu" in sijainti: s17 = 5500
        else: s17 = 6000
        
        # UUSI: Älykäs käyttöaikavalikko
        kaytto_tapa = st.selectbox("Valitse käyttöprofiili:", ["Jatkuva 24/7 (8760 h/v)", "Päiväkäyttö (esim. toimistot/koulut)", "Syötä vuosittaiset tunnit käsin"])
        
        if kaytto_tapa == "Jatkuva 24/7 (8760 h/v)":
            tunnit = 8760
            st.caption("Kone on aina päällä (esim. asuinkerrostalot, sairaalat).")
        elif kaytto_tapa == "Päiväkäyttö (esim. toimistot/koulut)":
            c_h, c_d = st.columns(2)
            # key-parametrit estävät Streamlitia sekoittamasta näitä Puhallinmuutoksen kenttiin
            tunnit_pv = c_h.number_input("Tuntia / vuorokausi", min_value=1, max_value=24, value=12, step=1, key="lto_h")
            paivat_vko = c_d.number_input("Päivää / viikko", min_value=1, max_value=7, value=5, step=1, key="lto_d")
            tunnit = tunnit_pv * paivat_vko * 52
            st.success(f"Laskennalliset käyntitunnit yhteensä: **{tunnit} tuntia vuodessa**")
        else:
            tunnit = st.number_input("Käyntitunnit (h/vuosi)", min_value=1, value=4000, step=100, key="lto_man")

    with col2:
        st.subheader("Investointi")
        investointi = st.number_input("Uudistuksen kokonaishinta (€)", min_value=0.0, value=35000.0, step=1000.0, format="%.0f")
        h_hinta = st.number_input("Lämmitysenergian hinta (€/kWh)", min_value=0.0, value=0.10, step=0.01, format="%.2f")
        arviointi_aika = st.slider("Tarkastelujakso (Vuosia)", 1, 25, 10)

    # LASKENTA
    e_max_kwh = qv * 1.2 * 1.0 * (s17 * 24) * (tunnit / 8760)
    
    kulutus_vanha_kwh = e_max_kwh * (1 - (eta_vanha / 100))
    kulutus_uusi_kwh = e_max_kwh * (1 - (eta_uusi / 100))
    
    saasto_kwh_vuosi = kulutus_vanha_kwh - kulutus_uusi_kwh
    saasto_eur_vuosi = saasto_kwh_vuosi * h_hinta
    
    roi = investointi / saasto_eur_vuosi if saasto_eur_vuosi > 0 else 0

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Vuotuinen säästö", f"{saasto_eur_vuosi:.0f} €", f"-{saasto_kwh_vuosi:.0f} kWh", delta_color="inverse")
    c2.metric("Takaisinmaksuaika", f"{roi:.1f} vuotta")
    c3.metric(f"Nettosäästö {arviointi_aika} vuodessa", f"{(saasto_eur_vuosi * arviointi_aika) - investointi:.0f} €", "Investointi vähennetty", delta_color="normal")

    # GRAAFI
    vuodet = np.arange(0, arviointi_aika + 1)
    kulu_vanha = kulutus_vanha_kwh * h_hinta * vuodet
    kulu_uusi = investointi + (kulutus_uusi_kwh * h_hinta * vuodet)
    
    df = pd.DataFrame({
        "Vuosi": vuodet,
        "Vanha LTO (Vain energia)": kulu_vanha,
        "Uusi LTO (Energia + Investointi)": kulu_uusi
    })
    
    fig = px.line(df, x="Vuosi", y=["Vanha LTO (Vain energia)", "Uusi LTO (Energia + Investointi)"], 
                  labels={"value": "Kumulatiiviset kustannukset (€)", "variable": "Vaihtoehto"},
                  color_discrete_map={"Vanha LTO (Vain energia)": "#d62728", "Uusi LTO (Energia + Investointi)": "#2ca02c"})
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Näytä laskennan perusteet ja kaavat"):
        st.markdown(r"""
        **Teoreettinen maksimi lämmitysenergian tarve (ilman LTO:ta):**
        $E_{max} = q_v \cdot \rho \cdot c_p \cdot (S17 \cdot 24) \cdot \left(\frac{t}{8760}\right)$
        * $S17$ = Sijainnin lämmitystarveluku
        * $t$ = Käyntitunnit vuodessa
        
        **LTO:n jälkeinen kulutus:**
        $E_{kulutus} = E_{max} \cdot (1 - \eta)$
        """)

    with st.expander("💼 Sisäinen muistio"):
        st.info(f"Kohteessa on iso säästöpotentiaali. LTO:n päivitys hyötysuhteesta {eta_vanha}% tasoon {eta_uusi}% säästää asiakkaalta {saasto_eur_vuosi:.0f} € vuodessa. Investointi maksaa itsensä takaisin {roi:.1f} vuodessa.")
