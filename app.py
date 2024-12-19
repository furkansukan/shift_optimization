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

    # Optimizasyon sonrası sonuçlar
    vardiya_plan = {g: [] for g in gunler}
    toplam_maas = 0
    for g in gunler:
        for c in calisanlar:
            if vardiyalar[(c, g)].value() == 1:
                vardiya_plan[g].append(c)
                toplam_maas += gunluk_ucret

    return toplam_maas, vardiya_plan

# Streamlit Uygulaması
st.title("Vardiya Planlama ve Optimizasyon")

# Kullanıcıdan veri alma
st.header("Girdi Bilgileri")
num_employees = st.number_input("Çalışan Sayısı", min_value=1, value=5, step=1)
employees = [f"Çalışan_{i+1}" for i in range(num_employees)]
weekly_days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

st.subheader("Çalışanların İzin Günleri")
off_days = {emp: st.multiselect(f"{emp} için izin günleri seçin", weekly_days) for emp in employees}

max_work_days = {emp: st.number_input(f"{emp} için maksimum çalışma günü", min_value=1, max_value=7, value=5) for emp in employees}
daily_wage = st.number_input("Günlük Ücret (TL)", min_value=0, value=1000, step=100)

# 7 günlük talep tahmini
st.header("7 Günlük Talep Tahmini")
sample_data = generate_sample_data()
forecasted_data = forecast_demand(sample_data)
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)
st.dataframe(forecasted_data)
st.write("Çalışan İhtiyacı:", calisan_ihtiyaci)

# Optimizasyon
if st.button("Vardiya Optimizasyonu Yap"):
    gunler = weekly_days
    total_cost_before = sum(calisan_ihtiyaci.values()) * daily_wage
    total_cost_after, vardiya_plan = optimize_vardiya(employees, gunler, calisan_ihtiyaci, off_days, max_work_days, daily_wage)

    st.subheader("Optimizasyon Sonuçları")
    st.write(f"Optimizasyon Öncesi Toplam Maliyet: {total_cost_before} TL")
    st.write(f"Optimizasyon Sonrası Toplam Maliyet: {total_cost_after} TL")
    st.write(f"Kazanılan Kar: {total_cost_before - total_cost_after} TL")
    st.write("Vardiya Planı:")
    st.json(vardiya_plan)
