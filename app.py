import streamlit as st
import random
import pandas as pd
from prophet import Prophet
import pulp

# 1. Rastgele isim üretimi
def generate_random_names(count):
    return [f"Çalışan_{i+1}" for i in range(count)]

# 2. Prophet ile talep tahmini
def forecast_demand(data, future_days=7):
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=future_days)
    forecast = model.predict(future)
    return forecast[['ds', 'yhat']].tail(future_days)

# 3. Çalışan ihtiyacını belirleme
def calculate_staff_demand(forecasted_values, scaling_factor=0.1):
    demand = {}
    days_of_week = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    for i, row in forecasted_values.iterrows():
        day_name = days_of_week[i % 7]
        demand[day_name] = max(1, int(row['yhat'] * scaling_factor))
    return demand

# 4. Vardiya optimizasyonu
def optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret):
    problem = pulp.LpProblem("Vardiya_Planlama", pulp.LpMinimize)
    vardiyalar = pulp.LpVariable.dicts("Vardiya", [(c, g) for c in calisanlar for g in gunler], cat="Binary")
    problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar for g in gunler) * gunluk_ucret, "Toplam_Maliyet"
    
    for g in gunler:
        problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar) >= calisan_ihtiyaci[g], f"Gün_{g}_Kısıtı"
    
    for c in calisanlar:
        for g in izinli_gunler.get(c, []):
            problem += vardiyalar[(c, g)] == 0, f"Izin_{c}_{g}"
        problem += pulp.lpSum(vardiyalar[(c, g)] for g in gunler) <= max_calismalar[c], f"Max_{c}"
    
    problem.solve()
    
    result = {g: [c for c in calisanlar if vardiyalar[(c, g)].value() == 1] for g in gunler}
    toplam_maas = pulp.value(problem.objective)
    return result, toplam_maas

# Streamlit uygulaması
st.title("Vardiya Planlama ve Optimizasyon")

# Kullanıcı girişi
calisan_sayisi = st.number_input("Çalışan Sayısı", min_value=1, value=5, step=1)
calisanlar = generate_random_names(calisan_sayisi)

izin_gunleri = {}
for calisan in calisanlar:
    izin_gunleri[calisan] = st.multiselect(f"{calisan} için izin günleri:", 
                                           ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])

max_gunler = {}
for calisan in calisanlar:
    max_gunler[calisan] = st.slider(f"{calisan} için haftalık maksimum çalışma günü:", min_value=1, max_value=7, value=5)

gunluk_ucret = st.number_input("Çalışan Başına Günlük Ücret (TL):", min_value=100, step=50, value=1000)

# Talep tahmini
sample_data = pd.DataFrame({"ds": pd.date_range(start="2023-01-01", periods=365), "y": [random.randint(10, 100) for _ in range(365)]})
forecasted_data = forecast_demand(sample_data)
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)

# 7 günlük tahmin ve talep
st.subheader("7 Günlük Talep Tahmini")
st.write(pd.DataFrame(calisan_ihtiyaci.items(), columns=["Gün", "Gerekli Çalışan"]))

# Optimizasyon
gunler = list(calisan_ihtiyaci.keys())
result, toplam_maas = optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izin_gunleri, max_gunler, gunluk_ucret)

# Çıktılar
st.subheader("Vardiya Planı")
st.write(result)

st.subheader("Toplam Maaş Maliyeti")
st.write(f"Optimizasyon Sonrası Toplam Maaş: {toplam_maas} TL")
