import random
import pandas as pd
from prophet import Prophet
import pulp
import streamlit as st

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
    for i, row in enumerate(forecasted_values.itertuples()):
        day_name = days_of_week[i % 7]
        demand[day_name] = max(1, int(row.yhat * scaling_factor))  # En az 1 çalışan gereksinimi
    return demand

# 4. Adım: Optimize Vardiya Planlaması
def optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret):
    problem = pulp.LpProblem("Vardiya_Planlama", pulp.LpMinimize)

    # Karar değişkenleri
    vardiyalar = pulp.LpVariable.dicts("Vardiya", [(c, g) for c in calisanlar for g in gunler], cat="Binary")

    # Amaç fonksiyonu
    problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar for g in gunler), "Toplam_Vardiya"

    # Kısıtlar
    for g in gunler:
        problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar) >= calisan_ihtiyaci[g], f"Gün_{g}_Kısıtı"
    for c in calisanlar:
        for g in izinli_gunler.get(c, []):
            problem += vardiyalar[(c, g)] == 0, f"Izin_{c}_{g}"
        problem += pulp.lpSum(vardiyalar[(c, g)] for g in gunler) <= max_calismalar.get(c, 0), f"Max_{c}"

    problem.solve()

    plan = {}
    for g in gunler:
        plan[g] = [c for c in calisanlar if vardiyalar[(c, g)].value() == 1]

    optimizasyon_maas = sum(len(plan[g]) * gunluk_ucret for g in gunler)
    return plan, optimizasyon_maas

# Streamlit Arayüzü
st.title("Vardiya Planlama Optimizasyonu")

# Kullanıcıdan girişler
calisan_sayisi = st.number_input("Çalışan Sayısını Girin", min_value=1, step=1)
izin_gunleri = st.multiselect("Çalışanların İzin Günlerini Belirleyin", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
max_calisma_gunu = st.number_input("Maksimum Çalışma Günü Sayısını Girin", min_value=1, step=1)
gunluk_ucret = st.number_input("Günlük Ücreti Girin (TL)", min_value=1, step=1)

# Rastgele çalışan isimleri
calisanlar = [f"Çalışan_{i+1}" for i in range(calisan_sayisi)]
izinli_gunler = {c: izin_gunleri for c in calisanlar}
max_calismalar = {c: max_calisma_gunu for c in calisanlar}

# Örnek veri üretimi ve tahmin
sample_data = generate_sample_data()
forecasted_data = forecast_demand(sample_data)
st.subheader("7 Günlük Tahmini Talep")
st.dataframe(forecasted_data)

# Çalışan ihtiyacını belirleme
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)

# Optimizasyon
plan, optimizasyon_maas = optimize_vardiya(calisanlar, calisan_ihtiyaci.keys(), calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret)

# Sonuçların Gösterimi
st.subheader("Optimizasyon Sonuçları")
st.write("Çalışan Planı:")
st.json(plan)
st.write(f"Optimizasyon Sonrası Toplam Maaş: {optimizasyon_maas} TL")
