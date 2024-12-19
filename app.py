import streamlit as st
import random
import pandas as pd
from prophet import Prophet
import pulp

# 1. Adım: Örnek Veri Üretimi
def generate_sample_data(start_date="2023-01-01", periods=365):
    dates = pd.date_range(start=start_date, periods=periods, freq="D")
    values = [random.randint(10, 100) for _ in range(periods)]
    return pd.DataFrame({"ds": dates, "y": values})

# 2. Adım: Prophet ile Zaman Serisi Tahmini
def forecast_demand(data, future_days=7):
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=future_days)
    forecast = model.predict(future)
    forecasted_values = forecast[['ds', 'yhat']].tail(future_days)
    return forecasted_values

# 3. Adım: Tahminlere Göre Çalışan İhtiyacını Belirleme
def calculate_staff_demand(forecasted_values, scaling_factor=0.1):
    demand = {}
    days_of_week = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    for i, row in forecasted_values.iterrows():
        day_name = days_of_week[i % 7]
        demand[day_name] = max(1, int(row['yhat'] * scaling_factor))  # En az 1 çalışan gereksinimi
    return demand

# 4. Adım: Optimize Vardiya Planlaması
def optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret):
    # Optimizasyon yapılmadan önceki hesaplama
    def optimize_oncesi():
        toplam_maas = 0
        for g in gunler:
            gunun_calisanlari = 0
            for c in calisanlar:
                if g not in izinli_gunler[c]:  # İzinli olmayan çalışanlar
                    gunun_calisanlari += 1
            toplam_maas += gunun_calisanlari * gunluk_ucret
        return toplam_maas

    # Problem tanımı
    problem = pulp.LpProblem("Vardiya_Planlama", pulp.LpMinimize)

    # Karar değişkenleri
    vardiyalar = pulp.LpVariable.dicts("Vardiya", [(c, g) for c in calisanlar for g in gunler], cat="Binary")

    # Amaç fonksiyonu
    problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar for g in gunler), "Toplam_Vardiya"

    # Kısıtlar: Her gün yeterli çalışan atanmalı
    for g in gunler:
        problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar) >= calisan_ihtiyaci[g], f"Gün_{g}_Kısıtı"

    # Kısıtlar: Çalışanların izin günleri dikkate alınmalı
    for c in calisanlar:
        for g in izinli_gunler[c]:
            problem += vardiyalar[(c, g)] == 0, f"Izin_{c}_{g}"

    # Kısıtlar: Çalışanların haftalık maksimum çalışma saatleri
    for c in calisanlar:
        problem += pulp.lpSum(vardiyalar[(c, g)] for g in gunler) <= max_calismalar[c], f"Max_{c}"

    # Problemi çöz
    problem.solve()

    # Optimizasyon sonrası vardiya planı
    vardiya_plani = {g: [] for g in gunler}
    optimizasyon_maas = 0
    for g in gunler:
        for c in calisanlar:
            if vardiyalar[(c, g)].value() == 1:
                vardiya_plani[g].append(c)
                optimizasyon_maas += gunluk_ucret

    # Optimizasyon öncesi ve sonrası kar farkı
    optimizasyon_oncesi_maas = optimize_oncesi()
    kar = optimizasyon_oncesi_maas - optimizasyon_maas
    return vardiya_plani, optimizasyon_oncesi_maas, optimizasyon_maas, kar

# Streamlit Arayüzü
st.title("Vardiya Planlama ve Optimizasyon Uygulaması")

# Kullanıcı Girdileri
num_employees = st.number_input("Çalışan Sayısını Girin:", min_value=1, max_value=20, value=8)
gunluk_ucret = st.number_input("Günlük Ücret (TL):", min_value=100, step=50, value=1000)
max_gun = st.slider("Maksimum Çalışma Günü:", min_value=1, max_value=7, value=5)

# Çalışanların isimleri ve izin günleri
calisanlar = [f"Çalışan {i+1}" for i in range(num_employees)]
izinli_gunler = {}
gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
for calisan in calisanlar:
    izinli_gunler[calisan] = st.multiselect(f"{calisan} için izin günleri seçin:", gunler)

# Prophet ile talep tahmini
sample_data = generate_sample_data()
forecasted_data = forecast_demand(sample_data)
st.subheader("Tahmin Edilen 7 Günlük Talep")
st.table(forecasted_data)

# Çalışan ihtiyacı hesaplama
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)

# Optimizasyon
max_calismalar = {c: max_gun for c in calisanlar}
vardiya_plani, optimizasyon_oncesi_maas, optimizasyon_maas, kar = optimize_vardiya(
    calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret
)

# Sonuçlar
st.subheader("Optimizasyon Sonuçları")
st.write(f"Optimizasyon Öncesi Toplam Maaş: {optimizasyon_oncesi_maas} TL")
st.write(f"Optimizasyon Sonrası Toplam Maaş: {optimizasyon_maas} TL")
st.write(f"Kazanılan Kar: {kar} TL")

st.subheader("Vardiya Planı")
for g, calisanlar in vardiya_plani.items():
    st.write(f"**{g}:** {', '.join(calisanlar)}")
