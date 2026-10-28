"""Salt okunur EDA: ham CSV'yi değiştirmeden rapor ve grafik üretir.

Çalıştırma: .venv-windows/Scripts/python.exe eda.py
Mac: .venv/bin/python eda.py
"""

import hashlib
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "reports" / "eda"
# Matplotlib önbelleğini de proje içinde tut.
os.environ.setdefault("MPLCONFIGDIR", str(BASE / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def numeric_view(series, pattern, removals):
    """Sadece biçimi doğrulanan değerlerden ayrı bir sayısal analiz serisi."""
    text = series.astype("string")
    valid = text.str.fullmatch(pattern, na=False)
    view = text.where(valid)
    for old in removals:
        view = view.str.replace(old, "", regex=False)
    return pd.to_numeric(view, errors="coerce"), int((series.notna() & ~valid).sum())


def main():
    source = BASE / "used_cars.csv"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    df = pd.read_csv(source)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    price, price_invalid = numeric_view(
        df["price"], r"\$\d+(?:,\d{3})*(?:\.\d+)?", ["$", ","]
    )
    mileage, mileage_invalid = numeric_view(
        df["milage"], r"\d+(?:,\d{3})* mi\.", [",", " mi."]
    )
    numeric = pd.DataFrame({
        "model_year": df["model_year"],
        "milage_mi_analysis": mileage,
        "price_dollar_analysis": price,
    })
    lines = [
        "# İkinci El Araçlar — EDA Raporu",
        "",
        "## Amaç ve kapsam",
        "Verinin yapısını, eksiklerini, dağılımlarını ve olası sorunlarını modelleme öncesinde tanımak.",
        "Kaynak: `used_cars.csv`. Tüm kayıtlar incelendi; örnekleme yapılmadı.",
        "Veri toplama tarihi ve örnekleme yöntemi bilinmiyor; sonuçlar bu dosyayla sınırlıdır.",
        "CSV değiştirilmedi; kayıt silinmedi, eksik değer doldurulmadı, özellik üretilmedi ve model eğitilmedi.",
        "",
        "## Kullanılan yöntemler ve nedenleri",
        "- pandas `shape`, `dtypes`, `head`, `nunique`: boyutu, türleri, örnekleri ve kategori çeşitliliğini görmek.",
        "- `isna` ve `duplicated`: pandas tarafından tanınan eksikleri ve tüm sütunları aynı olan tekrarları bulmak.",
        "- `value_counts(dropna=False)`: kategorileri ve eksikleri birlikte saymak.",
        "- Düzenli ifade ile biçim kontrolü ve ayrı sayısal seriler: fiyat ve mil bilgisi metin olduğu için yalnızca EDA hesapları yapmak. Orijinal sütunlara atama yapılmadı.",
        "- `describe`: ortalama, standart sapma, medyan, çeyrekler ve uç değerleri görmek.",
        "- Histogramlar ve sıklık grafiği: dağılımları ve baskın markaları görmek.",
        "- 1,5 × IQR kuralı: incelenecek uç gözlemleri işaretlemek; bunlar otomatik olarak hata sayılmaz veya silinmez.",
        "- Spearman korelasyonu: sıralamalara dayalı ikili ilişkiyi incelemek. Nedensellik göstermez.",
        "",
        "## Genel yapı",
        f"Satır: {len(df):,}; sütun: {len(df.columns)}; tamamen tekrarlı satır: {int(df.duplicated().sum())}.",
        "",
        "```text",
        pd.DataFrame({"veri_turu": df.dtypes.astype(str), "eksik": df.isna().sum(),
                      "eksik_yuzde": (df.isna().mean() * 100).round(2),
                      "benzersiz_dolu": df.nunique()}).to_string(),
        "```",
        "",
        "## İlk beş kayıt",
        "```text", df.head().to_string(index=False), "```",
        "",
        "## Metinlerde ek kalite kontrolleri",
        "Eksik olarak sayılmayan boşluk ve yer tutucular ayrıca listelenir; henüz dönüştürülmez.",
    ]
    markers = {"–", "—", "-", "not supported", "unknown", "n/a", "na", "null", "none", ""}
    for col in df.select_dtypes(include=["object", "string"]).columns:
        text = df[col].astype("string").str.strip()
        counts = text[text.str.lower().isin(markers)].value_counts()
        if not counts.empty:
            lines.append(f"- `{col}` yer tutucu adayları: {counts.to_dict()!r}")
    lines += [
        "",
        "## Sayısal özetler (geçici analiz serileri)",
        f"Dolu olup beklenen biçime uymayan fiyat: {price_invalid}; mil bilgisi: {mileage_invalid}.",
        "Mesafe birimi mildir; kilometreye çevrilmedi. Fiyat işareti `$`; dosyada ülke/para birimi kodu doğrulanmadığından TL olarak yorumlanmadı.",
        "```text", numeric.describe().round(2).to_string(), "```",
        "",
        "## IQR ile uç gözlem adayları",
    ]
    for col in ["price_dollar_analysis", "milage_mi_analysis"]:
        s = numeric[col].dropna()
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((s < low) | (s > high)).sum())
        lines.append(f"- `{col}`: alt sınır {low:.2f}, üst sınır {high:.2f}; {count} aday (%{count / len(s) * 100:.2f}). Hiçbiri silinmedi.")
    lines += ["", "## Kategorik dağılımlar", "Her sütun için en sık 10 dolu/eksik değer:"]
    for col in df.columns:
        if col != "model_year":
            lines += [f"### {col}", "```text", df[col].value_counts(dropna=False).head(10).to_string(), "```"]
    lines += [
        "", "## Spearman korelasyonu",
        "Her ikili hesapta dolu gözlemler kullanılır; kategori sütunları bu hesaba dahil değildir.",
        "```text", numeric.corr(method="spearman").round(3).to_string(), "```",
        "", "## Bulguların yorumu ve sonraki aşama önerileri",
        "- `fuel_type`, `accident`, `clean_title` eksiklerinin anlamı araştırılmalı; eksik kaza kaydı kazasız, eksik tapu kaydı olumsuz olarak kabul edilmemeli.",
        "- `clean_title` dolu kayıtlarında yalnızca `Yes` bulunuyor. Bu sütunun bilgi içeriği ve eksiklik mekanizması değerlendirilmeden ikili kodlama yapılmamalı.",
        "- Fiyat ve mil bilgisi model öncesinde sayısal sütunlara dönüştürülmeli; biçim ve birim doğrulanmalı.",
        "- Model, motor, şanzıman ve renk sütunlarında çok sayıda kategori var; birleştirme ve kodlama kararları sonraki aşamada verilmeli.",
        "- Yüksek fiyat veya mesafe tek başına hatalı kayıt anlamına gelmez; IQR adayları araç özellikleriyle birlikte incelenmeli.",
        "- Model yılı, veri toplama tarihi bilinmeden bugünkü yıla göre araç yaşına çevrilmemeli.",
        "- Regresyonda fiyat hedef olacaktır. Kümelemede fiyatın dahil edilip edilmeyeceği amaca göre ayrıca kararlaştırılmalı.",
        "- İleride öğrenilen doldurma, kodlama ve ölçekleme işlemleri regresyonda yalnızca eğitim bölümünde öğrenilmeli; veri sızıntısı önlenmeli.",
        "", "## Grafikler", "![Dağılımlar](dagilimlar.png)",
        "Fiyat grafiğinde yalnızca görünüm için log10 ekseni kullanıldı; veri setine dönüşüm uygulanmadı.",
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    df["model_year"].value_counts().sort_index().plot.bar(ax=axes[0, 0], color="steelblue")
    axes[0, 0].set(title="Model yılı dağılımı", xlabel="Model yılı", ylabel="Araç sayısı")
    axes[0, 1].hist(mileage.dropna().to_numpy(dtype=float), bins=35, color="steelblue")
    axes[0, 1].set(title="Mesafe dağılımı", xlabel="Mesafe (mil)", ylabel="Araç sayısı")
    positive = price[price > 0].dropna().to_numpy(dtype=float)
    axes[1, 0].hist(np.log10(positive), bins=35, color="steelblue")
    axes[1, 0].set(title="Pozitif fiyatların log10 dağılımı", xlabel="log10(fiyat / 1 $)", ylabel="Araç sayısı")
    df["brand"].value_counts().head(10).sort_values().plot.barh(ax=axes[1, 1], color="steelblue")
    axes[1, 1].set(title="En sık görülen 10 marka", xlabel="Araç sayısı", ylabel="Marka")
    fig.suptitle("İkinci el araçlar — kaynak: used_cars.csv, tüm kayıtlar\nToplama tarihi bilinmiyor")
    fig.tight_layout()
    fig.savefig(OUTPUT / "dagilimlar.png", dpi=150)
    plt.close(fig)
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError("Kaynak CSV özeti değişti; inceleme gerekli.")
    lines += ["", "## Kaynak bütünlüğü", "Analiz öncesi ve sonrası SHA-256 aynı:", f"`{after}`", ""]
    report = OUTPUT / "EDA_RAPORU.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rapor: {report}")
    print(f"Grafikler: {OUTPUT / 'dagilimlar.png'}")
    print("CSV SHA-256 değişmedi. Temizleme ve model eğitimi yapılmadı.")


if __name__ == "__main__":
    main()
