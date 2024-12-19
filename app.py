import streamlit as st
import pandas as pd
import random
from prophet import Prophet
import pulp

# 1. Rastgele çalışan isimleri oluşturma fonksiyonu
def generate_employee_names(num):
    return [f"Calisan_{i+1}" for i in range(num)]

# 2. Prophet ile talep tahmini
def forecast_demand(data, future_days=7):
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=future_days)
    forecast = model.predict(future)
    return forecast[['ds', 'yhat']].tail(future_days)

# 3. Talebe göre çalışan ihtiyacı hesaplama
def calculate_staff_demand(forecasted_values, scaling_factor=0.1):
    demand = {row['ds'].strftime('%A'): max(1, int(row['yhat'] * scaling_factor)) for _, row in forecasted_values.iterrows()}
    return demand

# 4. Vardiya optimizasyonu
def optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret):
    # Optimizasyon yapılmadan önceki maliyet
    toplam_maas_oncesi = sum(
        calisan_ihtiyaci[g] * gunluk_ucret for g in gunler
    )

    # Problem tanımı
    problem = pulp.LpProblem("Vardiya_Planlama", pulp.LpMinimize)

    # Karar değişkenleri
    vardiyalar = pulp.LpVariable.dicts("Vardiya", [(c, g) for c in calisanlar for g in gunler], cat="Binary")

    # Amaç fonksiyonu
    problem += pulp.lpSum(vardiyalar[(c, g)] * gunluk_ucret for c in calisanlar for g in gunler)

    # Kısıtlar
    for g in gunler:
        problem += pulp.lpSum(vardiyalar[(c, g)] for c in calisanlar) >= calisan_ihtiyaci[g], f"Talep_{g}"

    for c in calisanlar:
        problem += pulp.lpSum(vardiyalar[(c, g)] for g in gunler) <= max_calismalar[c], f"Max_{c}"
        for g in izinli_gunler[c]:
            problem += vardiyalar[(c, g)] == 0, f"Izin_{c}_{g}"

    # Problemi çöz
    problem.solve()

    # Optimizasyon sonrası maliyet ve planlama
    toplam_maas_sonrasi = 0
    plan = {g: [] for g in gunler}
    for g in gunler:
        for c in calisanlar:
            if vardiyalar[(c, g)].value() == 1:
                plan[g].append(c)
                toplam_maas_sonrasi += gunluk_ucret

    return toplam_maas_oncesi, toplam_maas_sonrasi, toplam_maas_oncesi - toplam_maas_sonrasi, plan

# 5. Streamlit uygulaması
def main():
    st.title("Vardiya Optimizasyon Uygulaması")

    # Çalışan sayısı alma
    num_employees = st.number_input("Çalışan Sayısı", min_value=1, step=1, value=5)
    calisanlar = generate_employee_names(num_employees)

    # Çalışan izin günleri
    izinli_gunler = {}
    gunler = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for calisan in calisanlar:
        izinli_gunler[calisan] = st.multiselect(f"{calisan} için izin günleri:", gunler)

    # Maksimum çalışma günleri alma
    max_calismalar = {calisan: st.number_input(f"{calisan} için maksimum çalışma günü:", min_value=1, step=1, value=5) for calisan in calisanlar}

    # Günlük ücret alma
    gunluk_ucret = st.number_input("Günlük Ücret", min_value=1, step=1, value=1000)

    # 7 günlük talep tahmini
    st.header("7 Günlük Talep Tahmini")
    sample_data = pd.DataFrame({
        "ds": pd.date_range(start="2024-01-01", periods=365, freq="D"),
        "y": [random.randint(10, 100) for _ in range(365)]
    })
    forecasted_data = forecast_demand(sample_data)
    calisan_ihtiyaci = calculate_staff_demand(forecasted_data)
    st.table(forecasted_data.rename(columns={"ds": "Tarih", "yhat": "Tahmini Talep"}))

    # Vardiya optimizasyonu
    st.header("Vardiya Optimizasyonu")
    toplam_oncesi, toplam_sonrasi, kar, vardiya_plani = optimize_vardiya(calisanlar, gunler, calisan_ihtiyaci, izinli_gunler, max_calismalar, gunluk_ucret)

    # Sonuçları gösterme
    st.subheader("Optimizasyon Öncesi ve Sonrası Kazanç Karşılaştırması")
    st.write(pd.DataFrame({
        "Durum": ["Optimizasyon Öncesi", "Optimizasyon Sonrası", "Kazanılan Kar"],
        "Tutar (TL)": [toplam_oncesi, toplam_sonrasi, kar]
    }))

    st.subheader("Vardiya Planı")
    st.write(pd.DataFrame({
        "Gün": list(vardiya_plani.keys()),
        "Çalışanlar": [", ".join(vardiya_plani[g]) for g in gunler]
    }))

if __name__ == "__main__":
    main()
