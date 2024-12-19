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

    # Optimizasyon sonrası toplam maaşı hesapla
    optimizasyon_maas = 0
    for g in gunler:
        for c in calisanlar:
            if vardiyalar[(c, g)].value() == 1:
                optimizasyon_maas += gunluk_ucret

    # Optimizasyon öncesi ve sonrası kar farkı
    optimizasyon_oncesi_maas = optimize_oncesi()
    kar = optimizasyon_oncesi_maas - optimizasyon_maas

    return optimizasyon_oncesi_maas, optimizasyon_maas, kar


# Streamlit Uygulaması
st.title("Vardiya Planlama ve Optimizasyon")
# Prophet ile tahmin verisi
sample_data = generate_sample_data()
forecasted_data = forecast_demand(sample_data)

# 7 günlük talep tahminini gösterme
st.write("Tahmin Edilen 7 Günlük Talep:")
st.write(forecasted_data)

# Kullanıcıdan girdi alınması
calisan_sayisi = st.number_input("Çalışan Sayısı", min_value=1, max_value=20, value=8)
calisanlar = [f"Çalışan {i+1}" for i in range(calisan_sayisi)]

# Çalışan izin günlerini alma
izinli_gunler = {}
for calisan in calisanlar:
    izin_gunleri = st.multiselect(f"{calisan} için izin günleri", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    izinli_gunler[calisan] = izin_gunleri

# Maksimum çalışma gününü alma
max_calismalar = {}
for calisan in calisanlar:
    max_gun = st.number_input(f"{calisan} için maksimum çalışma günü", min_value=1, max_value=7, value=5)
    max_calismalar[calisan] = max_gun

# Günlük ücret
gunluk_ucret = st.number_input("Günlük Ücret", min_value=100, value=1000)



# 7 günlük talep tahminini gösterme
#st.write("Tahmin Edilen 7 Günlük Talep:")
#st.write(forecasted_data)

# Tahminlere göre çalışan ihtiyacı hesaplama
calisan_ihtiyaci = calculate_staff_demand(forecasted_data)

# Optimize vardiya planlaması
opt_oncesi, opt_sonrasi, kar = optimize_vardiya(calisanlar, ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"],
                                                calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret)

# Optimizasyon öncesi ve sonrası sonuçları gösterme
st.write(f"Optimizasyon Öncesi Maliyet: {opt_oncesi} TL")
st.write(f"Optimizasyon Sonrası Maliyet: {opt_sonrasi} TL")
st.write(f"Optimizasyon Sonrası Kar: {kar} TL")
