# Özellik Mühendisliği Raporu

## Amaç ve kapsam
Motor ve şanzıman metinlerindeki açık bilgileri ayrı özelliklere dönüştürmek, kaza/tapu bilgisinin eksikliğini ayrıca göstermek.
Kaynak: `data/used_cars_cleaned.csv`; çıktı: `data/used_cars_features.csv`.
Önce: 4009 satır × 12 sütun; sonra: 4009 satır × 18 sütun.
Mevcut 12 sütunun değerleri, satır sırası ve eksikleri korundu; yalnızca 6 sütun eklendi.

## Yöntemler ve nedenleri
Model veya tahmin kullanılmadı. Deterministik düzenli ifadeler, yalnızca açık metin kanıtından bilgi çıkarır.
- `horsepower_hp`: sayısal değerin ardından HP etiketi aranır. Birim HP olarak korunur; kW veya başka güç birimi varsayılmaz.
- `engine_displacement_l`: L veya Liter/Liters etiketi aranır; birim litre. Örneğin 120 AH hacim kabul edilmez.
- `cylinder_count`: V6, I4 gibi açık düzen etiketleri ve 6 Cylinder / 4-cyl ifadeleri kullanılır. 24V gibi supap ifadeleri silindir sayısı değildir.
- Aynı motor metnindeki tekrar eden eşit sayılar tek kanıt sayılır; farklı aday sayılar çelişki olarak eksik bırakılır. Pozitif olmayan sayılar da raporlanarak eksik bırakılır.
- `transmission_group`: açık etiketler Automatic, Manual, CVT, Dual-clutch gruplarına ayrılır. CVT veya Dual-clutch ile birlikte Automatic yazılması, özel alt grubun seçilmesini engellemez.
- Açık otomatik etiketiyle birlikte 'Manual Modes' ifadesi manuel şanzıman sayılmaz. 'Auto-Shift' tek başına çift kavrama kanıtı değildir.
- 'Dual Shift Mode', 'Variable', yalnızca vites sayısı ve çözülemeyen ifadeler belirsiz bırakılır. Manuel/otomatik veya CVT/çift kavrama çelişkileri de eksik bırakılır.
- `accident_missing`, `clean_title_missing`: bilgi eksikse 1, mevcutsa 0. Bunlar kaza veya tapu durumunun kendisi değildir.
- Kaynak eksikse özellikle elektrikli araçlarda hacim/silindir sayısı sıfırla doldurulmaz. Metinde açık bilgi yoksa tahmin yapılmaz.

## Çıkarım sonuçları
`extracted`: çıkarılan; `missing_source`: kaynak eksik; `no_explicit_match`: açık ifade yok; `conflict`: çelişkili; `nonpositive_value`: pozitif olmayan değer; `missing_total`: sonuçta eksik kalan toplam.
```text
status                 extracted  missing_source  no_explicit_match  conflict  nonpositive_value  missing_total
feature                                                                                                        
cylinder_count              3589              45                375         0                  0            420
engine_displacement_l       3792              45                172         0                  0            217
horsepower_hp               3201              45                763         0                  0            808
transmission_group          3586               4                418         1                  0            423
```

## Yeni sayısal özelliklerin özetleri
```text
       horsepower_hp  engine_displacement_l  cylinder_count
count         3201.0                 3792.0          3589.0
mean         332.206                  3.684           6.223
std          122.258                  1.417           1.719
min             70.0                   0.65             3.0
25%            248.0                    2.5             4.0
50%            310.0                    3.5             6.0
75%            400.0                    4.7             8.0
max           1020.0                    8.4            16.0
```

## Şanzıman grupları
```text
transmission_group
Automatic      3109
<NA>            423
Manual          373
CVT             100
Dual-clutch       4
```

## Eksiklik göstergeleri
- `accident_missing`: 1 olan 113, 0 olan 3896 kayıt.
- `clean_title_missing`: 1 olan 596, 0 olan 3413 kayıt.

## Çelişkili/geçersiz adayların tamamı
```text
 csv_row_number            feature source_column  source_value value   status
           2102 transmission_group  transmission 6 Speed At/Mt  <NA> conflict
```

## Denetim ve sınırlar
`extraction_audit.csv` her motor/şanzıman çıkarımı için kaynak CSV satırını (başlık nedeniyle ilk veri satırı 2), kaynak metni, sonucu ve durumunu içerir.
Kurallar açık metin eşleşmesine dayanır; üretici bilgisiyle dış doğrulama yapılmadı. Çıkarılabilen özellikler hatasız teknik veri garantisi değildir.
Mevcut sütunlar pandas karşılaştırmasıyla, çıktı ise yeniden okunarak doğrulandı. Kaynak dosyaların SHA-256 özetleri değişmedi:
- `used_cars.csv`: `faad2565d2da11cd0d3d2b38e9deb08f44c34c0c6b4e27004f8140d1de22e242`
- `data\used_cars_cleaned.csv`: `7b69c8046d00327315b1c53490d5876a5695807deb7d58e071f23ff591fe71de`

## Sonraki aşama
Araç yaşı ve yıllık ortalama mesafe üretilmedi; toplama tarihi bilinmiyor. Eksik doldurma, kodlama, ölçekleme, hedef dönüşümü veya model eğitimi yapılmadı.
Yeni eksik göstergeler orijinal sütunlarla ilişkili olabilir; model öncesinde yararları eğitim verisinde değerlendirilmelidir.
Regresyon ve kümeleme veri hazırlığı ayrı kararlarla yapılacak. Regresyonda öğrenilen dönüşümler yalnızca eğitim bölümünde öğrenilecek.
