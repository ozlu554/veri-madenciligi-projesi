"""Regresyon için bölme ve ön işleme; tahmin modeli eğitmez.

Windows: .venv-windows/Scripts/python.exe prepare_regression.py
macOS: .venv/bin/python prepare_regression.py
"""

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "data" / "used_cars_features.csv"
OUTPUT = BASE / "data" / "regression"
REPORT = BASE / "reports" / "regression" / "REGRESYON_HAZIRLIK_RAPORU.md"
NUMERIC = ["model_year", "milage", "horsepower_hp", "engine_displacement_l",
           "cylinder_count", "accident_missing", "clean_title_missing"]
CATEGORICAL = ["brand", "fuel_type", "transmission_group", "accident", "clean_title"]
TARGET = "price"
SEED = 42


def make_preprocessor():
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown", keep_empty_features=True)),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
    ])
    return ColumnTransformer(
        [("numeric", numeric, NUMERIC), ("categorical", categorical, CATEGORICAL)],
        remainder="drop", sparse_threshold=1.0,
    )


def main():
    guarded = [BASE / "used_cars.csv", BASE / "data" / "used_cars_cleaned.csv", SOURCE]
    hashes = {str(path.relative_to(BASE)): hashlib.sha256(path.read_bytes()).hexdigest() for path in guarded}
    data = pd.read_csv(SOURCE)
    if data[TARGET].isna().any() or not np.isfinite(data[TARGET].to_numpy()).all():
        raise ValueError("Hedefte eksik veya sonlu olmayan değer var; çıktı yazılmadı.")
    X, y = data[NUMERIC + CATEGORICAL].copy(), data[TARGET].copy()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
    preprocessor = make_preprocessor()
    train_matrix = sparse.csr_matrix(preprocessor.fit_transform(X_train))
    test_matrix = sparse.csr_matrix(preprocessor.transform(X_test))
    feature_names = preprocessor.get_feature_names_out().tolist()
    numeric_fit = preprocessor.named_transformers_["numeric"]
    categorical_fit = preprocessor.named_transformers_["categorical"]
    # Eğitim/test ayrılığı, satır sırası, sonluluk ve öğrenilen istatistikler.
    assert X_train.index.intersection(X_test.index).empty
    assert set(X_train.index).union(X_test.index) == set(data.index)
    assert X_train.index.equals(y_train.index) and X_test.index.equals(y_test.index)
    assert train_matrix.shape == (len(X_train), len(feature_names))
    assert test_matrix.shape == (len(X_test), len(feature_names))
    assert np.isfinite(train_matrix.data).all() and np.isfinite(test_matrix.data).all()
    np.testing.assert_allclose(numeric_fit.named_steps["imputer"].statistics_, X_train[NUMERIC].median().to_numpy())
    filled_train = numeric_fit.named_steps["imputer"].transform(X_train[NUMERIC])
    np.testing.assert_allclose(numeric_fit.named_steps["scaler"].mean_, filled_train.mean(axis=0))

    unknowns = {}
    for col, categories in zip(CATEGORICAL, categorical_fit.named_steps["encoder"].categories_):
        values = X_test[col].fillna("Unknown")
        unknowns[col] = {"unseen_test_rows": int((~values.isin(categories)).sum()),
                         "train_categories": len(categories)}
    # Testte yepyeni kategori oluştuğunda dönüşümün çalıştığını doğrula.
    probe = X_test.head(1).copy()
    probe.loc[:, "brand"] = "__UNSEEN_BRAND_CHECK__"
    assert preprocessor.transform(probe).shape[1] == len(feature_names)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    sparse.save_npz(OUTPUT / "X_train.npz", train_matrix)
    sparse.save_npz(OUTPUT / "X_test.npz", test_matrix)
    np.save(OUTPUT / "y_train.npy", y_train.to_numpy())
    np.save(OUTPUT / "y_test.npy", y_test.to_numpy())
    # Çapraz doğrulamada dönüşümleri her katın kendi eğitiminde yeniden öğrenmek için.
    for name, values, targets in [("train", X_train, y_train), ("test", X_test, y_test)]:
        raw_split = values.copy()
        raw_split.insert(0, "source_csv_row", values.index + 2)
        raw_split[TARGET] = targets
        raw_split.to_csv(OUTPUT / f"{name}_before_preprocessing.csv", index=False)
    joblib.dump(preprocessor, OUTPUT / "preprocessor.joblib")
    manifest = {
        "target": TARGET, "random_state": SEED, "test_size": 0.2,
        "numeric_columns": NUMERIC, "categorical_columns": CATEGORICAL,
        "feature_names": feature_names, "train_shape": list(train_matrix.shape),
        "test_shape": list(test_matrix.shape), "sklearn_version": sklearn.__version__,
        "source_sha256": hashes, "test_unseen_categories": unknowns,
        "train_source_csv_rows": (X_train.index + 2).tolist(),
        "test_source_csv_rows": (X_test.index + 2).tolist(),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # Kaydedilen matris, hedef ve ön işleyici aynı sonucu veriyor mu?
    restored = joblib.load(OUTPUT / "preprocessor.joblib")
    np.testing.assert_allclose(restored.transform(X_test).toarray(), test_matrix.toarray())
    assert (sparse.load_npz(OUTPUT / "X_train.npz") != train_matrix).nnz == 0
    assert (sparse.load_npz(OUTPUT / "X_test.npz") != test_matrix).nnz == 0
    np.testing.assert_array_equal(np.load(OUTPUT / "y_train.npy"), y_train.to_numpy())
    np.testing.assert_array_equal(np.load(OUTPUT / "y_test.npy"), y_test.to_numpy())
    for relative, before in hashes.items():
        if hashlib.sha256((BASE / relative).read_bytes()).hexdigest() != before:
            raise RuntimeError(f"Kaynak dosya değişti: {relative}")

    stats = pd.DataFrame({"sutun": NUMERIC,
                          "egitim_medyani": numeric_fit.named_steps["imputer"].statistics_,
                          "olcekleme_ortalamasi": numeric_fit.named_steps["scaler"].mean_,
                          "olcekleme_boleni": numeric_fit.named_steps["scaler"].scale_})
    lines = [
        "# Regresyon Veri Hazırlama Raporu", "",
        "## Amaç ve kapsam",
        "Hedef fiyatı tahmin edecek modeller için veri hazırlamak; bu aşamada tahmin modeli eğitilmedi veya değerlendirilmedi.",
        "Kaynak: `data/used_cars_features.csv`. Kaynaklar değiştirilmedi; fiyat ve uç gözlemler korundu.",
        f"Eğitim: {len(X_train)} kayıt; test: {len(X_test)} kayıt. %80/%20 rastgele bölme, `random_state=42`.",
        "4.009 kaydın %20'si tam sayı olmadığı için test 802, eğitim 3.207 kayıttır.",
        "", "## Girdiler ve hedef",
        "Hedef: `price`; girdilere dahil değildir. Fiyatın `$` gösterimi korunur, para birimi kodu ayrıca doğrulanmamıştır.",
        "Sayısal: " + ", ".join(f"`{c}`" for c in NUMERIC) + ".",
        "Kategorik: " + ", ".join(f"`{c}`" for c in CATEGORICAL) + ".",
        "`model`, `engine`, `transmission`, `ext_col`, `int_col` başlangıç hazırlığında dışarıda bırakıldı. Ham metinler çıkarılmış özelliklerle örtüşüyor; model ve renkler yüksek kategori sayısına sahip. Bu seçim henüz performansla doğrulanmış değildir.",
        "", "## Yöntemler ve gerekçeler",
        "1. `train_test_split`: öğrenilen tüm dönüşümlerden önce bölme yapıldı; satır sızıntısı önlendi.",
        "2. Sayısal `SimpleImputer(strategy='median')`: uç değerlere ortalamadan daha dayanıklı doldurma; medyanlar yalnızca eğitimden öğrenildi.",
        "3. `StandardScaler`: eğitimde doldurulmuş sayısal girdilerden ortalama/standart sapma öğrenildi. Eksiklik göstergeleri dahil sayısal sütunlara uygulandı. Ağaç tabanlı modeller için zorunlu değildir.",
        "4. Kategorik `SimpleImputer(strategy='constant', fill_value='Unknown')`: bilinmeyen bilgiyi ayrı kategoriyle gösterir; kaza/tapu durumu varsaymaz.",
        "5. `OneHotEncoder(handle_unknown='ignore')`: sıralama varsaymadan kodlama. Testte yeni kategori ilgili sütunun bütün gösterge değerlerinde sıfır olur; Unknown kategorisiyle aynı anlamda değildir.",
        "6. `Pipeline` ve `ColumnTransformer`: sayısal/kategorik adımları tek, yeniden kullanılabilir ön işleyicide birleştirir. Eğitimde `fit_transform`, testte yalnızca `transform` kullanıldı.",
        "", "## Öğrenilen sayısal istatistikler", "```text", stats.round(5).to_string(index=False), "```",
        "", "## Kodlama sonuçları",
        f"Eğitim matrisi: {train_matrix.shape}; test matrisi: {test_matrix.shape}. Seyrek CSR biçimiyle `.npz` olarak kaydedildi.",
        "```text", pd.DataFrame(unknowns).T.to_string(), "```",
        "", "## Doğrulamalar",
        "- Eğitim/test satırları ayrık, birleşimleri tüm kayıtları kapsıyor; X/y satır sıraları aynı.",
        "- İki matriste de eksik/sonsuz değer yok ve sütun sayıları aynı.",
        "- Doldurma medyanları ve ölçekleme ortalamaları yalnızca eğitim verisiyle karşılaştırılarak doğrulandı.",
        "- Yeni marka içeren örnek dönüştürüldü; görülmemiş kategori hata vermedi.",
        "- Kaydedilen matrisler/hedefler ve yeniden yüklenen ön işleyici doğrulandı.",
        "- Ham, temizlenmiş ve özellikli kaynakların SHA-256 özetleri değişmedi.",
        "", "## Dosyalar ve kullanım",
        "Çıktı dizini: `data/regression/`.",
        "- `X_train.npz`, `X_test.npz`: sıralı özellik matrisleri; `scipy.sparse.load_npz` ile okunur.",
        "- `y_train.npy`, `y_test.npy`: aynı sıradaki fiyat hedefleri; `numpy.load` ile okunur.",
        "- `preprocessor.joblib`: eğitimde öğrenilmiş ön işleyici.",
        "- `manifest.json`: sütun sırası, kaynak satırları, sürüm, bölme ayarları ve dosya özetleri.",
        "- `train_before_preprocessing.csv`, `test_before_preprocessing.csv`: öğrenilen dönüşümlerden önceki seçilmiş girdiler, hedef ve kaynak satır numarası. `price` ve `source_csv_row` model girdisi değildir.",
        "", "## Sınırlar ve sonraki aşama",
        "Bu rastgele bölme aynı araç/satıcı kimliğine göre gruplanmış veya zamana göre ayrılmış değildir; dosyada bunu doğrulayacak kimlik/toplama tarihi yoktur.",
        "Eksiklik ve kategori seçimleri henüz model performansıyla sınanmadı. Fiyat dönüşümü ve uç değer silme uygulanmadı.",
        "İleride çapraz doğrulama yapılırsa hazır dönüştürülmüş eğitim matrisiyle ön işleme seçimi yapılmamalı: `make_preprocessor()` ile yeni ön işleyici modelle aynı Pipeline içinde her katın eğitim bölümünde yeniden öğrenilmelidir. Bunun için dönüşüm öncesi bölmeler saklandı. Test bölümü model seçimi için kullanılmamalıdır.",
        "Kümeleme için veri hazırlığı ayrı onayla yapılacak. Bu aşama regresyon modeli eğitimi değildir.", "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Eğitim: {train_matrix.shape}; test: {test_matrix.shape}")
    print(pd.DataFrame(unknowns).T.to_string())
    print(f"Rapor: {REPORT}")
    print("Kontroller geçti; tahmin modeli eğitilmedi.")


if __name__ == "__main__":
    main()
