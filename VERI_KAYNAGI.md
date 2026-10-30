# Veri kaynağı ve atıf

- Veri seti: **Used Car Price Prediction Dataset**
- Yayımlayan: **Taeef Najib**
- Platform: Kaggle
- Kaynak: https://www.kaggle.com/datasets/taeefnajib/used-car-price-prediction-dataset
- Kaggle resmi üst veri kaydı: https://www.kaggle.com/api/v1/datasets/view/taeefnajib/used-car-price-prediction-dataset
- Kaggle kaydında belirtilen veri lisansı: **Attribution 4.0 International (CC BY 4.0)**
- Lisans açıklaması: https://creativecommons.org/licenses/by/4.0/
- Lisans metni: https://creativecommons.org/licenses/by/4.0/legalcode
- Kaynak/lisans kontrol tarihi: **30 Ekim 2026**

Kaynak bağlantısı proje ekibi tarafından sağlandı. Kaggle resmi üst veri
kaydındaki `licenseName` alanı ve yayımlayan bilgisi kontrol edildi.
Yerel dosyanın Kaggle'daki güncel indirmenin birebir kopyası olduğu ayrıca
indirilip karşılaştırılmadı. Yerel ham CSV 4.009 satır ve 12 sütun içerir;
kaynağın açıklamasındaki kayıt sayısıyla uyumludur.

Yayımlayanın açıklamasına göre veriler Cars.com araç ilanlarından elde
edilmiştir. Cars.com verisi proje ekibi tarafından yeniden toplanmadı.
Kaggle üst verisinde son güncelleme 15 Eylül 2023 görünür; bu tarih veri
TOPLAMA tarihi olarak kullanılmaz. Gerçek toplama tarihi ve örnekleme
prosedürü doğrulanmadı. Mesafe mil olarak korunmuştur; fiyatlar $ işaretlidir,
kesin para birimi kodu bu kaynak kontrolünde doğrulanmamıştır.

## Projede yapılan değişiklikler

Ham veri dosyasına analiz işlemleri uygulanmadı. Git nedeniyle LF/CRLF satır
sonları farklı olabilir. Türetilmiş çıktılarda metin/eksik gösterimleri
standartlaştırıldı; fiyat ve mesafe sayısallaştırıldı; altı özellik eklendi;
regresyon için eğitim/test ayrımı, eksik doldurma, kategorik kodlama ve
ölçekleme; kümeleme için özellik seçimi, eksik doldurma ve ölçekleme yapıldı.
Aşamalar `reports/` altında ayrıntılıdır. Raporlar, grafikler ve çevrimdışı
arayüz bu veri setine dayanır. Hiçbir tahmin veya kümeleme modeli eğitilmedi.

## Paylaşımda korunacak atıf

Taeef Najib, “Used Car Price Prediction Dataset”, Kaggle.
https://www.kaggle.com/datasets/taeefnajib/used-car-price-prediction-dataset
Veri lisansı: CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
Tuğçe ve İlayda'nın ders projesinde veri temizleme, özellik çıkarımı ve
modelleme öncesi hazırlık dönüşümleri uygulanmıştır. Yayımlayanın projeyi
onayladığı veya desteklediği ileri sürülmez.

CC BY 4.0 açıklaması; uygun atıf, lisans bağlantısı ve değişikliklerin
belirtilmesi koşullarıyla paylaşma ve uyarlamaya izin verir. Bu belge veri
lisansını kaydeder; proje koduna ayrıca bir yazılım lisansı atamaz.
