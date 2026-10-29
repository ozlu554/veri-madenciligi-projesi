# Kümeleme Veri Hazırlama Raporu

## Amaç ve kapsam
Benzer teknik özelliklere sahip araçları keşif amaçlı gruplamaya uygun sayısal girdi hazırlamak.
Kaynak: `data/used_cars_features.csv`. Hiçbir kümeleme algoritması çalıştırılmadı; küme sayısı/etiketi veya kalite skoru üretilmedi.
Girdi: 4009 kayıt × 18 sütun. Hazırlanan matris: 4009 kayıt × 5 özellik.
Tüm kayıtlar aynı sırada korundu. Yalnızca onaylanan beş sütun seçildi; kaynak dosyalar değiştirilmedi.

## Özellik seçimi ve gerekçeler
- `model_year`: üretim yılı; araç yaşı üretilmedi, veri toplama tarihi bilinmiyor.
- `milage`: mesafe, mil biriminde; kilometreye çevrilmedi.
- `horsepower_hp`: metinden çıkarılan HP değeri.
- `engine_displacement_l`: litre olarak motor hacmi.
- `cylinder_count`: silindir sayısı.
Fiyat, marka, model, yakıt türü, renkler, şanzıman ve kaza/tapu bilgileri uzaklık matrisine dahil edilmedi; yorumlama için ayrı dosyada korundu. Eksiklik göstergeleri de matrisin girdisi değildir.

## Uygulanan yöntemler
1. `SimpleImputer(strategy='median')`: beş sütunun eksikleri ilgili sütunun tüm veri üzerindeki medyanıyla dolduruldu. Aykırı değerlere ortalamadan daha dayanıklı bir başlangıç yöntemidir.
2. `RobustScaler(quantile_range=(25, 75))`: doldurulmuş sütunlardan medyan çıkarıldı ve IQR'ye (Q3 − Q1) bölündü. Birimler arasındaki ölçek farkını azaltır; uç kayıtları silmez veya kırpmaz.
3. `Pipeline`: doldurma ve ölçekleme tek yeniden kullanılabilir ön işleyicide saklandı.
Bu keşif hazırlığında bütün veriye `fit_transform` uygulandı; eğitim/test ayrımı yapılmadı. Bu dosyalar yeni verilere genelleme başarısı kanıtı değildir. İleride ayrı değerlendirme yapılırsa dönüşümler sadece o değerlendirmenin eğitim bölümünde yeniden öğrenilmelidir.

## Doldurma ve ölçekleme sonuçları
```text
                sutun  doldurulan  doldurma_medyani  olcekleme_merkezi  doldurma_sonrasi_Q1  doldurma_sonrasi_Q3  olcekleme_boleni_IQR
           model_year           0            2017.0             2017.0               2012.0               2020.0                   8.0
               milage           0           52775.0            52775.0              23044.0              94100.0               71056.0
        horsepower_hp         808             310.0              310.0                268.0                381.0                 113.0
engine_displacement_l         217               3.5                3.5                  2.5                  4.6                   2.1
       cylinder_count         420               6.0                6.0                  6.0                  8.0                   2.0
```
Çeyrekler ve ölçekleme böleni doldurma SONRASI hesaplandı; ham dolu gözlemlerin çeyreklerinden farklı olabilir.
En az bir özelliği doldurulan kayıt: 952. Üç motor özelliği de eksik olan kayıt: 80.

## Ölçeklenmiş dağılımlar
```text
       model_year     milage  horsepower_hp  engine_displacement_l  cylinder_count
count   4009.0000  4009.0000      4009.0000              4009.0000       4009.0000
mean      -0.1856     0.1681         0.1569                 0.0831          0.0998
std        0.7631     0.7360         0.9700                 0.6568          0.8141
min       -5.3750    -0.7413        -2.1239                -1.3571         -1.5000
25%       -0.6250    -0.4184        -0.3717                -0.4762          0.0000
50%        0.0000     0.0000         0.0000                 0.0000          0.0000
75%        0.3750     0.5816         0.6283                 0.5238          1.0000
max        0.8750     4.9570         6.2832                 2.3333          5.0000
```

## Doğrulama
- 4.009 kayıt ve beş özellik korundu; fiyat ve kategoriler matriste yok.
- Matrisin tüm değerleri sonlu; eksik değer yok.
- Doldurma medyanları, ölçekleme merkezleri ve IQR bölenleri bağımsız hesaplarla karşılaştırıldı.
- Dolu gözlemler doldurma adımında aynı kaldı; ölçekleme yalnızca doğrusal dönüşüm uyguladı.
- NPY ve CSV yeniden okundu; ön işleyici yeniden yüklenerek aynı dönüşüm doğrulandı.
- Yorumlama verisi ve kaynak satır eşleşmesi doğrulandı; kaynak dosyaların SHA-256 özetleri değişmedi.

## Üretilen dosyalar
Dizin: `data/clustering/`.
- `X_clustering.npy`: model girdisi olacak sayısal matris; `numpy.load` ile okunur.
- `X_clustering.csv`: aynı matrisin sütun adlarını içeren okunabilir sürümü.
- `preprocessor.joblib`: doldurma ve ölçeklemeyi öğrenmiş Pipeline.
- `manifest.json`: özellik sırası, parametreler, istatistikler ve kaynak dosya/satır bilgileri.
- `interpretation_context.csv`: fiyat ve kategoriler dahil özgün özellikli veri ve `source_csv_row`. Uzaklık girdisi değildir.
- `imputation_mask.csv`: her seçili özellik için 1=dolduruldu, 0=özgün değer mevcuttu. Uzaklık girdisi değildir.
Kaynak satır numarası CSV başlığını hesaba katar: ilk veri satırı 2'dir. Bütün dosyalar aynı araç sırasındadır.

## Sınırlar ve yorumlama
Medyanla doldurulan motor özellikleri, teknik bilgisi eksik araçları yapay olarak birbirine yaklaştırabilir. Elektrikli araçlarda eksik hacim/silindir bilgisi için de medyan kullanıldı; bu doldurma teknik bir gerçek olarak yorumlanmamalı, yorumlama sırasında maske ve yakıt türü incelenmelidir.
Motor gücü, hacim ve silindir sayısı ilişkili olabilir; uzaklıkta motor özelliklerine daha fazla ağırlık verilmesine yol açabilir. Bu aşamada ağırlıklandırma veya boyut indirgeme yapılmadı.
RobustScaler uç değerleri ortadan kaldırmaz; uç araçlar bazı algoritmalarda etkili olmaya devam edebilir. Kümeleme algoritması ve parametreleri ayrıca değerlendirilmeli.
Kümeleme eğitimi bu aşamanın dışında kaldı. Sonuç kalitesi veya bulunan grup sayısı hakkında henüz iddia yoktur.
