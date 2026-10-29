"""Keşif amaçlı kümeleme girdilerini hazırlar; kümeleme modeli eğitmez.

Windows: .venv-windows/Scripts/python.exe prepare_clustering.py
macOS: .venv/bin/python prepare_clustering.py
"""

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "data" / "used_cars_features.csv"
OUTPUT = BASE / "data" / "clustering"
REPORT = BASE / "reports" / "clustering" / "KUMELEME_HAZIRLIK_RAPORU.md"
FEATURES = ["model_year", "milage", "horsepower_hp", "engine_displacement_l", "cylinder_count"]


def make_preprocessor():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scaler", RobustScaler(quantile_range=(25.0, 75.0))),
    ])


def main():
    guarded = [BASE / "used_cars.csv", BASE / "data" / "used_cars_cleaned.csv", SOURCE]
    hashes = {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in guarded}
    source = pd.read_csv(SOURCE)
    X = source[FEATURES].copy()
    if X.isna().all().any():
        raise ValueError("Tamamen eksik sütunda medyan hesaplanamaz; çıktı yazılmadı.")
    if np.isinf(X.to_numpy(dtype=float)).any():
        raise ValueError("Girdide sonsuz değer var; çıktı yazılmadı.")
    preprocessor = make_preprocessor()
    matrix = preprocessor.fit_transform(X)
    imputer = preprocessor.named_steps["imputer"]
    scaler = preprocessor.named_steps["scaler"]
    filled = imputer.transform(X)
    assert matrix.shape == X.shape
    assert np.isfinite(matrix).all()
    np.testing.assert_allclose(imputer.statistics_, X.median().to_numpy())
    np.testing.assert_allclose(scaler.center_, np.median(filled, axis=0))
    q1, q3 = np.percentile(filled, [25, 75], axis=0)
    iqr = q3 - q1
    # Bu veri için IQR sıfır değil; sklearn sıfıra çok yakın aralıklarda böleni 1 yapar.
    assert (iqr > 0).all()
    np.testing.assert_allclose(scaler.scale_, iqr)
    np.testing.assert_allclose(matrix, (filled - scaler.center_) / scaler.scale_)
    observed = X.notna().to_numpy()
    np.testing.assert_array_equal(filled[observed], X.to_numpy()[observed])

    OUTPUT.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT / "X_clustering.npy", matrix)
    pd.DataFrame(matrix, columns=FEATURES).to_csv(OUTPUT / "X_clustering.csv", index=False)
    # Yorumlama verisi matristen ayrı tutulur; fiyat ve kategoriler uzaklık girdisi değildir.
    context = source.copy()
    context.insert(0, "source_csv_row", source.index + 2)
    context.to_csv(OUTPUT / "interpretation_context.csv", index=False)
    missing = X.isna().astype("int8")
    missing.insert(0, "source_csv_row", X.index + 2)
    missing.to_csv(OUTPUT / "imputation_mask.csv", index=False)
    joblib.dump(preprocessor, OUTPUT / "preprocessor.joblib")
    manifest = {
        "purpose": "Exploratory clustering preparation; no clustering fitted",
        "features": FEATURES, "shape": list(matrix.shape), "sklearn_version": sklearn.__version__,
        "fit_scope": "All 4009 source rows; no train/test split",
        "imputation": "median", "scaling": "RobustScaler", "quantile_range": [25.0, 75.0],
        "imputed_counts": {col: int(X[col].isna().sum()) for col in FEATURES},
        "imputer_medians": imputer.statistics_.tolist(), "scaler_centers": scaler.center_.tolist(),
        "scaler_divisors": scaler.scale_.tolist(), "source_sha256": hashes,
        "source_csv_rows": (source.index + 2).tolist(),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    np.testing.assert_array_equal(np.load(OUTPUT / "X_clustering.npy"), matrix)
    np.testing.assert_allclose(pd.read_csv(OUTPUT / "X_clustering.csv").to_numpy(), matrix, atol=1e-12)
    np.testing.assert_allclose(joblib.load(OUTPUT / "preprocessor.joblib").transform(X), matrix)
    restored_context = pd.read_csv(OUTPUT / "interpretation_context.csv")
    pd.testing.assert_frame_equal(restored_context.drop(columns="source_csv_row"), source)
    np.testing.assert_array_equal(restored_context.source_csv_row.to_numpy(), source.index.to_numpy() + 2)
    for relative, before in hashes.items():
        if hashlib.sha256((BASE / relative).read_bytes()).hexdigest() != before:
            raise RuntimeError(f"Kaynak değişti: {relative}")

    statistics = pd.DataFrame({"sutun": FEATURES, "doldurulan": X.isna().sum().to_numpy(),
                               "doldurma_medyani": imputer.statistics_, "olcekleme_merkezi": scaler.center_,
                               "doldurma_sonrasi_Q1": q1, "doldurma_sonrasi_Q3": q3,
                               "olcekleme_boleni_IQR": scaler.scale_})
    rows_imputed = int(X.isna().any(axis=1).sum())
    complete_motor_missing = int(X[["horsepower_hp", "engine_displacement_l", "cylinder_count"]].isna().all(axis=1).sum())
    lines = [
        "# Kümeleme Veri Hazırlama Raporu", "",
        "## Amaç ve kapsam",
        "Benzer teknik özelliklere sahip araçları keşif amaçlı gruplamaya uygun sayısal girdi hazırlamak.",
        "Kaynak: `data/used_cars_features.csv`. Hiçbir kümeleme algoritması çalıştırılmadı; küme sayısı/etiketi veya kalite skoru üretilmedi.",
        f"Girdi: {source.shape[0]} kayıt × {source.shape[1]} sütun. Hazırlanan matris: {matrix.shape[0]} kayıt × {matrix.shape[1]} özellik.",
        "Tüm kayıtlar aynı sırada korundu. Yalnızca onaylanan beş sütun seçildi; kaynak dosyalar değiştirilmedi.",
        "", "## Özellik seçimi ve gerekçeler",
        "- `model_year`: üretim yılı; araç yaşı üretilmedi, veri toplama tarihi bilinmiyor.",
        "- `milage`: mesafe, mil biriminde; kilometreye çevrilmedi.",
        "- `horsepower_hp`: metinden çıkarılan HP değeri.",
        "- `engine_displacement_l`: litre olarak motor hacmi.",
        "- `cylinder_count`: silindir sayısı.",
        "Fiyat, marka, model, yakıt türü, renkler, şanzıman ve kaza/tapu bilgileri uzaklık matrisine dahil edilmedi; yorumlama için ayrı dosyada korundu. Eksiklik göstergeleri de matrisin girdisi değildir.",
        "", "## Uygulanan yöntemler",
        "1. `SimpleImputer(strategy='median')`: beş sütunun eksikleri ilgili sütunun tüm veri üzerindeki medyanıyla dolduruldu. Aykırı değerlere ortalamadan daha dayanıklı bir başlangıç yöntemidir.",
        "2. `RobustScaler(quantile_range=(25, 75))`: doldurulmuş sütunlardan medyan çıkarıldı ve IQR'ye (Q3 − Q1) bölündü. Birimler arasındaki ölçek farkını azaltır; uç kayıtları silmez veya kırpmaz.",
        "3. `Pipeline`: doldurma ve ölçekleme tek yeniden kullanılabilir ön işleyicide saklandı.",
        "Bu keşif hazırlığında bütün veriye `fit_transform` uygulandı; eğitim/test ayrımı yapılmadı. Bu dosyalar yeni verilere genelleme başarısı kanıtı değildir. İleride ayrı değerlendirme yapılırsa dönüşümler sadece o değerlendirmenin eğitim bölümünde yeniden öğrenilmelidir.",
        "", "## Doldurma ve ölçekleme sonuçları", "```text",
        statistics.round(5).to_string(index=False), "```",
        "Çeyrekler ve ölçekleme böleni doldurma SONRASI hesaplandı; ham dolu gözlemlerin çeyreklerinden farklı olabilir.",
        f"En az bir özelliği doldurulan kayıt: {rows_imputed}. Üç motor özelliği de eksik olan kayıt: {complete_motor_missing}.",
        "", "## Ölçeklenmiş dağılımlar", "```text",
        pd.DataFrame(matrix, columns=FEATURES).describe().round(4).to_string(), "```",
        "", "## Doğrulama",
        "- 4.009 kayıt ve beş özellik korundu; fiyat ve kategoriler matriste yok.",
        "- Matrisin tüm değerleri sonlu; eksik değer yok.",
        "- Doldurma medyanları, ölçekleme merkezleri ve IQR bölenleri bağımsız hesaplarla karşılaştırıldı.",
        "- Dolu gözlemler doldurma adımında aynı kaldı; ölçekleme yalnızca doğrusal dönüşüm uyguladı.",
        "- NPY ve CSV yeniden okundu; ön işleyici yeniden yüklenerek aynı dönüşüm doğrulandı.",
        "- Yorumlama verisi ve kaynak satır eşleşmesi doğrulandı; kaynak dosyaların SHA-256 özetleri değişmedi.",
        "", "## Üretilen dosyalar",
        "Dizin: `data/clustering/`.",
        "- `X_clustering.npy`: model girdisi olacak sayısal matris; `numpy.load` ile okunur.",
        "- `X_clustering.csv`: aynı matrisin sütun adlarını içeren okunabilir sürümü.",
        "- `preprocessor.joblib`: doldurma ve ölçeklemeyi öğrenmiş Pipeline.",
        "- `manifest.json`: özellik sırası, parametreler, istatistikler ve kaynak dosya/satır bilgileri.",
        "- `interpretation_context.csv`: fiyat ve kategoriler dahil özgün özellikli veri ve `source_csv_row`. Uzaklık girdisi değildir.",
        "- `imputation_mask.csv`: her seçili özellik için 1=dolduruldu, 0=özgün değer mevcuttu. Uzaklık girdisi değildir.",
        "Kaynak satır numarası CSV başlığını hesaba katar: ilk veri satırı 2'dir. Bütün dosyalar aynı araç sırasındadır.",
        "", "## Sınırlar ve yorumlama",
        "Medyanla doldurulan motor özellikleri, teknik bilgisi eksik araçları yapay olarak birbirine yaklaştırabilir. Elektrikli araçlarda eksik hacim/silindir bilgisi için de medyan kullanıldı; bu doldurma teknik bir gerçek olarak yorumlanmamalı, yorumlama sırasında maske ve yakıt türü incelenmelidir.",
        "Motor gücü, hacim ve silindir sayısı ilişkili olabilir; uzaklıkta motor özelliklerine daha fazla ağırlık verilmesine yol açabilir. Bu aşamada ağırlıklandırma veya boyut indirgeme yapılmadı.",
        "RobustScaler uç değerleri ortadan kaldırmaz; uç araçlar bazı algoritmalarda etkili olmaya devam edebilir. Kümeleme algoritması ve parametreleri ayrıca değerlendirilmeli.",
        "Kümeleme eğitimi bu aşamanın dışında kaldı. Sonuç kalitesi veya bulunan grup sayısı hakkında henüz iddia yoktur.", "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(statistics.to_string(index=False))
    print(f"Matris: {matrix.shape}; en az bir doldurma içeren kayıt: {rows_imputed}")
    print(f"Rapor: {REPORT}")
    print("Kontroller geçti; kümeleme algoritması çalıştırılmadı.")


if __name__ == "__main__":
    main()
