"""Onaylanan temizlik işlemleri; ham veriyi korur, satır silmez.

Windows: .venv-windows/Scripts/python.exe clean_data.py
macOS: .venv/bin/python clean_data.py
"""

import hashlib
from pathlib import Path

import pandas as pd


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "used_cars.csv"
DESTINATION = BASE / "data" / "used_cars_cleaned.csv"
REPORT = BASE / "reports" / "cleaning" / "TEMIZLEME_RAPORU.md"
PLACEHOLDERS = {"", "–", "not supported"}


def clean_dataframe(raw):
    """Temizlenmiş kopyayı ve sütun bazında işlem kayıtlarını döndürür."""
    cleaned = raw.copy(deep=True)
    audit = []
    for col in raw.select_dtypes(include=["object", "string"]).columns:
        original = raw[col].astype("string")
        stripped = original.str.strip()
        whitespace_count = int((original != stripped).fillna(False).sum())
        marker_mask = stripped.str.lower().isin(PLACEHOLDERS)
        marker_counts = stripped[marker_mask].value_counts().to_dict()
        cleaned[col] = stripped.mask(marker_mask, pd.NA)
        audit.append((col, whitespace_count, marker_counts))

    specifications = {
        "price": (r"\$\d+(?:,\d{3})*(?:\.\d+)?", ["$", ","], "Float64"),
        "milage": (r"\d+(?:,\d{3})* mi\.", [",", " mi."], "Int64"),
    }
    for col, (pattern, removals, dtype) in specifications.items():
        values = cleaned[col]
        invalid = values.notna() & ~values.str.fullmatch(pattern, na=False)
        if invalid.any():
            # Sayıya çevrilemeyen dolu bir değeri sessizce eksik yapma.
            examples = [(int(i) + 2, str(v)) for i, v in values[invalid].head(10).items()]
            raise ValueError(
                f"{col}: {int(invalid.sum())} beklenmeyen biçim. "
                f"CSV satır numarası ve değer örnekleri: {examples!r}. "
                "Yeni çıktı yazılmadı; varsa eski çıktı bu çalıştırmaya ait değildir."
            )
        for item in removals:
            values = values.str.replace(item, "", regex=False)
        cleaned[col] = pd.to_numeric(values, errors="raise").astype(dtype)
    return cleaned, audit


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    raw = pd.read_csv(SOURCE)
    cleaned, audit = clean_dataframe(raw)
    if cleaned.shape != raw.shape or not cleaned.index.equals(raw.index):
        raise RuntimeError("Satır/sütun sayısı veya sırası değişti.")

    before_missing = raw.isna().sum()
    after_missing = cleaned.isna().sum()
    lines = [
        "# Veri Temizleme Raporu",
        "",
        "## Amaç ve kapsam",
        "Metin biçimlerini ve eksik bilgi gösterimlerini standartlaştırmak; fiyat ve mesafeyi sayısal analize hazırlamak.",
        "Kaynak: `used_cars.csv`; çıktı: `data/used_cars_cleaned.csv`.",
        f"Önce: {raw.shape[0]} satır × {raw.shape[1]} sütun. Sonra: {cleaned.shape[0]} satır × {cleaned.shape[1]} sütun.",
        "Satır sırası ve sütun adları korundu. Satır silme, eksik doldurma, kategori birleştirme, özellik mühendisliği ve model eğitimi yapılmadı.",
        "",
        "## Yöntem, gerekçe ve etkilenen kayıtlar",
        "### Metinler ve eksik bilgi işaretleri",
        "pandas StringDtype ve `str.strip()` ile yalnızca baştaki/sondaki boşluklar kaldırıldı.",
        "Boş metin, `–` ve `not supported` işaretleri (büyük/küçük harften bağımsız kontrolle) `pd.NA` yapıldı; diğer kategori yazımları korundu.",
        "Kaynak pandas varsayılan eksik-değer tanımasıyla okundu; aşağıdaki önce/sonra sayıları bu okumayı esas alır.",
    ]
    for col, spaces, markers in audit:
        lines.append(f"- `{col}`: boşluk düzeltmesi {spaces}; eksik yapılan özgün işaretler {markers!r}.")
    lines += [
        "", "### Sayısal tür dönüşümleri",
        "Önce düzenli ifadeyle biçim doğrulandı. Beklenmeyen dolu değer olursa işlem açık hata vererek çıktı yazmadan durur.",
        "- `price`: `$` ve binlik virgüller kaldırıldı; nullable `Float64` türüne dönüştürüldü. Para birimi kodu doğrulanmadı; TL veya kesin USD varsayımı yapılmadı.",
        f"  Başarıyla dönüştürülen dolu kayıt: {int(cleaned.price.notna().sum())}; çözülemeyen dolu kayıt: 0.",
        "- `milage`: ` mi.` eki ve binlik virgüller kaldırıldı; nullable `Int64` türüne dönüştürüldü. Birim mil olarak korundu, kilometreye çevrilmedi.",
        f"  Başarıyla dönüştürülen dolu kayıt: {int(cleaned.milage.notna().sum())}; çözülemeyen dolu kayıt: 0.",
        "", "## Sütun bazında önce/sonra",
        "```text",
        pd.DataFrame({"once_tur": raw.dtypes.astype(str), "sonra_tur": cleaned.dtypes.astype(str),
                      "once_eksik": before_missing, "sonra_eksik": after_missing,
                      "yeni_eksik": after_missing - before_missing}).to_string(),
        "```",
        "", "## Eksik bilgilerin anlamı",
        "`accident` eksikleri kazasız, `clean_title` eksikleri olumsuz tapu kaydı olarak kodlanmadı.",
        "Eksik değerler ileride eğitim verisinden öğrenilecek yöntemlere bırakıldı. Renk/motor gibi alanların `–` değerleri de eksik kaldı.",
        "", "## Tekrarlar ve uç gözlemler",
        f"Tamamen tekrarlı satır: önce {int(raw.duplicated().sum())}, sonra {int(cleaned.duplicated().sum())}. Hiçbir satır silinmedi.",
        "IQR = Q3 − Q1; adaylar [Q1 − 1,5 × IQR, Q3 + 1,5 × IQR] aralığının dışındadır. Bu bir silme kuralı olarak uygulanmadı.",
    ]
    for col in ["price", "milage"]:
        values = cleaned[col].dropna()
        q1, q3 = values.quantile([0.25, 0.75])
        low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        count = int(((values < low) | (values > high)).sum())
        lines.append(f"- `{col}`: {count} uç gözlem adayı korundu; alt sınır {low:.2f}, üst sınır {high:.2f}.")

    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Ham kaynak değişti; çıktı üretimi durduruldu.")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(DESTINATION, index=False, encoding="utf-8")
    # CSV tür saklamaz; yeniden okurken rapordaki türleri açıkça uygula.
    restored = pd.read_csv(DESTINATION, dtype=cleaned.dtypes.to_dict())
    pd.testing.assert_frame_equal(cleaned, restored)
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Ham CSV değişti.")
    lines += [
        "", "## Doğrulama ve kullanım",
        "Çıktı CSV yeniden okunarak sütun türleri, değerler, eksikler ve satır sırası temizlenmiş veriyle karşılaştırıldı; eşleşti.",
        "CSV veri türlerini saklamaz. pandas varsayılan okumada `string` yerine `object` gösterebilir; nullable türleri korumak için yukarıdaki sonra_tur değerlerini `dtype` argümanına verin.",
        "Ham CSV'nin işlem öncesi ve sonrası SHA-256 özeti aynı:", f"`{source_hash}`",
        "", "## Sonraki aşama",
        "Özellik mühendisliği kararları ayrı onayla belirlenecek; ardından regresyon ve kümeleme için ayrı hazırlık yapılacak.", "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Temizlenen veri: {DESTINATION}")
    print(f"Rapor: {REPORT}")
    print(f"Boyut: {cleaned.shape}; ham CSV değişmedi; yeniden okuma eşleşti.")
    print(pd.DataFrame({"once_eksik": before_missing, "sonra_eksik": after_missing}).to_string())


if __name__ == "__main__":
    main()
