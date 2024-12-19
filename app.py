import random
import pandas as pd
import pulp
import streamlit as st
from prophet import Prophet

# 1. Rastgele veri üretimi
@st.cache
def generate_sample_data(start_date="2023-01-01", periods=365):
    dates = pd.date_range(start=start_date, periods=periods, freq="D")
    values = [random.randint(10, 100) for _ in range(periods)]
    return pd.DataFrame({"ds": dates, "y": values})

# 2. Prophet ile talep tahmini
@st.cache
def forecast_demand(data, future_days=7):
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=future_days)
    forecast = model.predict(future)
    return forecast[['ds', 'yhat']].tail(future_days)

# 3. Tahminlere göre çalışan ihtiyacını belirleme
def calculate_staff_demand(forecasted_values, scaling_factor=0.1):
    demand = {}
    days_of_week = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    for i, row in forecasted_values.iterrows():
        day_name = days_of_week[i % 7]
        demand[day_name] = max(1, int(row['yhat'] * scaling_factor))
    return demand

# 4. Optimize vardiya planlaması
def optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret):
    # Problem tanımı
    problem = pulp.LpProblem("Vardiya_Planlama", pulp.LpMinimize)

    # Karar değişkenleri
    vardiyalar = pulp.LpVariable.dicts("Vardiya", [(c, g) for c in calisanlar for g in gunler], cat="Binary")

    # Amaç fonksiyonu
    problem += pulp.lpSum(vardiyalar[(c, g)] * gunluk_ucret for c in calisanlar for g in gunler)

    # Her gün yeterli çalışan atanmalı
    for g in gunler:
        problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar) >= calisan_ihtiyaci[g], f"Gun_{g}_Kisit"

    # Çalışanların izin günleri dikkate alınmalı
    for c in calisanlar:
        for g in izinli_gunler[c]:
            problem += vardiyalar[(c, g)] == 0, f"Izin_{c}_{g}"

    # Çalışanların haftalık maksimum çalışma günleri
    for c in calisanlar:
        problem += pulp.lpSum(vardiyalar[(c, g)] for g in gunler) <= max_calismalar[c], f"Max_{c}"

    # Problemi çöz
    problem.solve()

    # Optimizasyon sonrası plan
    plan = {}
    for g in gunler:
        plan[g] = [c for c in calisanlar if vardiyalar[(c, g)].value() == 1]

    # Optimizasyon sonrası maliyet
    optimizasyon_maas = pulp.value(problem.objective)
    return plan, optimizasyon_maas

# Streamlit uygulaması
st.title("Vardiya Optimizasyon Uygulaması")

# Çalışan sayısı
calisan_sayisi = st.number_input("Çalışan Sayısını Girin:", min_value=1, value=5, step=1)
calisanlar = [f"Çalışan_{i+1}" for i in range(calisan_sayisi)]

# Çalışan izin günleri
izinli_gunler = {}
gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
for calisan in calisanlar:
    izinli_gunler[calisan] = st.multiselect(f"{calisan} için izin günlerini seçin:", gunler)

# Maksimum çalışma günleri
max_calismalar = {}
for calisan in calisanlar:
    max_calismalar[calisan] = st.number_input(f"{calisan} için maksimum çalışma gününü girin:", min_value=1, max_value=7, value=5)

# Günlük ücret
gunluk_ucret = st.number_input("Çalışan başına günlük ücreti girin (TL):", min_value=1, value=1000, step=100)

# Rastgele talep tahmini
sample_data = generate_sample_data()
forecasted_data = forecast_demand(sample_data)
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)
st.subheader("7 Günlük Tahmini Talep")
st.write(pd.DataFrame(calisan_ihtiyaci.items(), columns=["Gün", "Çalışan İhtiyacı"]))

# Optimizasyon
if st.button("Vardiya Optimizasyonunu Başlat"):
    plan, optimizasyon_maas = optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret)

    # Optimizasyon öncesi maliyet
    optimize_oncesi_maas = sum(calisan_ihtiyaci[g] * gunluk_ucret for g in gunler)

    # Kar hesaplama
    kar = optimize_oncesi_maas - optimizasyon_maas

    # Sonuçlar
    st.subheader("Optimizasyon Sonuçları")
    st.write(f"Optimizasyon Öncesi Toplam Maaş: {optimize_oncesi_maas} TL")
    st.write(f"Optimizasyon Sonrası Toplam Maaş: {optimizasyon_maas} TL")
    st.write(f"Optimizasyondan Kazanılan: {kar} TL")

    # Vardiya planı
    st.subheader("Vardiya Planı")
    vardiya_tablosu = pd.DataFrame.from_dict(plan, orient="index", columns=[f"Çalışan {i+1}" for i in range(len(calisanlar))])
    st.write(vardiya_tablosu)
