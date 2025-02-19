import streamlit as st
import pandas as pd
import altair as alt
import random

# =====================================================================
# SETUP: Page configuration and custom CSS to widen the container
# =====================================================================
st.set_page_config(page_title="Skolu informācijas panelis", layout="wide")
st.markdown(
    """
    <style>
        [data-testid="stBlockContainer"] {
            max-width: 1400px;
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Determine text color based on theme (for dark mode compatibility)
theme_base = st.get_option("theme.base")
if theme_base == "dark":
    text_color = "white"
else:
    text_color = "black"

# =====================================================================
# Helper function: add noise if exam values are too similar.
# =====================================================================
def add_noise_if_similar(school_val, country_val, threshold=5, noise_amplitude=10):
    if abs(school_val - country_val) < threshold:
        new_school = school_val + random.uniform(-noise_amplitude, noise_amplitude)
        new_country = country_val + random.uniform(-noise_amplitude, noise_amplitude)
        # Clamp values to 0-100
        new_school = max(0, min(new_school, 100))
        new_country = max(0, min(new_country, 100))
        return new_school, new_country
    else:
        return school_val, country_val

# =====================================================================
# DATA DEFINITIONS
# =====================================================================
# For each school we define:
# - "quartile": socio‑economic distribution. Country average is always given.
# - "valsts_eksameni" and "diagnostiskie_eksameni": exam results for each subject (for years 2019–2023)
# - "apmierinātība": student satisfaction (as percentages)
# Other fields (student count, staff, location, etc.) are also provided.

skolu_dati = {
    "Rīgas Pilsētas 1. Pamatskola": {
        "nosaukums": "Rīgas Pilsētas 1. Pamatskola",
        "sektors": "Valsts",
        "skolas_tips": "Pamatskola",
        "gadu_range": "1-6",
        "adrese": "Brīvības iela 1, Rīga",
        "lat": 56.9496,
        "lon": 24.1052,
        "skola_web": "http://www.rp1pamatskola.lv",
        "skolotaji": {"Skolotāju skaits": 25, "Pilna laika ekvivalents": 23.5},
        "personals": {"Administratīvais personāls": 5, "Pilna laika ekvivalents": 5.0},
        "skolēnu_skaits": {
            "2019": {"zēni": 150, "meitenes": 160},
            "2020": {"zēni": 145, "meitenes": 155},
            "2021": {"zēni": 140, "meitenes": 150},
            "2022": {"zēni": 135, "meitenes": 145},
            "2023": {"zēni": 130, "meitenes": 140},
        },
        # Socio‑economic distribution (school vs. country average)
        "quartile": {
            "skola": {"Q1": 35, "Q2": 32, "Q3": 23, "Q4": 10},
            "valsts_vidējais": {"Q1": 30, "Q2": 30, "Q3": 25, "Q4": 15}
        },
        "apmeklejums": {
            "2019": 95, "2020": 93, "2021": 94, "2022": 92, "2023": 90,
        },
        "apmierinātība": {
            "skola": {"2019": 72, "2020": 74, "2021": 79, "2022": 83, "2023": 87},
            "valsts_vidējais": {"2019": 80, "2020": 80, "2021": 80, "2022": 80, "2023": 80},
        },
        # Valsts eksāmenu dati – 9. klase
        "valsts_eksameni": {
            "9. klase": {
                "Matematika": {
                    "skola": {"2019": 65, "2020": 65, "2021": 66, "2022": 65, "2023": 66},
                    "valsts_vidējais": {"2019": 65, "2020": 66, "2021": 67, "2022": 66, "2023": 67},
                },
                "Latviešu valoda": {
                    "skola": {"2019": 70, "2020": 70, "2021": 71, "2022": 71, "2023": 72},
                    "valsts_vidējais": {"2019": 70, "2020": 71, "2021": 72, "2022": 71, "2023": 72},
                },
                "Angļu valoda": {
                    "skola": {"2019": 75, "2020": 75, "2021": 75, "2022": 76, "2023": 77},
                    "valsts_vidējais": {"2019": 75, "2020": 76, "2021": 77, "2022": 76, "2023": 77},
                },
            },
            "12. klase": {
                "Matematika": {
                    "skola": {"2019": 60, "2020": 61, "2021": 60, "2022": 61, "2023": 62},
                    "valsts_vidējais": {"2019": 61, "2020": 62, "2021": 61, "2022": 62, "2023": 63},
                },
                "Latviešu valoda": {
                    "skola": {"2019": 68, "2020": 68, "2021": 69, "2022": 69, "2023": 70},
                    "valsts_vidējais": {"2019": 68, "2020": 69, "2021": 70, "2022": 69, "2023": 70},
                },
                "Angļu valoda": {
                    "skola": {"2019": 72, "2020": 72, "2021": 72, "2022": 73, "2023": 74},
                    "valsts_vidējais": {"2019": 72, "2020": 73, "2021": 74, "2022": 73, "2023": 74},
                },
            },
        },
        # Diagnostikas darbi – 3. klase
        "diagnostiskie_eksameni": {
            "3. klase": {
                "Lasītprasme": {
                    "skola": {"2019": 80, "2020": 80, "2021": 81, "2022": 81, "2023": 82},
                    "valsts_vidējais": {"2019": 80, "2020": 81, "2021": 82, "2022": 81, "2023": 82},
                },
                "Rēķinpratība": {
                    "skola": {"2019": 75, "2020": 75, "2021": 76, "2022": 76, "2023": 77},
                    "valsts_vidējais": {"2019": 75, "2020": 76, "2021": 77, "2022": 76, "2023": 77},
                },
                "Dabaszinātnes": {
                    "skola": {"2019": 70, "2020": 70, "2021": 71, "2022": 71, "2023": 72},
                    "valsts_vidējais": {"2019": 70, "2020": 71, "2021": 72, "2022": 71, "2023": 72},
                },
            },
            "6. klase": {
                "Lasītprasme": {
                    "skola": {"2019": 85, "2020": 85, "2021": 86, "2022": 86, "2023": 87},
                    "valsts_vidējais": {"2019": 85, "2020": 86, "2021": 87, "2022": 86, "2023": 87},
                },
                "Rēķinpratība": {
                    "skola": {"2019": 80, "2020": 80, "2021": 81, "2022": 81, "2023": 82},
                    "valsts_vidējais": {"2019": 80, "2020": 81, "2021": 82, "2022": 81, "2023": 82},
                },
                "Dabaszinātnes": {
                    "skola": {"2019": 75, "2020": 75, "2021": 76, "2022": 76, "2023": 77},
                    "valsts_vidējais": {"2019": 75, "2020": 76, "2021": 77, "2022": 76, "2023": 77},
                },
            },
        },
    },
    "Jelgavas Privātā Vidusskola": {
        "nosaukums": "Jelgavas Privātā Vidusskola",
        "sektors": "Privāts",
        "skolas_tips": "Vidusskola",
        "gadu_range": "7-12",
        "adrese": "Brīvības iela 10, Jelgava",
        "lat": 56.6570,
        "lon": 23.7110,
        "skola_web": "http://www.jpvidusskola.lv",
        "skolotaji": {"Skolotāju skaits": 30, "Pilna laika ekvivalents": 28.0},
        "personals": {"Administratīvais personāls": 6, "Pilna laika ekvivalents": 6.0},
        "skolēnu_skaits": {
            "2019": {"zēni": 200, "meitenes": 210},
            "2020": {"zēni": 195, "meitenes": 205},
            "2021": {"zēni": 190, "meitenes": 200},
            "2022": {"zēni": 185, "meitenes": 195},
            "2023": {"zēni": 180, "meitenes": 190},
        },
        # Socio‑economic distribution: Tilted toward Q4 (affluent)
        "quartile": {
            "skola": {"Q1": 10, "Q2": 15, "Q3": 25, "Q4": 50},
            "valsts_vidējais": {"Q1": 30, "Q2": 30, "Q3": 25, "Q4": 15}
        },
        "apmeklejums": {
            "2019": 96, "2020": 95, "2011": 95, "2022": 94, "2023": 93,
        },
        "apmierinātība": {
            "skola": {"2019": 76, "2020": 84, "2021": 82, "2022": 77, "2023": 85},
            "valsts_vidējais": {"2019": 80, "2020": 80, "2021": 80, "2022": 80, "2023": 80},
        },
        # Valsts eksāmenu dati – 9. klase
        "valsts_eksameni": {
            "9. klase": {
                "Matematika": {
                    "skola": {"2019": 80, "2020": 82, "2021": 81, "2022": 83, "2023": 82},
                    "valsts_vidējais": {"2019": 75, "2020": 76, "2021": 75, "2022": 76, "2023": 77},
                },
                "Latviešu valoda": {
                    "skola": {"2019": 85, "2020": 86, "2021": 85, "2022": 87, "2023": 86},
                    "valsts_vidējais": {"2019": 80, "2020": 81, "2021": 80, "2022": 81, "2023": 82},
                },
                "Angļu valoda": {
                    "skola": {"2019": 88, "2020": 89, "2021": 88, "2022": 90, "2023": 89},
                    "valsts_vidējais": {"2019": 83, "2020": 84, "2021": 83, "2022": 84, "2023": 85},
                },
            },
            "12. klase": {
                "Matematika": {
                    "skola": {"2019": 78, "2020": 79, "2021": 78, "2022": 80, "2023": 79},
                    "valsts_vidējais": {"2019": 73, "2020": 74, "2021": 73, "2022": 74, "2023": 75},
                },
                "Latviešu valoda": {
                    "skola": {"2019": 82, "2020": 83, "2021": 82, "2022": 84, "2023": 83},
                    "valsts_vidējais": {"2019": 77, "2020": 78, "2021": 77, "2022": 78, "2023": 79},
                },
                "Angļu valoda": {
                    "skola": {"2019": 85, "2020": 86, "2021": 85, "2022": 87, "2023": 86},
                    "valsts_vidējais": {"2019": 80, "2020": 81, "2021": 80, "2022": 81, "2023": 82},
                },
            },
        },
        "diagnostiskie_eksameni": {
            "3. klase": {
                "Lasītprasme": {
                    "skola": {"2019": 88, "2020": 89, "2021": 88, "2022": 90, "2023": 89},
                    "valsts_vidējais": {"2019": 83, "2020": 84, "2021": 83, "2022": 84, "2023": 85},
                },
                "Rēķinpratība": {
                    "skola": {"2019": 85, "2020": 86, "2021": 85, "2022": 87, "2023": 86},
                    "valsts_vidējais": {"2019": 80, "2020": 81, "2021": 80, "2022": 81, "2023": 82},
                },
                "Dabaszinātnes": {
                    "skola": {"2019": 90, "2020": 91, "2021": 90, "2022": 92, "2023": 91},
                    "valsts_vidējais": {"2019": 85, "2020": 86, "2021": 85, "2022": 86, "2023": 87},
                },
            },
            "6. klase": {
                "Lasītprasme": {
                    "skola": {"2019": 92, "2020": 93, "2021": 92, "2022": 94, "2023": 93},
                    "valsts_vidējais": {"2019": 87, "2020": 88, "2021": 87, "2022": 88, "2023": 89},
                },
                "Rēķinpratība": {
                    "skola": {"2019": 90, "2020": 91, "2021": 90, "2022": 92, "2023": 91},
                    "valsts_vidējais": {"2019": 85, "2020": 86, "2021": 85, "2022": 86, "2023": 87},
                },
                "Dabaszinātnes": {
                    "skola": {"2019": 88, "2020": 89, "2021": 88, "2022": 90, "2023": 89},
                    "valsts_vidējais": {"2019": 83, "2020": 84, "2021": 83, "2022": 84, "2023": 85},
                },
            },
        },
    },
    "Liepājas Pirmsskolas Centrs": {
        "nosaukums": "Liepājas Pirmsskolas Centrs",
        "sektors": "Valsts",
        "skolas_tips": "Pirmsskolas izglītība",
        "gadu_range": "0-6",
        "adrese": "Pils iela 5, Liepāja",
        "lat": 56.5048,
        "lon": 21.0118,
        "skola_web": "http://www.lpc.lv",
        "skolotaji": {"Skolotāju skaits": 15, "Pilna laika ekvivalents": 14.0},
        "personals": {"Administratīvais personāls": 4, "Pilna laika ekvivalents": 4.0},
        "skolēnu_skaits": {
            "2019": {"zēni": 80, "meitenes": 90},
            "2020": {"zēni": 78, "meitenes": 88},
            "2021": {"zēni": 75, "meitenes": 85},
            "2022": {"zēni": 73, "meitenes": 83},
            "2023": {"zēni": 70, "meitenes": 80},
        },
        # Socio‑economic distribution: Matches country average
        "quartile": {
            "skola": {"Q1": 22, "Q2": 28, "Q3": 30, "Q4": 20},
            "valsts_vidējais": {"Q1": 30, "Q2": 30, "Q3": 25, "Q4": 15}
        },
        "apmeklejums": {
            "2019": 97, "2020": 96, "2021": 95, "2022": 94, "2023": 93,
        },
        "apmierinātība": {
            # This school’s satisfaction is higher than the country average
            "skola": {"2019": 90, "2020": 91, "2021": 90, "2022": 91, "2023": 90},
            "valsts_vidējais": {"2019": 85, "2020": 85, "2021": 85, "2022": 85, "2023": 85},
        },
        "valsts_eksameni": {
            "9. klase": {
                "Matematika": {
                    "skola": {"2019": 60, "2020": 60, "2021": 59, "2022": 60, "2023": 59},
                    "valsts_vidējais": {"2019": 65, "2020": 66, "2021": 65, "2022": 66, "2023": 67},
                },
                "Latviešu valoda": {
                    "skola": {"2019": 68, "2020": 68, "2011": 67, "2022": 68, "2023": 67},
                    "valsts_vidējais": {"2019": 70, "2020": 71, "2021": 70, "2022": 71, "2023": 72},
                },
                "Angļu valoda": {
                    "skola": {"2019": 72, "2020": 72, "2021": 71, "2022": 72, "2023": 71},
                    "valsts_vidējais": {"2019": 75, "2020": 76, "2021": 75, "2022": 76, "2023": 77},
                },
            },
            "12. klase": {
                "Matematika": {
                    "skola": {"2019": 58, "2020": 58, "2021": 57, "2022": 58, "2023": 57},
                    "valsts_vidējais": {"2019": 61, "2020": 62, "2021": 61, "2022": 62, "2023": 63},
                },
                "Latviešu valoda": {
                    "skola": {"2019": 66, "2020": 66, "2021": 65, "2022": 66, "2023": 65},
                    "valsts_vidējais": {"2019": 68, "2020": 69, "2021": 68, "2022": 69, "2023": 70},
                },
                "Angļu valoda": {
                    "skola": {"2019": 70, "2020": 70, "2021": 69, "2022": 70, "2023": 69},
                    "valsts_vidējais": {"2019": 72, "2020": 73, "2021": 72, "2022": 73, "2023": 74},
                },
            },
        },
        "diagnostiskie_eksameni": {
            "3. klase": {
                "Lasītprasme": {
                    "skola": {"2019": 78, "2020": 78, "2021": 77, "2022": 78, "2023": 77},
                    "valsts_vidējais": {"2019": 80, "2020": 81, "2021": 80, "2022": 81, "2023": 82},
                },
                "Rēķinpratība": {
                    "skola": {"2019": 73, "2020": 73, "2021": 72, "2022": 73, "2023": 72},
                    "valsts_vidējais": {"2019": 75, "2020": 76, "2021": 75, "2022": 76, "2023": 77},
                },
                "Dabaszinātnes": {
                    "skola": {"2019": 68, "2020": 68, "2021": 67, "2022": 68, "2023": 67},
                    "valsts_vidējais": {"2019": 70, "2020": 71, "2021": 70, "2022": 71, "2023": 72},
                },
            },
            "6. klase": {
                "Lasītprasme": {
                    "skola": {"2019": 83, "2020": 83, "2021": 82, "2022": 83, "2023": 82},
                    "valsts_vidējais": {"2019": 85, "2020": 86, "2021": 85, "2022": 86, "2023": 87},
                },
                "Rēķinpratība": {
                    "skola": {"2019": 78, "2020": 78, "2021": 77, "2022": 78, "2023": 77},
                    "valsts_vidējais": {"2019": 80, "2020": 81, "2021": 80, "2022": 81, "2023": 82},
                },
                "Dabaszinātnes": {
                    "skola": {"2019": 73, "2020": 73, "2021": 72, "2022": 73, "2023": 72},
                    "valsts_vidējais": {"2019": 75, "2020": 76, "2021": 75, "2022": 76, "2023": 77},
                },
            },
        },
    },
}

# =====================================================================
# APP LAYOUT: Title and Tab Structure
# =====================================================================
st.title("Skolu informācijas panelis")

# School selector
skolu_list = list(skolu_dati.keys())
izveleta_skola = st.selectbox("Izvēlies skolu:", skolu_list)
skola = skolu_dati[izveleta_skola]

# Create tabs for "Galvenā informācija", "Skolēnu labbūtība", "Eksāmeni"
cilsnes = st.tabs(["Galvenā informācija", "Skolēnu labbūtība", "Eksāmeni"])

# =====================================================================
# 1. GALVENĀ INFORMĀCIJA
# =====================================================================
with cilsnes[0]:
    st.header("Skolas fakti un statistika")
    st.write(
        "Šajā sadaļā atradīsi pamatinformāciju par skolu – tās nosaukumu, tipu, adresi, mājaslapu, personālu un skolēnu sadalījumu pa dzimumiem.")

    st.subheader("Skolas fakti")
    st.markdown(f"""**Nosaukums:** {skola['nosaukums']}  
**Sektors:** {skola['sektors']}  
**Skolas tips:** {skola['skolas_tips']}  
**Mācību gadi:** {skola['gadu_range']}  
**Adrese:** {skola['adrese']}  
**Skolas mājaslapa:** [klikšķini šeit]({skola['skola_web']})
    """)

    st.subheader("Skolas personāls")
    st.markdown("**Skolotāji:** " + ", ".join([f"{key}: {value}" for key, value in skola["skolotaji"].items()]))
    st.markdown("**Administratīvais personāls:** " + ", ".join(
        [f"{key}: {value}" for key, value in skola["personals"].items()]))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Skolas atrašanās vieta")
        df_map = pd.DataFrame({'lat': [skola['lat']], 'lon': [skola['lon']]})
        st.map(df_map, zoom=10)
    with col2:
        st.subheader("Skolēnu skaits pēdējos 5 gados")
        dati_Skolēni = []
        for gads, dzimumi in skola["skolēnu_skaits"].items():
            for dzimums, skaits in dzimumi.items():
                dati_Skolēni.append({"Gads": int(gads), "Dzimums": dzimums.capitalize(), "Skaits": skaits})
        df_Skolēni = pd.DataFrame(dati_Skolēni)
        skolēnu_chart = alt.Chart(df_Skolēni).mark_bar().encode(
            x=alt.X("Gads:O", title="Gads"),
            y=alt.Y("Skaits:Q", title="skolēnu skaits"),
            color=alt.Color("Dzimums:N", title="Dzimums"),
            tooltip=["Gads", "Dzimums", "Skaits"]
        ).properties(width=350, height=500)
        skolēnu_chart = skolēnu_chart.configure_axis(labelFontSize=16, titleFontSize=18) \
            .configure_legend(labelFontSize=16, titleFontSize=18, orient='bottom', direction='horizontal')
        st.altair_chart(skolēnu_chart, use_container_width=True)

# =====================================================================
# 2. SKOLĒNU LABBŪTĪBA
# =====================================================================
with cilsnes[1]:
    st.header("Skolēnu labbūtība")
    st.warning("No esošajiem VIIS datiem šādu cilni nevarētu izveidot!")
    st.write(
        "Šajā sadaļā redzēsi apmeklējuma datus, skolēnu apmierinātības vērtējumu, kā arī socio-ekonomisko izglītības priekšrocību sadalījumu (ar procentiem tieši virs stabiņiem).")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Apmeklējuma dati")
        dati_apmeklejums = []
        for gads, proc in skola["apmeklejums"].items():
            dati_apmeklejums.append({"Gads": int(gads), "Apmeklējums (%)": proc})
        df_apmeklejums = pd.DataFrame(dati_apmeklejums)
        apmeklejums_chart = alt.Chart(df_apmeklejums).mark_line(point=True).encode(
            x=alt.X("Gads:O", title="Gads"),
            y=alt.Y("Apmeklējums (%):Q", title="Apmeklējums (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=["Gads", "Apmeklējums (%)"]
        ).properties(width=350, height=300)
        apmeklejums_chart = apmeklejums_chart.configure_axis(labelFontSize=16, titleFontSize=18) \
            .configure_legend(labelFontSize=16, titleFontSize=18, orient='bottom', direction='horizontal')
        st.altair_chart(apmeklejums_chart, use_container_width=True)
    with col2:
        st.subheader("Skolēnu apmierinātība")
        dati_apmierinata = []
        for gads in skola["apmierinātība"]["skola"].keys():
            dati_apmierinata.append({
                "Gads": int(gads),
                "Rezultāts": skola["apmierinātība"]["skola"][gads],
                "Kategorija": "Skola"
            })
            dati_apmierinata.append({
                "Gads": int(gads),
                "Rezultāts": skola["apmierinātība"]["valsts_vidējais"][gads],
                "Kategorija": "Valsts vidējais"
            })
        df_apmier = pd.DataFrame(dati_apmierinata)
        apmierinata_chart = alt.Chart(df_apmier).mark_line(point=True).encode(
            x=alt.X("Gads:O", title="Gads"),
            y=alt.Y("Rezultāts:Q", title="Apmierinātība (%)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Kategorija:N", title="Kategorija"),
            tooltip=["Gads", "Kategorija", "Rezultāts"]
        ).properties(width=350, height=300)
        apmierinata_chart = apmierinata_chart.configure_axis(labelFontSize=16, titleFontSize=18) \
            .configure_legend(labelFontSize=16, titleFontSize=18, orient='bottom', direction='horizontal')
        st.altair_chart(apmierinata_chart, use_container_width=True)

    st.subheader("Socio-ekonomisko priekšrocību sadalījums")
    dati_quartile = []
    for kvartile, vērtība in skola["quartile"]["skola"].items():
        dati_quartile.append({"kvartile": kvartile, "Tips": "Skola", "Vērtība": vērtība})
    for kvartile, vērtība in skola["quartile"]["valsts_vidējais"].items():
        dati_quartile.append({"kvartile": kvartile, "Tips": "Valsts vidējais", "Vērtība": vērtība})
    df_quartile = pd.DataFrame(dati_quartile)
    df_quartile["Label"] = df_quartile["Vērtība"].astype(str) + "%"

    bars = alt.Chart(df_quartile).mark_bar().encode(
        x=alt.X("kvartile:N", title="kvartile"),
        xOffset=alt.X("Tips:N"),
        y=alt.Y("Vērtība:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
        color=alt.Color("Tips:N", title="Kategorija"),
        tooltip=["kvartile", "Tips", "Vērtība"]
    ).properties(width=300, height=300)

    text = alt.Chart(df_quartile).mark_text(dy=10, fontSize=16, color=text_color).encode(
        x=alt.X("kvartile:N"),
        xOffset=alt.X("Tips:N"),
        y=alt.Y("Vērtība:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
        text=alt.Text("Label:N")
    )

    soc_chart = (bars + text).configure_axis(labelFontSize=16, titleFontSize=18) \
        .configure_legend(labelFontSize=16, titleFontSize=18, orient='bottom', direction='horizontal')
    st.altair_chart(soc_chart, use_container_width=True)

# =====================================================================
# 3. EKSĀMENI
# =====================================================================
with cilsnes[2]:
    st.header("Eksāmenu rezultāti")
    st.write(
        "Šajā sadaļā atradīsi informāciju par valsts un diagnostisko eksāmenu rezultātiem. Izvēlies eksāmenu tipu, klasi un priekšmetu, lai apskatītu datus (rezultāti procentos, no 0 līdz 100%).")

    eksamenu_tips = st.radio("Izvēlies eksāmenu tipu:", ["Valsts eksāmeni", "Diagnostikas darbi"])

    if eksamenu_tips == "Valsts eksāmeni":
        st.subheader("Valsts eksāmeni")
        klase = st.selectbox("Izvēlies klasi:", ["9. klase", "12. klase"])
        priekšmeti = list(skola["valsts_eksameni"][klase].keys())
        priekšmets = st.selectbox("Izvēlies priekšmetu:", priekšmeti)

        dati_eksameni = skola["valsts_eksameni"][klase][priekšmets]
        if dati_eksameni.get("skola") is None or all(v is None for v in dati_eksameni["skola"].values()):
            st.info("Valsts eksāmenu dati šai skolai nav pieejami.")
        else:
            dati_valsts = []
            for gads in dati_eksameni["skola"].keys():
                # Add noise if school and country values are too similar.
                school_val = dati_eksameni["skola"][gads]
                country_val = dati_eksameni["valsts_vidējais"][gads]
                new_school, new_country = add_noise_if_similar(school_val, country_val)
                dati_valsts.append({
                    "Gads": int(gads),
                    "Rezultāts": new_school,
                    "Kategorija": "Skola"
                })
                dati_valsts.append({
                    "Gads": int(gads),
                    "Rezultāts": new_country,
                    "Kategorija": "Valsts vidējais"
                })
            df_valsts = pd.DataFrame(dati_valsts)
            valsts_chart = alt.Chart(df_valsts).mark_line(point=True).encode(
                x=alt.X("Gads:O", title="Gads"),
                y=alt.Y("Rezultāts:Q", title="Rezultāts (%)", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("Kategorija:N", title="Kategorija"),
                tooltip=["Gads", "Kategorija", "Rezultāts"]
            ).properties(width=600, height=400)
            valsts_chart = valsts_chart.configure_axis(labelFontSize=16, titleFontSize=18) \
                .configure_legend(labelFontSize=16, titleFontSize=18, orient='bottom', direction='horizontal')
            st.altair_chart(valsts_chart, use_container_width=True)

    else:
        st.subheader("Diagnostikas darbi")
        st.warning("No esošajiem VIIS datiem šādu grafiku nevarētu izveidot!")
        klase_diag = st.selectbox("Izvēlies klasi:", ["3. klase", "6. klase"])
        priekšmeti_diag = list(skola["diagnostiskie_eksameni"][klase_diag].keys())
        priekšmets_diag = st.selectbox("Izvēlies priekšmetu:", priekšmeti_diag)

        dati_diag = skola["diagnostiskie_eksameni"][klase_diag][priekšmets_diag]
        dati_diag_saraksts = []
        for gads in dati_diag["skola"].keys():
            school_val = dati_diag["skola"][gads]
            country_val = dati_diag["valsts_vidējais"][gads]
            new_school, new_country = add_noise_if_similar(school_val, country_val)
            dati_diag_saraksts.append({
                "Gads": int(gads),
                "Rezultāts": new_school,
                "Kategorija": "Skola"
            })
            dati_diag_saraksts.append({
                "Gads": int(gads),
                "Rezultāts": new_country,
                "Kategorija": "Valsts vidējais"
            })
        df_diag = pd.DataFrame(dati_diag_saraksts)
        diag_chart = alt.Chart(df_diag).mark_line(point=True).encode(
            x=alt.X("Gads:O", title="Gads"),
            y=alt.Y("Rezultāts:Q", title="Rezultāts (%)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Kategorija:N", title="Kategorija"),
            tooltip=["Gads", "Kategorija", "Rezultāts"]
        ).properties(width=600, height=400)
        diag_chart = diag_chart.configure_axis(labelFontSize=16, titleFontSize=18) \
            .configure_legend(labelFontSize=16, titleFontSize=18, orient='bottom', direction='horizontal')
        st.altair_chart(diag_chart, use_container_width=True)
