import streamlit as st
import random
import pandas as pd
from prophet import Prophet
import pulp

# Örnek Veri Üretimi
def generate_sample_data(start_date="2023-01-01", periods=365):
    dates = pd.date_range(start=start_date, periods=periods, freq="D")
    values = [random.randint(10, 100) for _ in range(periods)]
    return pd.DataFrame({"ds": dates, "y": values})

# Prophet ile Zaman Serisi Tahmini
def forecast_demand(data, future_days=7):
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=future_days)
    forecast = model.predict(future)
    forecasted_values = forecast[['ds', 'yhat']].tail(future_days)
    return forecasted_values

# Çalışan İhtiyacını Hesaplama
def calculate_staff_demand(forecasted_values, scaling_factor=0.1):
    demand = {}
    for i, row in forecasted_values.iterrows():
        day_name = row['ds'].strftime("%A")
        demand[day_name] = max(1, int(row['yhat'] * scaling_factor))  # En az 1 çalışan
    return demand

# Vardiya Optimizasyonu
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

    # Kısıtlar: Çalışanların izin günleri
    for c in calisanlar:
        for g in izinli_gunler[c]:
            problem += vardiyalar[(c, g)] == 0, f"Izin_{c}_{g}"

    # Kısıtlar: Çalışanların maksimum çalışma günleri
    for c in calisanlar:
        problem += pulp.lpSum(vardiyalar[(c, g)] for g in gunler) <= max_calismalar[c], f"Max_{c}"

    # Problemi çöz
    problem.solve()

    # Optimizasyon sonrası vardiya planı ve maaş
    vardiya_plani = {g: [] for g in gunler}
    optimizasyon_maas = 0
    for g in gunler:
        for c in calisanlar:
            if vardiyalar[(c, g)].value() == 1:
                vardiya_plani[g].append(c)
                optimizasyon_maas += gunluk_ucret

    return vardiya_plani, optimizasyon_maas

# Streamlit Uygulaması
st.title("Vardiya Planlama ve Optimizasyon Uygulaması")

# Kullanıcıdan Girdi Al
num_employees = st.number_input("Çalışan Sayısını Giriniz", min_value=1, step=1)
calisanlar = [f"Çalışan {i+1}" for i in range(num_employees)]
izinli_gunler = {c: st.multiselect(f"{c} için izin günleri seçin", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]) for c in calisanlar}
max_calismalar = {c: st.number_input(f"{c} için maksimum çalışma günü", min_value=1, step=1) for c in calisanlar}
gunluk_ucret = st.number_input("Günlük Ücret", min_value=0, step=100)

# Tahmin Verileri
data = generate_sample_data()
forecasted_data = forecast_demand(data)
st.subheader("7 Günlük Talep Tahmini")
st.dataframe(forecasted_data)

# Çalışan İhtiyacı Hesaplama
gunler = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)

# Vardiya Optimizasyonu
vardiya_plani, optimizasyon_maas = optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret)

# Optimizasyon Sonuçları
toplam_maas_oncesi = sum(gunluk_ucret * len(calisanlar) for _ in gunler)
kar = toplam_maas_oncesi - optimizasyon_maas

st.subheader("Optimizasyon Sonuçları")
st.write(f"Optimizasyon Öncesi Maliyet: {toplam_maas_oncesi} TL")
st.write(f"Optimizasyon Sonrası Maliyet: {optimizasyon_maas} TL")
st.write(f"Kazanç: {kar} TL")

# Vardiya Planı Gösterimi
st.subheader("Vardiya Planı")
vardiya_df = pd.DataFrame.from_dict(vardiya_plani, orient="index").T
vardiya_df.columns = gunler
st.dataframe(vardiya_df)
