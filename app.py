import streamlit as st
import random
import pandas as pd
from prophet import Prophet
import pulp

# Örnek veri üretimi
def generate_sample_data(start_date="2023-01-01", periods=365):
    dates = pd.date_range(start=start_date, periods=periods, freq="D")
    values = [random.randint(10, 100) for _ in range(periods)]
    return pd.DataFrame({"ds": dates, "y": values})

# Prophet ile tahmin
def forecast_demand(data, future_days=7):
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=future_days)
    forecast = model.predict(future)
    forecasted_values = forecast[['ds', 'yhat']].tail(future_days)
    return forecasted_values

# Talebe göre çalışan ihtiyacı
def calculate_staff_demand(forecasted_values, scaling_factor=0.1):
    demand = {}
    days_of_week = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    for i, row in forecasted_values.iterrows():
        day_name = days_of_week[i % 7]
        demand[day_name] = max(1, int(row['yhat'] * scaling_factor))  # En az 1 çalışan
    return demand

# Optimize vardiya planlaması
def optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret):
    # Problem tanımı
    problem = pulp.LpProblem("Vardiya_Planlama", pulp.LpMinimize)

    # Karar değişkenleri
    vardiyalar = pulp.LpVariable.dicts("Vardiya", [(c, g) for c in calisanlar for g in gunler], cat="Binary")

    # Amaç fonksiyonu
    problem += pulp.lpSum(vardiyalar[(c, g)] * gunluk_ucret for c in calisanlar for g in gunler), "Toplam_Maliyet"

    # Kısıtlar: Her gün yeterli çalışan atanmalı
    for g in gunler:
        problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar) >= calisan_ihtiyaci[g], f"Gün_{g}_Kısıtı"

    # Kısıtlar: Çalışanların izin günleri dikkate alınmalı
    for c in calisanlar:
        for g in izinli_gunler[c]:
            problem += vardiyalar[(c, g)] == 0, f"Izin_{c}_{g}"

    # Kısıtlar: Çalışanların haftalık maksimum çalışma günleri
    for c in calisanlar:
        problem += pulp.lpSum(vardiyalar[(c, g)] for g in gunler) <= max_calismalar[c], f"Max_{c}"

    # Problemi çöz
    problem.solve()

    # Sonuçları düzenle
    vardiya_plani = {g: [] for g in gunler}
    toplam_maas = 0
    for g in gunler:
        for c in calisanlar:
            if vardiyalar[(c, g)].value() == 1:
                vardiya_plani[g].append(c)
                toplam_maas += gunluk_ucret
    return vardiya_plani, toplam_maas

# Streamlit Uygulaması
st.title("Vardiya Planlama ve Optimizasyonu")

# Kullanıcıdan girişler
calisan_sayisi = st.number_input("Çalışan Sayısı:", min_value=1, value=5, step=1)
calisanlar = [f"Çalışan {i+1}" for i in range(calisan_sayisi)]
izin_gunleri = st.multiselect("İzin Günleri:", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
max_calisma_gunu = st.slider("Haftalık Maksimum Çalışma Günü:", min_value=1, max_value=7, value=5)
gunluk_ucret = st.number_input("Günlük Ücret (TL):", min_value=0, value=1000, step=50)

# Rastgele talep tahmini
sample_data = generate_sample_data()
forecasted_data = forecast_demand(sample_data)
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)

forecasted_data = forecast_demand(sample_data)
st.subheader("7 Günlük Tahmini Talep")
st.dataframe(forecasted_data)

# Optimizasyon
gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
izinli_gunler = {c: izin_gunleri for c in calisanlar}
max_calismalar = {c: max_calisma_gunu for c in calisanlar}
vardiya_plani, optimizasyon_maas = optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret)

# Optimizasyon sonuçlarını göster
st.subheader("Optimizasyon Sonuçları")
st.write(f"Optimizasyon Sonrası Toplam Maaş: {optimizasyon_maas} TL")

# Çalışma planını göster
st.subheader("Vardiya Planı")
for g, calisan_listesi in vardiya_plani.items():
    st.write(f"**{g}:** {', '.join(calisan_listesi)}")
