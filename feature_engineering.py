"""Açık metin ifadelerinden özellik çıkarır; mevcut sütunları korur.

Windows: .venv-windows/Scripts/python.exe feature_engineering.py
macOS: .venv/bin/python feature_engineering.py
"""

import hashlib
from pathlib import Path
import re

import pandas as pd


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "data" / "used_cars_cleaned.csv"
OUTPUT = BASE / "data" / "used_cars_features.csv"
REPORT_DIR = BASE / "reports" / "features"
PATTERNS = {
    "horsepower_hp": r"\b(\d+(?:\.\d+)?)\s*HP\b",
    "engine_displacement_l": r"\b(\d+(?:\.\d+)?)\s*(?:L|Liters?)\b",
    "cylinder_count": r"\b(?:V|I|H|W)\s*(\d{1,2})\b|\b(\d{1,2})\s*[- ]?cyl(?:inder)?s?\b",
}


def extract_number(value, pattern):
    if pd.isna(value):
        return pd.NA, "missing_source"
    found = re.findall(pattern, str(value), flags=re.IGNORECASE)
    numbers = set()
    for match in found:
        parts = match if isinstance(match, tuple) else (match,)
        numbers.update(float(part) for part in parts if part)
    if not numbers:
        return pd.NA, "no_explicit_match"
    if len(numbers) > 1:
        return pd.NA, "conflict"
    number = numbers.pop()
    if number <= 0:
        return pd.NA, "nonpositive_value"
    return number, "extracted"


def transmission_group(value):
    if pd.isna(value):
        return pd.NA, "missing_source"
    text = str(value).lower()
    # Manuel mod içeren açık otomatik etiket, manuel şanzıman sayılmaz.
    text_without_modes = re.sub(r"(?:sport\s*&\s*)?manual\s+modes?", "", text)
    automatic = bool(re.search(r"\bautomatic\b|\bauto\b|\ba\s*/\s*t\b|\bat\b", text))
    manual = bool(re.search(r"\bmanual\b|\bm\s*/\s*t\b|\bmt\b", text_without_modes))
    cvt = bool(re.search(r"\bcvt\b", text))
    dct = bool(re.search(r"\bdct\b|\bdual[ -]clutch\b", text))
    if (manual and (automatic or cvt or dct)) or (cvt and dct):
        return pd.NA, "conflict"
    if cvt:
        return "CVT", "extracted"
    if dct:
        return "Dual-clutch", "extracted"
    if manual:
        return "Manual", "extracted"
    if automatic:
        return "Automatic", "extracted"
    # 'Dual Shift Mode', 'Variable', vites sayısı vb. için mekanizma tahmini yok.
    return pd.NA, "no_explicit_match"


def build_features(source):
    result = source.copy(deep=True)
    audit = []
    for feature, pattern in PATTERNS.items():
        pairs = [extract_number(value, pattern) for value in source["engine"]]
        dtype = "Int64" if feature == "cylinder_count" else "Float64"
        result[feature] = pd.array([value for value, _ in pairs], dtype=dtype)
        for i, (value, status) in enumerate(pairs):
            audit.append({"csv_row_number": i + 2, "feature": feature,
                          "source_column": "engine", "source_value": source["engine"].iloc[i],
                          "value": value, "status": status})
    pairs = [transmission_group(value) for value in source["transmission"]]
    result["transmission_group"] = pd.array([value for value, _ in pairs], dtype="string")
    for i, (value, status) in enumerate(pairs):
        audit.append({"csv_row_number": i + 2, "feature": "transmission_group",
                      "source_column": "transmission", "source_value": source["transmission"].iloc[i],
                      "value": value, "status": status})
    for col in ["accident", "clean_title"]:
        result[col + "_missing"] = source[col].isna().astype("Int64")
    return result, pd.DataFrame(audit)


def main():
    guarded = [BASE / "used_cars.csv", SOURCE]
    hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in guarded}
    source = pd.read_csv(SOURCE, dtype={"price": "Float64", "milage": "Int64"})
    result, audit = build_features(source)
    pd.testing.assert_frame_equal(source, result[source.columns])
    if len(result) != len(source) or len(result.columns) != len(source.columns) + 6:
        raise RuntimeError("Beklenmeyen çıktı boyutu.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False, encoding="utf-8")
    restored = pd.read_csv(OUTPUT, dtype=result.dtypes.to_dict())
    pd.testing.assert_frame_equal(result, restored)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    audit.to_csv(REPORT_DIR / "extraction_audit.csv", index=False, encoding="utf-8")
    summary = pd.crosstab(audit["feature"], audit["status"]).reindex(
        columns=["extracted", "missing_source", "no_explicit_match", "conflict", "nonpositive_value"], fill_value=0)
    summary["missing_total"] = len(source) - summary["extracted"]
    lines = [
        "# Özellik Mühendisliği Raporu", "",
        "## Amaç ve kapsam",
        "Motor ve şanzıman metinlerindeki açık bilgileri ayrı özelliklere dönüştürmek, kaza/tapu bilgisinin eksikliğini ayrıca göstermek.",
        "Kaynak: `data/used_cars_cleaned.csv`; çıktı: `data/used_cars_features.csv`.",
        f"Önce: {source.shape[0]} satır × {source.shape[1]} sütun; sonra: {result.shape[0]} satır × {result.shape[1]} sütun.",
        "Mevcut 12 sütunun değerleri, satır sırası ve eksikleri korundu; yalnızca 6 sütun eklendi.",
        "", "## Yöntemler ve nedenleri",
        "Model veya tahmin kullanılmadı. Deterministik düzenli ifadeler, yalnızca açık metin kanıtından bilgi çıkarır.",
        "- `horsepower_hp`: sayısal değerin ardından HP etiketi aranır. Birim HP olarak korunur; kW veya başka güç birimi varsayılmaz.",
        "- `engine_displacement_l`: L veya Liter/Liters etiketi aranır; birim litre. Örneğin 120 AH hacim kabul edilmez.",
        "- `cylinder_count`: V6, I4 gibi açık düzen etiketleri ve 6 Cylinder / 4-cyl ifadeleri kullanılır. 24V gibi supap ifadeleri silindir sayısı değildir.",
        "- Aynı motor metnindeki tekrar eden eşit sayılar tek kanıt sayılır; farklı aday sayılar çelişki olarak eksik bırakılır. Pozitif olmayan sayılar da raporlanarak eksik bırakılır.",
        "- `transmission_group`: açık etiketler Automatic, Manual, CVT, Dual-clutch gruplarına ayrılır. CVT veya Dual-clutch ile birlikte Automatic yazılması, özel alt grubun seçilmesini engellemez.",
        "- Açık otomatik etiketiyle birlikte 'Manual Modes' ifadesi manuel şanzıman sayılmaz. 'Auto-Shift' tek başına çift kavrama kanıtı değildir.",
        "- 'Dual Shift Mode', 'Variable', yalnızca vites sayısı ve çözülemeyen ifadeler belirsiz bırakılır. Manuel/otomatik veya CVT/çift kavrama çelişkileri de eksik bırakılır.",
        "- `accident_missing`, `clean_title_missing`: bilgi eksikse 1, mevcutsa 0. Bunlar kaza veya tapu durumunun kendisi değildir.",
        "- Kaynak eksikse özellikle elektrikli araçlarda hacim/silindir sayısı sıfırla doldurulmaz. Metinde açık bilgi yoksa tahmin yapılmaz.",
        "", "## Çıkarım sonuçları",
        "`extracted`: çıkarılan; `missing_source`: kaynak eksik; `no_explicit_match`: açık ifade yok; `conflict`: çelişkili; `nonpositive_value`: pozitif olmayan değer; `missing_total`: sonuçta eksik kalan toplam.",
        "```text", summary.to_string(), "```",
        "", "## Yeni sayısal özelliklerin özetleri", "```text",
        result[list(PATTERNS)].describe().round(3).to_string(), "```",
        "", "## Şanzıman grupları", "```text",
        result.transmission_group.value_counts(dropna=False).to_string(), "```",
        "", "## Eksiklik göstergeleri",
    ]
    for col in ["accident", "clean_title"]:
        lines.append(f"- `{col}_missing`: 1 olan {int(result[col + '_missing'].sum())}, 0 olan {int((result[col + '_missing'] == 0).sum())} kayıt.")
    exceptional = audit[audit.status.isin(["conflict", "nonpositive_value"])]
    if not exceptional.empty:
        lines += ["", "## Çelişkili/geçersiz adayların tamamı", "```text", exceptional.to_string(index=False), "```"]
    lines += [
        "", "## Denetim ve sınırlar",
        "`extraction_audit.csv` her motor/şanzıman çıkarımı için kaynak CSV satırını (başlık nedeniyle ilk veri satırı 2), kaynak metni, sonucu ve durumunu içerir.",
        "Kurallar açık metin eşleşmesine dayanır; üretici bilgisiyle dış doğrulama yapılmadı. Çıkarılabilen özellikler hatasız teknik veri garantisi değildir.",
        "Mevcut sütunlar pandas karşılaştırmasıyla, çıktı ise yeniden okunarak doğrulandı. Kaynak dosyaların SHA-256 özetleri değişmedi:",
    ]
    for path, before in hashes.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != before:
            raise RuntimeError(f"Kaynak değişti: {path}")
        lines.append(f"- `{path.relative_to(BASE)}`: `{before}`")
    lines += [
        "", "## Sonraki aşama",
        "Araç yaşı ve yıllık ortalama mesafe üretilmedi; toplama tarihi bilinmiyor. Eksik doldurma, kodlama, ölçekleme, hedef dönüşümü veya model eğitimi yapılmadı.",
        "Yeni eksik göstergeler orijinal sütunlarla ilişkili olabilir; model öncesinde yararları eğitim verisinde değerlendirilmelidir.",
        "Regresyon ve kümeleme veri hazırlığı ayrı kararlarla yapılacak. Regresyonda öğrenilen dönüşümler yalnızca eğitim bölümünde öğrenilecek.", "",
    ]
    report = REPORT_DIR / "OZELLIK_RAPORU.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(summary.to_string())
    print(f"Çıktı: {OUTPUT}; boyut: {result.shape}")
    print(f"Rapor: {report}")
    print("Kaynaklar ve mevcut sütunlar korundu; CSV yeniden okuma kontrolü geçti.")


if __name__ == "__main__":
    main()
