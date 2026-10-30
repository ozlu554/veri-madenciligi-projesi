# Ortak geliştirme ortamı

Her bilgisayar kendi sanal ortamını kullanır. Sanal ortam klasörleri
bilgisayarlar arasında kopyalanmaz. Ortak doğrudan bağımlılıklar
`requirements.txt` içinde sabitlenmiştir; alt bağımlılıklar işletim sistemi
ve Python sürümüne göre farklı olabilir.

## Windows

Proje klasöründe çalışın. Yeni kurulumda Python 3.12 yüklüyse ortamı bir kez oluşturun:

```powershell
py -3.12 -m venv .venv-windows
```

Çalışan `.venv-windows` ortamınız zaten varsa yeniden oluşturmayın.
Ardından:

```powershell
.\.venv-windows\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-windows\Scripts\python.exe -m pip check
.\.venv-windows\Scripts\python.exe verify_project.py
```

VS Code içinde **Python: Select Interpreter** komutuyla seçilecek yorumlayıcı: `.venv-windows\Scripts\python.exe`.

## macOS

Mevcut yerel ortamı kullanarak, proje klasöründe:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -B verify_project.py
```

Yerel ortam henüz yoksa önce `python3 -m venv .venv` çalıştırılır.
Bu depoda `.venv` hâlâ takip edildiği için yeni klonda klasörün var olması,
Mac'inizde çalışacağı anlamına gelmez. Kopyalanmış ortam hata verirse mevcut
klasörü silmeden/yedeklemeden yeniden kurmayın; ortam geçişini ayrıca planlayın.
Mac doğrulaması Python 3.9.6 ile yapıldı.
VS Code içinde **Python: Select Interpreter** komutuyla seçilecek yorumlayıcı: `.venv/bin/python`.

## Geçiş durumu

Bu dosyaların eklenmesi hiçbir bilgisayardaki kurulu paketleri kendiliğinden
değiştirmez. Yukarıdaki kurulum komutu çalıştırılınca ortam ortak sürümlere geçer.
Windows ortamı bu listedeki sürümlere geçirilmiştir. Beş kütüphanenin içe
aktarılması, sürüm eşleşmeleri, `pip check` ve CSV'nin okunması doğrulanmıştır.
Mac ortamında da ortak sürümlerin kurulumu, paketlerin içe aktarılması,
`pip check`, `verify_project.py`, kayıtlı ön işleyicilerin dönüşümleri ve
grafik çizimi doğrulandı. Tüm analiz/hazırlık akışı Mac üzerinde geçici
bir kopyada da başarıyla çalıştırıldı; mevcut proje çıktıları korunmuştur.
Windows manifestlerindeki dosya ayırıcıları ve Git kaynaklı LF/CRLF
farkları doğrulama kodunda desteklenir; CSV içerikleri değiştirilmez.

`.venv-windows/` Git tarafından takip edilmez. Eski Mac `.venv/` klasörü ise
önceki commitlerden beri takip edilmektedir. `.gitignore` içindeki `.venv/`
kuralı mevcut takibi kaldırmaz.

Mac ortamını korumak için bu aşamada Git takibinden dosya çıkarılmadı.
İleride takip kaldırma değişikliği gönderilmeden önce Mac kullanıcısı ortamını
depo dışına yedeklemelidir: bu değişikliği çekmek, takipten çıkarılan ortam
dosyalarını yerel çalışma klasöründen silebilir. Ardından her bilgisayarda
yerel ortam oluşturulup `requirements.txt` ile kurulum yapılır.

Kod ve veri paylaşılır; sanal ortamlar paylaşılmaz. EDA, veri temizleme,
özellik mühendisliği ve modelleme öncesi veri hazırlığı tamamlanmıştır;
model eğitimi yapılmamıştır. İşlem sırası ve çıktı rehberi README.md'dedir.

## Doğrulama ve paylaşım

`verify_project.py` mevcut çıktıları okur; analizleri yeniden üretmez ve model
eğitmez. Kayıtlı ön işleyicilerin mevcut regresyon ve kümeleme matrislerini
ürettiğini, CSV/NPY eşleşmelerini ve kaynak satır sırasını da denetler.
Bu kontrol veri hazırlama kalitesinin veya model başarısının garantisi değildir.

Sanal ortamı etkinleştirmek zorunlu değildir; yukarıdaki doğrudan Python
komutları doğru ortamı kullanır. `main.py` yalnızca ilk örnek çıktıyı gösterir.
Windows'ta güncel doğrulayıcı ayrıca çalıştırılmalıdır; Mac testi Windows testi
olarak değerlendirilmez. Kurulum için internet bağlantısı gerekir.

SciPy ve joblib doğrudan kullanıldığı için ortak gereksinimlere eklendi.
Alt bağımlılıklar tamamen kilitlenmiş değildir. Mevcut Windows ortamı yeni
listeyle kontrol edilmeden bütün paket sürümlerinin eşleştiği varsayılmamalıdır.
