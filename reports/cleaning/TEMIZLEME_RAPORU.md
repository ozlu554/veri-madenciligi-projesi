# Veri Temizleme Raporu

## Amaç ve kapsam
Metin biçimlerini ve eksik bilgi gösterimlerini standartlaştırmak; fiyat ve mesafeyi sayısal analize hazırlamak.
Kaynak: `used_cars.csv`; çıktı: `data/used_cars_cleaned.csv`.
Önce: 4009 satır × 12 sütun. Sonra: 4009 satır × 12 sütun.
Satır sırası ve sütun adları korundu. Satır silme, eksik doldurma, kategori birleştirme, özellik mühendisliği ve model eğitimi yapılmadı.

## Yöntem, gerekçe ve etkilenen kayıtlar
### Metinler ve eksik bilgi işaretleri
pandas StringDtype ve `str.strip()` ile yalnızca baştaki/sondaki boşluklar kaldırıldı.
Boş metin, `–` ve `not supported` işaretleri (büyük/küçük harften bağımsız kontrolle) `pd.NA` yapıldı; diğer kategori yazımları korundu.
Kaynak pandas varsayılan eksik-değer tanımasıyla okundu; aşağıdaki önce/sonra sayıları bu okumayı esas alır.
- `brand`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {}.
- `model`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {}.
- `milage`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {}.
- `fuel_type`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {'–': 45, 'not supported': 2}.
- `engine`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {'–': 45}.
- `transmission`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {'–': 4}.
- `ext_col`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {'–': 15}.
- `int_col`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {'–': 133}.
- `accident`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {}.
- `clean_title`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {}.
- `price`: boşluk düzeltmesi 0; eksik yapılan özgün işaretler {}.

### Sayısal tür dönüşümleri
Önce düzenli ifadeyle biçim doğrulandı. Beklenmeyen dolu değer olursa işlem açık hata vererek çıktı yazmadan durur.
- `price`: `$` ve binlik virgüller kaldırıldı; nullable `Float64` türüne dönüştürüldü. Para birimi kodu doğrulanmadı; TL veya kesin USD varsayımı yapılmadı.
  Başarıyla dönüştürülen dolu kayıt: 4009; çözülemeyen dolu kayıt: 0.
- `milage`: ` mi.` eki ve binlik virgüller kaldırıldı; nullable `Int64` türüne dönüştürüldü. Birim mil olarak korundu, kilometreye çevrilmedi.
  Başarıyla dönüştürülen dolu kayıt: 4009; çözülemeyen dolu kayıt: 0.

## Sütun bazında önce/sonra
```text
             once_tur sonra_tur  once_eksik  sonra_eksik  yeni_eksik
brand          object    string           0            0           0
model          object    string           0            0           0
model_year      int64     int64           0            0           0
milage         object     Int64           0            0           0
fuel_type      object    string         170          217          47
engine         object    string           0           45          45
transmission   object    string           0            4           4
ext_col        object    string           0           15          15
int_col        object    string           0          133         133
accident       object    string         113          113           0
clean_title    object    string         596          596           0
price          object   Float64           0            0           0
```

## Eksik bilgilerin anlamı
`accident` eksikleri kazasız, `clean_title` eksikleri olumsuz tapu kaydı olarak kodlanmadı.
Eksik değerler ileride eğitim verisinden öğrenilecek yöntemlere bırakıldı. Renk/motor gibi alanların `–` değerleri de eksik kaldı.

## Tekrarlar ve uç gözlemler
Tamamen tekrarlı satır: önce 0, sonra 0. Hiçbir satır silinmedi.
IQR = Q3 − Q1; adaylar [Q1 − 1,5 × IQR, Q3 + 1,5 × IQR] aralığının dışındadır. Bu bir silme kuralı olarak uygulanmadı.
- `price`: 244 uç gözlem adayı korundu; alt sınır -31985.00, üst sınır 99175.00.
- `milage`: 69 uç gözlem adayı korundu; alt sınır -83540.00, üst sınır 200684.00.

## Doğrulama ve kullanım
Çıktı CSV yeniden okunarak sütun türleri, değerler, eksikler ve satır sırası temizlenmiş veriyle karşılaştırıldı; eşleşti.
CSV veri türlerini saklamaz. pandas varsayılan okumada `string` yerine `object` gösterebilir; nullable türleri korumak için yukarıdaki sonra_tur değerlerini `dtype` argümanına verin.
Ham CSV'nin işlem öncesi ve sonrası SHA-256 özeti aynı:
`faad2565d2da11cd0d3d2b38e9deb08f44c34c0c6b4e27004f8140d1de22e242`

## Sonraki aşama
Özellik mühendisliği kararları ayrı onayla belirlenecek; ardından regresyon ve kümeleme için ayrı hazırlık yapılacak.
