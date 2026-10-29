# Regresyon Veri Hazırlama Raporu

## Amaç ve kapsam
Hedef fiyatı tahmin edecek modeller için veri hazırlamak; bu aşamada tahmin modeli eğitilmedi veya değerlendirilmedi.
Kaynak: `data/used_cars_features.csv`. Kaynaklar değiştirilmedi; fiyat ve uç gözlemler korundu.
Eğitim: 3207 kayıt; test: 802 kayıt. %80/%20 rastgele bölme, `random_state=42`.
4.009 kaydın %20'si tam sayı olmadığı için test 802, eğitim 3.207 kayıttır.

## Girdiler ve hedef
Hedef: `price`; girdilere dahil değildir. Fiyatın `$` gösterimi korunur, para birimi kodu ayrıca doğrulanmamıştır.
Sayısal: `model_year`, `milage`, `horsepower_hp`, `engine_displacement_l`, `cylinder_count`, `accident_missing`, `clean_title_missing`.
Kategorik: `brand`, `fuel_type`, `transmission_group`, `accident`, `clean_title`.
`model`, `engine`, `transmission`, `ext_col`, `int_col` başlangıç hazırlığında dışarıda bırakıldı. Ham metinler çıkarılmış özelliklerle örtüşüyor; model ve renkler yüksek kategori sayısına sahip. Bu seçim henüz performansla doğrulanmış değildir.

## Yöntemler ve gerekçeler
1. `train_test_split`: öğrenilen tüm dönüşümlerden önce bölme yapıldı; satır sızıntısı önlendi.
2. Sayısal `SimpleImputer(strategy='median')`: uç değerlere ortalamadan daha dayanıklı doldurma; medyanlar yalnızca eğitimden öğrenildi.
3. `StandardScaler`: eğitimde doldurulmuş sayısal girdilerden ortalama/standart sapma öğrenildi. Eksiklik göstergeleri dahil sayısal sütunlara uygulandı. Ağaç tabanlı modeller için zorunlu değildir.
4. Kategorik `SimpleImputer(strategy='constant', fill_value='Unknown')`: bilinmeyen bilgiyi ayrı kategoriyle gösterir; kaza/tapu durumu varsaymaz.
5. `OneHotEncoder(handle_unknown='ignore')`: sıralama varsaymadan kodlama. Testte yeni kategori ilgili sütunun bütün gösterge değerlerinde sıfır olur; Unknown kategorisiyle aynı anlamda değildir.
6. `Pipeline` ve `ColumnTransformer`: sayısal/kategorik adımları tek, yeniden kullanılabilir ön işleyicide birleştirir. Eğitimde `fit_transform`, testte yalnızca `transform` kullanıldı.

## Öğrenilen sayısal istatistikler
```text
                sutun  egitim_medyani  olcekleme_ortalamasi  olcekleme_boleni
           model_year          2017.0            2015.55784           6.03159
               milage         53500.0           64942.19956       52425.34125
        horsepower_hp           311.0             329.39788         110.47443
engine_displacement_l             3.5               3.67479           1.37467
       cylinder_count             6.0               6.20112           1.61139
     accident_missing             0.0               0.02838           0.16604
  clean_title_missing             0.0               0.14655           0.35366
```

## Kodlama sonuçları
Eğitim matrisi: (3207, 79); test matrisi: (802, 79). Seyrek CSR biçimiyle `.npz` olarak kaydedildi.
```text
                    unseen_test_rows  train_categories
brand                              1                56
fuel_type                          0                 6
transmission_group                 0                 5
accident                           0                 3
clean_title                        0                 2
```

## Doğrulamalar
- Eğitim/test satırları ayrık, birleşimleri tüm kayıtları kapsıyor; X/y satır sıraları aynı.
- İki matriste de eksik/sonsuz değer yok ve sütun sayıları aynı.
- Doldurma medyanları ve ölçekleme ortalamaları yalnızca eğitim verisiyle karşılaştırılarak doğrulandı.
- Yeni marka içeren örnek dönüştürüldü; görülmemiş kategori hata vermedi.
- Kaydedilen matrisler/hedefler ve yeniden yüklenen ön işleyici doğrulandı.
- Ham, temizlenmiş ve özellikli kaynakların SHA-256 özetleri değişmedi.

## Dosyalar ve kullanım
Çıktı dizini: `data/regression/`.
- `X_train.npz`, `X_test.npz`: sıralı özellik matrisleri; `scipy.sparse.load_npz` ile okunur.
- `y_train.npy`, `y_test.npy`: aynı sıradaki fiyat hedefleri; `numpy.load` ile okunur.
- `preprocessor.joblib`: eğitimde öğrenilmiş ön işleyici.
- `manifest.json`: sütun sırası, kaynak satırları, sürüm, bölme ayarları ve dosya özetleri.
- `train_before_preprocessing.csv`, `test_before_preprocessing.csv`: öğrenilen dönüşümlerden önceki seçilmiş girdiler, hedef ve kaynak satır numarası. `price` ve `source_csv_row` model girdisi değildir.

## Sınırlar ve sonraki aşama
Bu rastgele bölme aynı araç/satıcı kimliğine göre gruplanmış veya zamana göre ayrılmış değildir; dosyada bunu doğrulayacak kimlik/toplama tarihi yoktur.
Eksiklik ve kategori seçimleri henüz model performansıyla sınanmadı. Fiyat dönüşümü ve uç değer silme uygulanmadı.
İleride çapraz doğrulama yapılırsa hazır dönüştürülmüş eğitim matrisiyle ön işleme seçimi yapılmamalı: `make_preprocessor()` ile yeni ön işleyici modelle aynı Pipeline içinde her katın eğitim bölümünde yeniden öğrenilmelidir. Bunun için dönüşüm öncesi bölmeler saklandı. Test bölümü model seçimi için kullanılmamalıdır.
Kümeleme için veri hazırlığı ayrı onayla yapılacak. Bu aşama regresyon modeli eğitimi değildir.
