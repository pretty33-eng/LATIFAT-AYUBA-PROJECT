import streamlit as st
import pandas as pd
import altair as alt

@st.cache_data
def load_data():
    df = pd.read_csv("Air Crash Full Data Updated_2024.csv")

    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_") \
        .str.replace("(", "", regex=False).str.replace(")", "", regex=False) \
        .str.replace("/", "_")

    # Fill essential missing values
    df['country_region'] = df['country_region'].fillna("Unknown")
    df['operator'] = df['operator'].fillna('Unknown')
    df['aircraft_manufacturer'] = df['aircraft_manufacturer'].fillna('Unknown')

    # Convert numeric columns
    df['year'] = pd.to_numeric(df.get('year', pd.Series(dtype='float64')), errors='coerce')
    df['day'] = pd.to_numeric(df.get('day', pd.Series(dtype='float64')), errors='coerce')
    df['abroad'] = pd.to_numeric(df.get('abroad', pd.Series(dtype='float64')), errors='coerce')
    df['fatalities_air'] = pd.to_numeric(df.get('fatalities_air', pd.Series(dtype='float64')), errors='coerce')
    df['ground'] = pd.to_numeric(df.get('ground', pd.Series(dtype='float64')), errors='coerce')

    # Map month names to numbers
    month_map = {
        'January': 1, 'Feburary': 2, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9,
        'October': 10, 'November': 11, 'December': 12
    }
    df["month_num"] = df['month'].map(month_map)

    # Create a datetime column
    df['month_date'] = pd.to_datetime(
        dict(year=df['year'], month=df['month_num'], day=1),
        errors="coerce"
    )
    df['month_name'] = df['month_date'].dt.month_name()

    # Add decade/period bins
    bins = [1908, 1920, 1932, 1944, 1956, 1968, 1980, 1992, 2004, 2016, 2020, 2024]
    labels = [
        "Early 1910s", "Mid 1920s", "Late 1930s", "Early 1940s",
        "Mid 1950s", "Late 1960s", "Early 1970s", "Late 1980s",
        "Early 2000s", "Mid 2010s", "Early 2020s"
    ]
    df['year_bin'] = pd.cut(df['year'], bins=bins, labels=labels, include_lowest=True)

    # Drop duplicates
    df.drop_duplicates(inplace=True)

    return df

# Load data
df = load_data()

# Streamlit app layout
st.title('Air Crash Data Analysis')
st.sidebar.header('Filters')

# Sidebar filters
filters = {
    "year": df["year"].dropna().unique().tolist(),
    "quarter": df["quarter"].dropna().unique().tolist() if "quarter" in df.columns else [],
    "month": df["month"].dropna().unique().tolist(),
}

# User selections
selected_filters = {}
for key, options in filters.items():
    if options:
        selected_filters[key] = st.sidebar.multiselect(key.capitalize(), sorted(options))

# Apply filters
filtered_df = df.copy()
for key, selected_values in selected_filters.items():
    if selected_values:
        filtered_df = filtered_df[filtered_df[key].isin(selected_values)]

# Display table
st.dataframe(filtered_df.head())
st.write("Columns:", filtered_df.columns.tolist())

# Metrics
no_of_fatalities = len(filtered_df)
total_year = filtered_df["year"].sum()
sum_of_fatalities = filtered_df["fatalities_air"].sum()
no_of_aircrafts = filtered_df["aircraft"].nunique() if "aircraft" in filtered_df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Fatality Records", no_of_fatalities)
col2.metric("Sum of Years", int(total_year))
col3.metric("Total Fatalities (Air)", int(sum_of_fatalities))
col4.metric("Unique Aircraft", int(no_of_aircrafts))

# Top 5 years with highest fatalities
st.subheader("Top 5 Years With Highest Fatalities")
crashes_per_year = (
    filtered_df.groupby("year")["fatalities_air"]
    .sum()
    .nlargest(5)
    .reset_index()
)
st.write(crashes_per_year)

if not crashes_per_year.empty:
    st.subheader("Top 5 Yearly Fatalities (Bar Chart)")
    chart = alt.Chart(crashes_per_year).mark_bar().encode(
        x=alt.X('fatalities_air:Q', title="Total Fatalities"),
        y=alt.Y("year:N", sort='-x', title="Year"),
        color=alt.Color("year:N", scale=alt.Scale(scheme='category20'), legend=None)
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No data to display for the selected filters.")

# Pie Chart - Top 5 Countries
top_countries = (
    filtered_df.groupby("country_region")["fatalities_air"]
    .sum().nlargest(5).reset_index()
)
st.subheader("Top 5 Countries by Fatalities")
pie_chart = alt.Chart(top_countries).mark_arc().encode(
    theta=alt.Theta(field="fatalities_air", type="quantitative"),
    color=alt.Color("country_region:N", scale=alt.Scale(scheme='dark2')),
    tooltip=["country_region:N", "fatalities_air:Q"]
).properties(height=300)
st.altair_chart(pie_chart, use_container_width=True)

# Monthly Distribution
st.subheader("Monthly Distribution of Fatalities")
monthly_fatalities = ( 
    filtered_df.groupby("month_name")["fatalities_air"]
    .sum()
    .reindex([
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ])
    .reset_index()
    .dropna()
)
bar_month = alt.Chart(monthly_fatalities).mark_bar().encode(
    x=alt.X("month_name:N", sort=list(monthly_fatalities["month_name"]), title="Month"),
    y=alt.Y("fatalities_air:Q", title="Total Fatalities"),
    color=alt.Color("month_name:N", scale=alt.Scale(scheme='tableau20'), legend=None)
)
st.altair_chart(bar_month, use_container_width=True)

# Top 5 Manufacturers
st.subheader("Top 5 Aircraft Manufacturers by Fatalities")
top_manufacturers = (
    filtered_df.groupby("aircraft_manufacturer")["fatalities_air"]
    .sum().nlargest(5).reset_index()
)
bar_manufacturer = alt.Chart(top_manufacturers).mark_bar().encode(
    x=alt.X("fatalities_air:Q", title="Total Fatalities"),
    y=alt.Y("aircraft_manufacturer:N", sort='-x', title="Aircraft Manufacturer"),
    color=alt.Color("aircraft_manufacturer:N", scale=alt.Scale(scheme='category10'), legend=None)
)
st.altair_chart(bar_manufacturer, use_container_width=True)

# Decade distribution
st.subheader("Air Crashes by Decade/Period")
decade_counts = (
    filtered_df.groupby("year_bin")["fatalities_air"]
    .sum()
    .reset_index()
    .dropna()
)
bar_decade = alt.Chart(decade_counts).mark_bar().encode(
    x=alt.X("year_bin:N", title="Decade/Period"),
    y=alt.Y("fatalities_air:Q", title="Total Fatalities"),
    color=alt.Color("year_bin:N", scale=alt.Scale(scheme='set2'), legend=None)
)
st.altair_chart(bar_decade, use_container_width=True)
