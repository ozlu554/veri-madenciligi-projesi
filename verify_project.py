"""Mevcut proje çıktılarını salt okunur kontrol eder; dosya üretmez."""

import ast
import hashlib
import json
from pathlib import Path, PureWindowsPath

import joblib
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
            # Windows manifest paths and Git LF/CRLF conversion are portable.
            source = base.joinpath(*PureWindowsPath(relative).parts)
            content = source.read_bytes()
            candidates = {hashlib.sha256(content).hexdigest()}
            if source.suffix.lower() == ".csv":
                lf_content = content.replace(b"\r\n", b"\n")
                candidates.update(hashlib.sha256(value).hexdigest() for value in
                                  (lf_content, lf_content.replace(b"\n", b"\r\n")))
            assert expected in candidates, relative
            if hashlib.sha256(content).hexdigest() != expected:
                print(f"Satır sonu farkı doğrulandı (LF/CRLF): {relative}")
    train = sparse.load_npz(base / "data/regression/X_train.npz")
    test = sparse.load_npz(base / "data/regression/X_test.npz")
    cluster = np.load(base / "data/clustering/X_clustering.npy")
    assert train.shape == (3207, 79) and test.shape == (802, 79)
    assert cluster.shape == (4009, 5)
    assert len(reg["feature_names"]) == train.shape[1]
    for matrix in [train.data, test.data, cluster]:
        assert np.isfinite(matrix).all()
    regression_preprocessor = joblib.load(base / "data/regression/preprocessor.joblib")
    assert regression_preprocessor.get_feature_names_out().tolist() == reg["feature_names"]
    for split, matrix in [("train", train), ("test", test)]:
        frame = pd.read_csv(base / f"data/regression/{split}_before_preprocessing.csv")
        columns = reg["numeric_columns"] + reg["categorical_columns"]
        transformed = sparse.csr_matrix(regression_preprocessor.transform(frame[columns]))
        np.testing.assert_allclose(transformed.toarray(), matrix.toarray(), rtol=1e-10, atol=1e-12)
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
    clustering_preprocessor = joblib.load(base / "data/clustering/preprocessor.joblib")
    np.testing.assert_allclose(
        clustering_preprocessor.transform(features[clu["features"]]), cluster,
        rtol=1e-10, atol=1e-12,
    )
    cluster_csv = pd.read_csv(base / "data/clustering/X_clustering.csv")
    assert cluster_csv.columns.tolist() == clu["features"]
    np.testing.assert_allclose(cluster_csv.to_numpy(), cluster, rtol=1e-10, atol=1e-12)
    context = pd.read_csv(base / "data/clustering/interpretation_context.csv")
    expected_rows = list(range(2, len(features) + 2))
    assert clu["source_csv_rows"] == expected_rows
    assert context.source_csv_row.tolist() == mask.source_csv_row.tolist() == expected_rows
    pd.testing.assert_frame_equal(context.drop(columns="source_csv_row"), features)
    print("Ön işleyiciler, matris içerikleri ve kümeleme satır eşleşmeleri doğrulandı.")
    print("SON KONTROL GEÇTİ")
    print("Python sözdizimi, kaynak SHA-256, korunan sütunlar ve çıktı boyutları doğrulandı.")
    print("Eğitim/test ayrılığı, kaynak satırları, hedef eşleşmeleri ve doldurma maskesi doğrulandı.")
    print("Hazırlanan matrislerde eksik veya sonsuz değer yok. Dosya değiştirilmedi.")


if __name__ == "__main__":
    main()
