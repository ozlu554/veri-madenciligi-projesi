# İkinci El Araç Verisi: Modelleme Öncesi Hazırlık

Proje ekibi: Tuğçe ve İlayda.

## Amaç ve mevcut durum

Amaç; keşifsel veri analizi, temizleme ve özellik mühendisliği uygulayarak
veriyi regresyon ve kümeleme için ayrı biçimlerde hazırlamaktır. Tahmin veya
kümeleme modeli eğitilmedi; doğruluk, R², hata metriği ya da küme skoru üretilmedi.

Ham veri `used_cars.csv`: 4.009 kayıt, 12 sütun. Kaynak: Taeef Najib,
[Used Car Price Prediction Dataset (Kaggle)](https://www.kaggle.com/datasets/taeefnajib/used-car-price-prediction-dataset).
Kaggle resmi kaydında belirtilen lisans [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Atıf, dönüşümler ve doğrulama sınırları [VERI_KAYNAGI.md](VERI_KAYNAGI.md)
içindedir. Veri toplama tarihi ve örnekleme yöntemi doğrulanmadı. Mesafe mil
birimindedir; fiyatlarda `$` vardır, para birimi kodu doğrulanmamıştır.

## İşlem sırası ve sonuçlar

1. `eda.py`: eksiklik, tekrar, kategori sıklıkları, sayısal özetler, histogramlar,
   Spearman korelasyonu ve 1,5 × IQR uç gözlem adayları incelendi. Tamamen tekrarlı
   satır bulunmadı. İlk eksikler: yakıt türü 170, kaza bilgisi 113, temiz tapu 596.
2. `clean_data.py`: baş/son boşluklar temizlendi; boş metin, `–` ve
   `not supported` eksik bilgi olarak standartlaştırıldı. Fiyat ve mesafe
   sayısallaştırıldı. Kayıt silinmedi. `data/used_cars_cleaned.csv`: 4.009 × 12.
3. `feature_engineering.py`: açık metinlerden motor gücü, hacmi, silindir sayısı
   ve şanzıman grubu çıkarıldı. Kaza/tapu için eksiklik göstergeleri eklendi.
   Çıkarım yapılamayan veya çelişkili ifadeler eksik bırakıldı.
   `data/used_cars_features.csv`: 4.009 × 18.
4. `prepare_regression.py`: hedef `price`; %80 eğitim/%20 test, seed 42.
   Eğitim medyanı, kategorik Unknown, One-Hot Encoding ve StandardScaler
   Pipeline/ColumnTransformer içinde kullanıldı. Bütün öğrenilen dönüşümler
   yalnızca eğitimde öğrenildi. Eğitim 3.207 × 79; test 802 × 79.
5. `prepare_clustering.py`: yıl, mil, güç, hacim ve silindir sayısı seçildi.
   Tüm veri üzerinde medyanla doldurma ve RobustScaler uygulandı. Fiyat ve
   kategoriler uzaklık girdisine alınmadı. Matris 4.009 × 5.
6. `verify_project.py`: mevcut çıktıları değiştirmeden sözdizimi, kaynak özetleri,
   boyut, satır/etiket eşleşmeleri, eksiklik maskesi ve sonluluk kontrolü yapar.

`main.py` ilk örnek kod olarak korundu; analiz akışını çalıştırmaz.

## Çalıştırma

Ortam kurulumu için [KURULUM.md](KURULUM.md) dosyasını okuyun.
Proje klasöründen aşağıdaki sırayı kullanın. Komutlar ilgili türetilmiş çıktı
dosyalarını yeniden üretir; ham CSV'yi değiştirmez.

Windows PowerShell:

```powershell
.\.venv-windows\Scripts\python.exe eda.py
.\.venv-windows\Scripts\python.exe clean_data.py
.\.venv-windows\Scripts\python.exe feature_engineering.py
.\.venv-windows\Scripts\python.exe prepare_regression.py
.\.venv-windows\Scripts\python.exe prepare_clustering.py
.\.venv-windows\Scripts\python.exe verify_project.py
```

macOS:

```bash
.venv/bin/python eda.py
.venv/bin/python clean_data.py
.venv/bin/python feature_engineering.py
.venv/bin/python prepare_regression.py
.venv/bin/python prepare_clustering.py
.venv/bin/python verify_project.py
```

Windows ortamı daha önce doğrulandı. Mac üzerinde ortak paket sürümleri,
`pip check`, `verify_project.py`, kayıtlı ön işleyicilerin mevcut matrislerle
eşleşmesi ve grafik çizimi doğrulandı. Tüm analiz/hazırlık akışı Mac üzerinde geçici kopyada başarıyla çalıştırıldı;
mevcut proje çıktıları değiştirilmedi.
Doğrulayıcı Windows manifest yollarını ve Git kaynaklı LF/CRLF farklarını
destekler; farklı satır sonlarıyla eşleşme ayrıca bildirilir.
Ortak doğrudan bağımlılıklar sabittir; Python ve alt bağımlılık sürümleri
farklı olabileceğinden bilgisayarlar arasında birebir aynı ortam garantisi yoktur.

## Raporlar ve çıktılar

- [EDA](reports/eda/EDA_RAPORU.md) ve [grafikler](reports/eda/dagilimlar.png).
- [Temizleme](reports/cleaning/TEMIZLEME_RAPORU.md): hangi işlemin kaç kaydı etkilediği.
- [Özellik mühendisliği](reports/features/OZELLIK_RAPORU.md) ve
  [satır bazında çıkarım denetimi](reports/features/extraction_audit.csv).
- [Regresyon hazırlığı](reports/regression/REGRESYON_HAZIRLIK_RAPORU.md).
- [Kümeleme hazırlığı](reports/clustering/KUMELEME_HAZIRLIK_RAPORU.md).

Regresyonun matrisleri, hedefleri, ön işleyicisi ve manifesti `data/regression/`
altındadır. Kümeleme çıktıları, yorumlama verisi ve doldurma maskesi
`data/clustering/` altındadır. Manifestler sütun sırasını, kaynak satırlarını,
ayarları ve SHA-256 özetlerini belgeler.

## Sunumda açıklanacak temel kararlar

- Neden medyan? Uç değerlere ortalamadan daha dayanıklı bir başlangıç doldurması.
- Neden iki farklı ölçekleyici? Regresyonda standartlaştırılmış başlangıç girdisi;
  kümelemede uç gözlemlerin ölçek üzerindeki etkisini azaltmak için medyan/IQR.
- Neden uç değerleri silmedik? Yüksek fiyat veya mesafe tek başına hata değildir.
  EDA'da 244 fiyat ve 69 mesafe adayı bulundu; hepsi korundu.
- Neden Unknown? Eksik kaza bilgisi kazasız, eksik tapu bilgisi No demek değildir.
- Neden önce eğitim/test ayrımı? Doldurma ve kodlamada test verisinin eğitim
  istatistiklerine karışmasını önlemek için.
- Neden kümelemede fiyat yok? Teknik benzerlikleri keşfetmek; fiyatı daha sonra
  grupları yorumlamada kullanmak için.

## Sınırlar ve kalan işler

Motor özellikleri kurallarla metinden çıkarıldı; dış teknik kaynakla doğrulanmadı.
Araç yaşı, toplama tarihi bilinmediği için üretilmedi. Kümelemede medyanla
doldurma, özellikle teknik bilgisi eksik/elektrikli araçları yapay olarak
yaklaştırabilir. Motor özellikleri birbirleriyle ilişkili olabilir.

Regresyonda çapraz doğrulama yapılacaksa ön işleyici her katın eğitiminde modelle
aynı Pipeline içinde yeniden öğrenilmelidir. Hazır dönüştürülmüş eğitim
matrisleriyle ön işleme seçimi yapmak katlar arasında bilgi sızıntısına yol açar.
Test verisi model seçimi için kullanılmamalıdır.

Mac `.venv` klasörü eski commitlerden beri Git tarafından takip edilmektedir;
`.gitignore` bu mevcut takibi kaldırmaz. Yedekleme ve geçiş planı KURULUM.md'dedir.

Bu kapsamın sonunda model eğitimi yapılmaz. Bundan sonraki çalışmalar ayrı
karar/onay gerektirir; mevcut çıktıların hazır olması model başarısı kanıtı değildir.

## Yerel sunum arayüzü

`arayuz/index.html` dosyasını çift tıklayarak Chrome, Edge veya Safari'de açın.
Sunucu, internet veya yeni Python paketi gerekmez. Arayüz mevcut veri ve
raporların bir anlık kopyasını içerir; kaynak dosyalara yazmaz.

Genel bakış, veri gezgini (ham/temizlenmiş/özellikli veri), arama, marka filtresi,
sıralama, CSV indirme, dağılımlar ve yöntem raporları bulunur. Grafikler tüm
veriyi kullanır; tablodaki filtrelerden etkilenmez. İndirilen CSV ayrı bir
kopyadır; formül benzeri metinlere elektronik tablo güvenliği için ön ek eklenir.

Veri veya raporlar değiştiğinde görünümü yeniden üretin:

Windows: `.\.venv-windows\Scripts\python.exe arayuz_olustur.py`

Mac: `.venv/bin/python -B arayuz_olustur.py`

`sablon.html` geliştirme şablonudur; sunum için `index.html` açılmalıdır.
Arayüz model eğitmez ve tahmin üretmez. Gösterilen zaman görünümün oluşturulma
zamanıdır; veri toplama tarihi değildir.

### Geliştirilmiş sunum ekranı ve önceki sürüm

Yeni arayüzde aynı araç için ham/temizlenmiş veri karşılaştırması, araç detay
kartı, marka filtreli grafikler ve çubuk ayrıntıları bulunur. Sağ üstteki
“Sunum görünümü” ile beş anlatım ekranı arasında geçilir; sol/sağ oklar da
kullanılabilir. Sunumdan çıkış: “Sunumdan çık” veya Escape.

Önceki açık mavi ekranın HTML ve şablonu `arayuz/yedek-acik-mavi/` içinde
korunmuştur. `ozet.json` yedek dosyaların SHA-256 özetlerini içerir.
Geri dönüşte hem `index.html` hem `sablon.html` bu yedekten geri alınmalıdır;
yalnızca HTML geri alınırsa sonraki üretimde yeni tasarım tekrar oluşur.

### Ek görseller

- Genel bakışta iki marka seçilerek kayıt sayıları ve medyan fiyat/mesafe/yıl
  karşılaştırılır. Bu yalnızca mevcut veri setinin betimleyici özetidir.
- Önce/sonra ekranında seçilen aracın ham, temizlenmiş ve çıkarılmış özellikleri
  üç aşamalı bir anlatımla açılır. Oynat, duraklat, başa dön ve doğrudan aşama
  seçimi desteklenir; kaynak veri üzerinde işlem yapılmaz.
- Keşifsel analizde fiyat–mesafe dağılım grafiği marka filtresini kullanır.
  Noktalar yakıt türüne göre renklidir; fare veya dokunmayla bir araç seçilip
  detay kartı açılabilir. Klavye kullanıcıları aynı kayıtları Veri gezgininde
  inceleyebilir. Fiyat ekseni doğrusal veya logaritmik seçilebilir.

İlk açık mavi sürüm `arayuz/yedek-acik-mavi/`, bu eklemelerden önceki
geliştirilmiş sürüm `arayuz/yedek-gelistirilmis-mavi/` içinde korunur.
