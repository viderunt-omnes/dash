import streamlit as st
import pandas as pd
import altair as alt
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.title("Eksāmenu rezultātu analīzes rīks")
st.write("Ar šo instrumentu var aplūkot vizuāli VIIS datubāzē esošos rezultātus par centralizētajiem eksāmeniem. Ja šeit kāds eksāmens nav atrodams, tas nozīmē, ka tas **nav** bijis centralizēts - piemēram, pamatskolā daudzi eksāmeni līdz 2022. gadam netika vērtēti centralizēti.")
st.write("Ar filtru palīdzību var atlasīt konkrētu skolu, gadu un eksāmenu, ko aplūkot. Stabiņu diagrammā varēs redzēt salīdzinājumu ar valsts vidējo rezultātu.")

# =============================================================================
# 1. Load the CSV Data from a Local File
# =============================================================================
csv_file = "https://www.dropbox.com/scl/fi/o7j7q5hlq9i04s9tcvj8q/Web-Intelligence-1.csv?rlkey=e05vhykdwv6zrprmx1i5n4fml&dl=1"
try:
    df = pd.read_csv(csv_file)
except Exception as e:
    st.error(f"Error reading the CSV file: {e}")
    st.stop()

# Clean column names (remove any leading/trailing spaces)
df.columns = df.columns.str.strip()

# Filter data to include only rows for "Centralizēts eksāmens"
df = df[df["Pārbaudījuma tips"] == "Centralizēts eksāmens"]

if df.empty:
    st.error("No data available for 'Centralizēts eksāmens' in the CSV file.")
    st.stop()

# =============================================================================
# 2. Sidebar: Filtering Options (School, Year, School Type, Exam)
# =============================================================================
st.sidebar.header("Filtri")

# --- School Dropdown with Placeholder ---
valid_schools = df["Iestādes nosaukums"].dropna().unique()
if len(valid_schools) == 0:
    st.error("No school data available for 'Centralizēts eksāmens'.")
    st.stop()

# Prepend a placeholder to the list of schools.
schools_options = ["Izvēlies skolu"] + sorted(valid_schools)
selected_school = st.sidebar.selectbox("Izvēlies skolu:", schools_options)

# If the placeholder is selected, display a landing page message.
if selected_school == "Izvēlies skolu":
    st.write("**Lūdzu, izvēlies skolu no kreisās puses, lai turpinātu analīzi.**")
    st.stop()

filtered_school = df[df["Iestādes nosaukums"] == selected_school]
if filtered_school.empty:
    st.error("No data available for the selected school.")
    st.stop()

# --- Year Dropdown (based on the selected school) ---
valid_years = filtered_school["Mācību gads"].dropna().unique()
if len(valid_years) == 0:
    st.error("No year data available for the selected school.")
    st.stop()

years_sorted = sorted(valid_years)
# Default to the last (highest) year in the list.
selected_year = st.sidebar.selectbox("Izvēlies gadu:", years_sorted, index=len(years_sorted) - 1)
filtered_year = filtered_school[filtered_school["Mācību gads"] == selected_year]
if filtered_year.empty:
    st.error("No data available for the selected year.")
    st.stop()

# --- School Type Filter ---
# Define groups: "Pamatskola" includes classes 1-9, "Vidusskola" includes classes 10-12.
school_type = st.sidebar.selectbox("Izvēlies izglītības līmeni:", ["Pamatskola", "Vidusskola"])

filtered_year = filtered_year.copy()
filtered_year["Klases pakāpe_numeric"] = pd.to_numeric(filtered_year["Klases pakāpe"], errors='coerce')

if school_type == "Pamatskola":
    filtered_group = filtered_year[filtered_year["Klases pakāpe_numeric"].between(1, 9)]
else:  # Vidusskola
    filtered_group = filtered_year[filtered_year["Klases pakāpe_numeric"].between(10, 12)]

if filtered_group.empty:
    st.error(f"No data available for the selected school type: {school_type}.")
    st.stop()

# --- Exam Dropdown (for the selected school, year, and school type) ---
# Define a helper function that returns the appropriate exam name.
def get_exam_name(row):
    if row["Pārbaudījuma nosaukums"] == "N/D":
        try:
            year = int(row["Mācību gads"])
        except:
            year = 0
        # For years prior to 2022, remove the prefix "Centralizētais eksāmens "
        if year < 2022:
            prefix = "Centralizētais eksāmens "
            exam_subject = row["Pārbaudījuma mācību priekšmeta nosaukums"]
            if isinstance(exam_subject, str) and exam_subject.startswith(prefix):
                exam_subject = exam_subject[len(prefix):]
            # Capitalize the first letter of the remaining string.
            return exam_subject.capitalize() if isinstance(exam_subject, str) else exam_subject
        else:
            return row["Pārbaudījuma mācību priekšmeta nosaukums"]
    else:
        return row["Pārbaudījuma nosaukums"]

filtered_group = filtered_group.copy()
filtered_group["Exam"] = filtered_group.apply(get_exam_name, axis=1)

valid_exams = filtered_group["Exam"].dropna().unique()
if len(valid_exams) == 0:
    st.error("No exam data available for the selected school, year, and school type.")
    st.stop()

selected_exam = st.sidebar.selectbox("Izvēlies eksāmenu:", sorted(valid_exams))

# =============================================================================
# 3. Display the School’s Address and Map Location
# =============================================================================
# Use the first record for the school (address is independent of class level)
school_info = filtered_school.iloc[0]
address = school_info["Iestādes juridiskās adrese"]

# Display the header with the selected school's name.
st.subheader(f"Izvēlētā skola: {selected_school}")
st.write("**Adrese:**", address)

@st.cache_resource
def geocode_address(addr):
    geolocator = Nominatim(user_agent="exam_dashboard")
    geocode_fn = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    location = geocode_fn(addr)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

lat, lon = geocode_address(address)
if lat is not None and lon is not None:
    location_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
    st.map(location_df)
else:
    st.write("Nespējām automātiski atrast skolu kartē pēc tās adreses.")

# =============================================================================
# 4. Compute and Plot Normalized Grouped Bar Chart (School vs Country)
# =============================================================================
st.subheader("Eksāmena rezultāti - skola vs. valsts vidējais")

# --- School Exam Results ---
exam_results = filtered_group[filtered_group["Exam"] == selected_exam]

# Compute the total number of students (for the selected school and exam)
total_school_count = len(exam_results)
st.markdown(f"**Kopējais eksāmena kārtotāju skaits: {total_school_count} kārtotāji**")

if exam_results.empty:
    st.write("No exam results available for the selected school options.")
else:
    # Define bins: 0-5, 5-10, ..., 95-100
    bins = list(range(0, 105, 5))
    labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins) - 1)]

    # Bin the school results and compute counts and normalized frequencies
    school_bins = pd.cut(exam_results["Procenti"], bins=bins, right=False, include_lowest=True)
    school_counts = school_bins.value_counts(sort=False)
    school_normalized = school_counts / school_counts.sum()

    # Create a DataFrame for the school group.
    school_df = pd.DataFrame({
        'Exam_Percentage_Bin': labels,
        'Normalized_Frequency': school_normalized.values,
        'Raw_Count': school_counts.values,
        'Group': 'School'
    })

    # --- Country Exam Results ---
    # Apply the exam naming logic on the entire dataset.
    df_country = df.copy()
    df_country["Exam"] = df_country.apply(get_exam_name, axis=1)
    country_exam_results = df_country[
        (df_country["Mācību gads"] == selected_year) &
        (df_country["Exam"] == selected_exam)
    ]

    if country_exam_results.empty:
        st.write("No country exam results available for the selected options.")
        country_df = pd.DataFrame(columns=['Exam_Percentage_Bin', 'Normalized_Frequency', 'Group', 'Raw_Count'])
    else:
        country_bins = pd.cut(country_exam_results["Procenti"], bins=bins, right=False, include_lowest=True)
        country_counts = country_bins.value_counts(sort=False)
        country_normalized = country_counts / country_counts.sum()
        country_df = pd.DataFrame({
            'Exam_Percentage_Bin': labels,
            'Normalized_Frequency': country_normalized.values,
            'Raw_Count': country_counts.values,
            'Group': 'Country'
        })

    # Combine the two dataframes.
    combined_df = pd.concat([school_df, country_df], ignore_index=True)

    # Create the grouped bar chart with enlarged fonts.
    chart_grouped = alt.Chart(combined_df).mark_bar().encode(
        x=alt.X('Exam_Percentage_Bin:N', title='Intervāls'),
        xOffset=alt.X('Group:N', title=''),
        y=alt.Y('Normalized_Frequency:Q', title='Biežums, %', axis=alt.Axis(format='%')),
        color=alt.Color('Group:N',
                        scale=alt.Scale(domain=['School', 'Country'],
                                        range=['blue', 'orange'])),
        tooltip=[
            alt.Tooltip('Group:N', title='Grupa'),
            alt.Tooltip('Exam_Percentage_Bin:N', title='Rezultātu intervāls, %'),
            alt.Tooltip('Normalized_Frequency:Q', format='.2%', title='Biežums, %'),
            alt.Tooltip('Raw_Count:Q', title='Kārtotāju skaits')
        ]
    ).properties(
        width=350,
        height=400,
        title="Eksāmena rezultāti - skola vs. valsts vidējais"
    ).configure_axis(
        labelFontSize=16,
        titleFontSize=18
    ).configure_title(
        fontSize=20
    )

    st.altair_chart(chart_grouped, use_container_width=True)
