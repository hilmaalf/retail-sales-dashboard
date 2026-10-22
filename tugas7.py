import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Analisis Penjualan Ritel",
    layout="wide"
)

# Atur palette warna
WARNA_UTAMA = ["#6E4BA5", "#A681E1", "#29B09D", "#7DEFA1", "#FF2B2B", "#FFABAB"]
WARNA_GENDER = {"Female": "#A681E1", "Male": "#6E4BA5"}

# Baca datanya
@st.cache_data
def muat_data():
    df = pd.read_csv("retail_sales_dataset.csv")
    df.columns = df.columns.str.strip()
    
    # Tipe data Date diubah dr string/object jd datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    
    # Standarisasi tipe data numerik
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Price per Unit"] = pd.to_numeric(df["Price per Unit"], errors="coerce")
    df["Total Amount"] = pd.to_numeric(df["Total Amount"], errors="coerce")
    
    # Bikin kategori Age Group (4 kategori)
    kategori_usia = ["< 25 tahun", "25 - 40 tahun", "41 - 55 tahun", "> 55 tahun"]
    batas_usia = [0, 24, 40, 55, 100]
    
    df["Age Group"] = pd.cut(
        df["Age"], 
        bins=batas_usia, 
        labels=kategori_usia, 
        right=True
    )
    
    return df

df = muat_data()

# Judul n deskripsi
st.title("Dashboard Analisis Penjualan Retail")
st.write("Dashboard interaktif ini menyajikan analisis kinerja penjualan retail berdasarkan transaksi pelanggan, kategori produk, demografi, dan tren periode waktu.")

st.sidebar.header("Filter Dashboard")

# Filter rentang tanggal
tgl_min = df["Date"].min().date()
tgl_maks = df["Date"].max().date()

rentang = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(tgl_min, tgl_maks),
    min_value=tgl_min,
    max_value=tgl_maks
)

if isinstance(rentang, tuple) and len(rentang) == 2:
    awal, akhir = rentang
else:
    awal, akhir = tgl_min, tgl_maks

# Filter kategori produk
pilih_kategori = st.sidebar.multiselect(
    "Kategori Produk",
    options=sorted(df["Product Category"].unique()),
    default=sorted(df["Product Category"].unique())
)

# Filter gender pelanggan
pilih_gender = st.sidebar.multiselect(
    "Gender Pelanggan",
    options=sorted(df["Gender"].unique()),
    default=sorted(df["Gender"].unique())
)

# Filter kelompok usia pelanggan
pilih_usia = st.sidebar.multiselect(
    "Kelompok Usia",
    options=list(df["Age Group"].cat.categories),
    default=list(df["Age Group"].cat.categories)
)

# Filter diterapin ke dataframe
data = df[
    (df["Date"].dt.date >= awal) &
    (df["Date"].dt.date <= akhir) &
    (df["Product Category"].isin(pilih_kategori)) &
    (df["Gender"].isin(pilih_gender)) &
    (df["Age Group"].isin(pilih_usia))
].copy()

if data.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini. Silakan longgarkan filter di sidebar.")
    st.stop()

# Kalkulasi indikator utama KPI
total_pendapatan = data["Total Amount"].sum()
total_transaksi = len(data)
total_unit = data["Quantity"].sum()
rata_transaksi = data["Total Amount"].mean()

# Tampilan KPI (Format USD / $)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Pendapatan", f"${total_pendapatan:,.0f}".replace(",", "."))
k2.metric("Total Transaksi", f"{total_transaksi:,}".replace(",", "."))
k3.metric("Total Unit Terjual", f"{total_unit:,}".replace(",", "."))
k4.metric("Rata-rata Transaksi", f"${rata_transaksi:,.2f}".replace(",", "."))

st.divider()

# Visualisasi 1: Line Chart & Pie Chart
col1, col2 = st.columns([2, 1])

with col1:
    bulanan = (
        data.assign(Bulan=data["Date"].dt.to_period("M").astype(str))
        .groupby("Bulan", as_index=False)["Total Amount"]
        .sum()
        .rename(columns={"Total Amount": "Pendapatan"})
    )
    fig_line = px.line(
        bulanan, x="Bulan", y="Pendapatan", markers=True,
        title="Tren Pendapatan Bulanan"
    )
    fig_line.update_traces(line_color=WARNA_UTAMA[0])
    fig_line.update_layout(yaxis_tickprefix="$")
    st.plotly_chart(fig_line, use_container_width=True)

with col2:
    gender_df = data.groupby("Gender", as_index=False)["Total Amount"].sum().rename(columns={"Total Amount": "Pendapatan"})
    fig_pie = px.pie(
        gender_df, names="Gender", values="Pendapatan",
        title="Proporsi Pendapatan berdasarkan Gender", hole=0.45,
        color="Gender", color_discrete_map=WARNA_GENDER
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Visualisasi 2: Bar Chart Kategori & Bar Chart Kelompok Usia
col3, col4 = st.columns(2)

with col3:
    kat_df = (
        data.groupby("Product Category", as_index=False)["Total Amount"]
        .sum()
        .sort_values("Total Amount", ascending=True)
        .rename(columns={"Total Amount": "Pendapatan", "Product Category": "Kategori"})
    )
    fig_bar = px.bar(
        kat_df, x="Pendapatan", y="Kategori", orientation="h",
        title="Pendapatan per Kategori Produk"
    )
    fig_bar.update_traces(marker_color=WARNA_UTAMA[0])
    fig_bar.update_layout(xaxis_tickprefix="$")
    st.plotly_chart(fig_bar, use_container_width=True)

with col4:
    age_group_df = (
        data.groupby("Age Group", observed=False, as_index=False)
        .size()
        .rename(columns={"size": "Jumlah Transaksi"})
    )
    
    fig_age = px.bar(
        age_group_df, x="Age Group", y="Jumlah Transaksi",
        title="Distribusi Pelanggan berdasarkan Kelompok Usia"
    )
    fig_age.update_traces(
        marker_color=WARNA_UTAMA[1],
        marker_line_color="white",
        marker_line_width=1.5
    )
    fig_age.update_xaxes(title="Kelompok Usia")
    fig_age.update_yaxes(title="Jumlah Transaksi")
    st.plotly_chart(fig_age, use_container_width=True)

st.divider()

# Tabel data hasil filter dan tombol unduh CSV
with st.expander("Lihat Tabel"):
    st.dataframe(data.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

csv = data.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv,
    file_name="retail_sales_filtered.csv",
    mime="text/csv"
)