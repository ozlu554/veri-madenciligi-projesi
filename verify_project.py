"""Mevcut proje çıktılarını salt okunur kontrol eder; dosya üretmez."""

import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse


def main():
    base = Path(__file__).resolve().parent
    for path in base.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    raw = pd.read_csv(base / "used_cars.csv")
    cleaned = pd.read_csv(base / "data/used_cars_cleaned.csv")
    features = pd.read_csv(base / "data/used_cars_features.csv")
    assert raw.shape == cleaned.shape == (4009, 12)
    assert features.shape == (4009, 18)
    pd.testing.assert_frame_equal(cleaned, features[cleaned.columns])
    reg = json.loads((base / "data/regression/manifest.json").read_text(encoding="utf-8"))
    clu = json.loads((base / "data/clustering/manifest.json").read_text(encoding="utf-8"))
    for manifest in [reg, clu]:
        for relative, expected in manifest["source_sha256"].items():
            assert hashlib.sha256((base / relative).read_bytes()).hexdigest() == expected, relative
    train = sparse.load_npz(base / "data/regression/X_train.npz")
    test = sparse.load_npz(base / "data/regression/X_test.npz")
    cluster = np.load(base / "data/clustering/X_clustering.npy")
    assert train.shape == (3207, 79) and test.shape == (802, 79)
    assert cluster.shape == (4009, 5)
    assert len(reg["feature_names"]) == train.shape[1]
    for matrix in [train.data, test.data, cluster]:
        assert np.isfinite(matrix).all()
    for split, matrix in [("train", train), ("test", test)]:
        frame = pd.read_csv(base / f"data/regression/{split}_before_preprocessing.csv")
        rows = reg[f"{split}_source_csv_rows"]
        assert frame.source_csv_row.tolist() == rows
        assert len(frame) == matrix.shape[0]
        np.testing.assert_array_equal(np.load(base / f"data/regression/y_{split}.npy"), frame.price.to_numpy())
        pd.testing.assert_frame_equal(
            frame.drop(columns="source_csv_row").reset_index(drop=True),
            features.iloc[np.array(rows) - 2][frame.columns.drop("source_csv_row")].reset_index(drop=True),
        )
    train_rows, test_rows = set(reg["train_source_csv_rows"]), set(reg["test_source_csv_rows"])
    assert train_rows.isdisjoint(test_rows)
    assert train_rows | test_rows == set(range(2, len(raw) + 2))
    assert "price" not in clu["features"]
    mask = pd.read_csv(base / "data/clustering/imputation_mask.csv")
    np.testing.assert_array_equal(mask[clu["features"]].to_numpy(), features[clu["features"]].isna().astype(int).to_numpy())
    print("SON KONTROL GEÇTİ")
    print("Python sözdizimi, kaynak SHA-256, korunan sütunlar ve çıktı boyutları doğrulandı.")
    print("Eğitim/test ayrılığı, kaynak satırları, hedef eşleşmeleri ve doldurma maskesi doğrulandı.")
    print("Hazırlanan matrislerde eksik veya sonsuz değer yok. Dosya değiştirilmedi.")


if __name__ == "__main__":
    main()
