# Ortak geliştirme ortamı

Her bilgisayar kendi sanal ortamını kullanır. Sanal ortam klasörleri
bilgisayarlar arasında kopyalanmaz. Ortak doğrudan bağımlılıklar
`requirements.txt` içinde sabitlenmiştir; alt bağımlılıklar işletim sistemi
ve Python sürümüne göre farklı olabilir.

## Windows

Proje klasöründe, mevcut ortamı kullanarak:

```powershell
.\.venv-windows\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-windows\Scripts\python.exe -m pip check
.\.venv-windows\Scripts\python.exe main.py
```

VS Code yorumlayıcısı: `.venv-windows\Scripts\python.exe`.

## macOS

Mevcut yerel ortamı kullanarak, proje klasöründe:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python main.py
```

Yeni bir klonda, ortam henüz yoksa önce `python3 -m venv .venv` çalıştırılır.
VS Code yorumlayıcısı: `.venv/bin/python`.

## Geçiş durumu

Bu dosyaların eklenmesi hiçbir bilgisayardaki kurulu paketleri kendiliğinden
değiştirmez. Yukarıdaki kurulum komutu çalıştırılınca ortam ortak sürümlere geçer.
Windows ortamı bu listedeki sürümlere geçirilmiştir. Beş kütüphanenin içe
aktarılması, sürüm eşleşmeleri, `pip check` ve CSV'nin okunması doğrulanmıştır.
Mac ortamında kurulum ve çalıştırma henüz doğrulanmamıştır.

`.venv-windows/` Git tarafından takip edilmez. Eski Mac `.venv/` klasörü ise
önceki commitlerden beri takip edilmektedir. `.gitignore` içindeki `.venv/`
kuralı mevcut takibi kaldırmaz.

Mac ortamını korumak için bu aşamada Git takibinden dosya çıkarılmadı.
İleride takip kaldırma değişikliği gönderilmeden önce Mac kullanıcısı ortamını
depo dışına yedeklemelidir: bu değişikliği çekmek, takipten çıkarılan ortam
dosyalarını yerel çalışma klasöründen silebilir. Ardından her bilgisayarda
yerel ortam oluşturulup `requirements.txt` ile kurulum yapılır.

Kod ve veri paylaşılır; sanal ortamlar paylaşılmaz. Bu aşamada EDA, veri
temizleme veya model eğitimi yapılmamıştır.
