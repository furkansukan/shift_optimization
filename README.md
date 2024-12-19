# Shift Optimizer: Vardiya Planlama ve Optimizasyon 🌟

Bu proje, **vardiya planlaması ve optimizasyonu** üzerine bir uygulama geliştirmeyi amaçlamaktadır. Yöneylem araştırması ve optimizasyon tekniklerini kullanarak, işletmelerin çalışan taleplerini tahmin etmesine ve vardiya planlarını daha verimli hale getirmesine yardımcı olur.

## 📊 Proje Hedefi 🎯
Bu uygulama, kullanıcıların geçmiş verilere dayalı olarak çalışan talebini tahmin etmelerini, vardiya planlamalarını optimize etmelerini ve böylece iş gücü yönetimini daha verimli bir şekilde yapmalarını sağlar. **Prophet** zaman serisi tahmin modeli kullanılarak çalışan ihtiyacı tahmin edilir, **Pulp** kütüphanesi ise vardiya optimizasyonu yapar. Ayrıca, uygulama kullanıcıların günlük ücretlerini, izin günlerini ve çalışma saatlerini dikkate alarak maliyetleri optimize eder.

## 🚀 Kullanıcıya Sunulan Özellikler:
- **Zaman Serisi Tahmin:** Prophet modeli ile gelecekteki çalışan talepleri tahmin edilir.
- **Çalışan İhtiyacı Hesaplama:** Tahmin edilen verilere göre çalışan ihtiyacı hesaplanır.
- **Vardiya Optimizasyonu:** Çalışan izin günleri ve maksimum çalışma günleri göz önünde bulundurularak, en verimli vardiya planı oluşturulur.
- **Maliyet Hesaplama:** Optimizasyon öncesi ve sonrası maliyet farkları gösterilir.

## 🔧 Gereksinimler:
- Python 3.x
- Pandas
- Prophet
- Pulp
- Streamlit

## 📧 İletişim
- 📧 **E-posta:** [furkansukan10@gmail.com](mailto:furkansukan10@gmail.com)
- 🪪 **LinkedIn:** [furkansukan](https://www.linkedin.com/in/furkansukan)
- 🔗 **Kaggle:** [furkansukan](https://www.kaggle.com/furkansukan)
- 💻 **Uygulama Sitesi:** [Shift Optimization](https://shiftoptimization-furkansukan.streamlit.app/)

## 💡 Proje Amacı:
Bu proje, özellikle iş gücü yönetimi ve vardiya planlaması yapan şirketler için önemli bir araçtır. Zaman serisi tahminleri ve optimizasyon teknikleriyle, fazla mesaiyi, eksik çalışanları ve verimsiz vardiya planlarını minimize ederek **iş gücü maliyetlerini düşürmeye** yardımcı olur. Bu, işletmelerin daha verimli çalışmasına ve kaynaklarını daha etkin kullanmasına olanak tanır.

## 💻 Kullanım:
Proje, **Streamlit** uygulaması aracılığıyla kullanıcı dostu bir arayüz sağlar. Çalışan sayısı, izin günleri ve maksimum çalışma günleri gibi parametreleri girerek, tahminlere dayalı vardiya planlaması yapılabilir ve optimizasyon sonuçları görüntülenebilir.

Başlamak için projeyi kendi bilgisayarınıza indirip gerekli bağımlılıkları yükleyebilirsiniz:

```bash
pip install -r requirements.txt
```

### Proje Adımları:
1. **Örnek Veri Üretimi:** Başlangıç verisi oluşturulur.
2. **Tahmin Modeli:** Prophet kullanılarak zaman serisi tahminleri yapılır.
3. **Çalışan İhtiyacı Hesaplama:** Tahminlere göre çalışan ihtiyacı belirlenir.
4. **Vardiya Planlama ve Optimizasyon:** Pulp kullanılarak vardiya optimizasyonu yapılır.
5. **Sonuçların Gösterilmesi:** Optimizasyon öncesi ve sonrası maliyet farkı gösterilir.

### Teknolojiler:
- **Prophet:** Zaman serisi tahminleri için kullanılır.
- **Pulp:** Yöneylem araştırması için optimizasyon çözümleyicisi.
- **Streamlit:** Uygulama arayüzü için kullanılır.

Bu proje, özellikle küçük ve orta ölçekli işletmelerin vardiya yönetiminde karşılaştıkları zorlukları çözmeyi amaçlar.
