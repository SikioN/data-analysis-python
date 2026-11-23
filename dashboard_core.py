"""Расчётное ядро для интерактивного дашборда ЛР4 (по данным и методам ЛР1–3)."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.neighbors import NearestNeighbors, radius_neighbors_graph
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "Econom_Cities_data.csv"
RANDOM_STATE = 42

CLUSTER_NAMES_K4 = {
    0: "Работают много, получают мало",
    1: "Дешёвая периферия",
    2: "Благополучный Запад",
    3: "Дорого и богато",
}

CLUSTER_NAMES_DBSCAN = {
    -1: "Шум (нетипичные города)",
    0: "Небогатые города",
    1: "Благополучный Запад",
}


def load_data(path: Path = DATA_PATH):
    """Загружает данные городов, удаляет строки с пропусками -9999 и стандартизует признаки."""
    df_raw = pd.read_csv(path, sep=";", decimal=",", index_col="City")
    df_raw = df_raw.replace(-9999, np.nan)
    dropped = df_raw[df_raw.isna().any(axis=1)]
    df = df_raw.dropna().copy()
    names = df.index.str.replace("_", " ").tolist()

    scaler = StandardScaler()
    X = scaler.fit_transform(df)
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    xy_pca = pca.fit_transform(X)
    z_df = pd.DataFrame(X, index=df.index, columns=df.columns)

    return {
        "df_raw": df_raw,
        "dropped": dropped,
        "df": df,
        "names": names,
        "scaler": scaler,
        "pca": pca,
        "X": X,
        "z_df": z_df,
        "pca_var": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "xy_pca": xy_pca,
    }


def relabel(labels, df: pd.DataFrame, by: str = "Salary") -> np.ndarray:
    """Перенумеровывает кластеры 0, 1, ... по возрастанию среднего `by`, оставляя шум (-1)."""
    labels = np.asarray(labels)
    order = df[by].groupby(labels).mean().drop(-1, errors="ignore").sort_values().index
    mapping = {old: new for new, old in enumerate(order)} | {-1: -1}
    return np.array([mapping[int(label)] for label in labels])


def silhouette_wo_noise(X: np.ndarray, labels: np.ndarray):
    """Силуэт по нешумовым точкам, либо None если кластеров меньше двух."""
    mask = labels != -1
    if len(np.unique(labels[mask])) < 2:
        return None
    return float(silhouette_score(X[mask], labels[mask]))


def _evaluate_run(df: pd.DataFrame, X: np.ndarray, z_df: pd.DataFrame, labels: np.ndarray, ref_km4: np.ndarray) -> dict:
    """Собирает метрики качества и профили кластеров для одного разбиения."""
    labels = np.asarray(labels, dtype=int)
    n_clusters = len(set(labels) - {-1})
    n_noise = int((labels == -1).sum())
    noise_pct = round(100.0 * n_noise / len(labels), 1)

    mask = labels != -1
    sil = silhouette_wo_noise(X, labels)
    if n_clusters >= 2 and mask.sum() > n_clusters:
        ch = float(calinski_harabasz_score(X[mask], labels[mask]))
        db = float(davies_bouldin_score(X[mask], labels[mask]))
        sil_samples = np.zeros(len(labels), dtype=float)
        sil_samples[mask] = silhouette_samples(X[mask], labels[mask])
        if not mask.all():
            sil_samples[~mask] = np.nan
    else:
        ch = None
        db = None
        sil_samples = np.full(len(labels), np.nan)

    ari_km4 = float(adjusted_rand_score(labels, ref_km4))

    work_df = df.assign(Salary_to_Price=df["Salary"] / df["Price"])
    profiles = []
    for cl in sorted(set(labels)):
        sub_mask = labels == cl
        sub = work_df[sub_mask]
        z_sub = z_df[sub_mask]
        cities = [c.replace("_", " ") for c in df.index[sub_mask]]
        profiles.append({
            "cluster": int(cl),
            "size": int(sub_mask.sum()),
            "Work": round(float(sub["Work"].mean()), 1),
            "Price": round(float(sub["Price"].mean()), 1),
            "Salary": round(float(sub["Salary"].mean()), 1),
            "Salary_to_Price": round(float(sub["Salary_to_Price"].mean()), 2),
            "z_Work": round(float(z_sub["Work"].mean()), 2),
            "z_Price": round(float(z_sub["Price"].mean()), 2),
            "z_Salary": round(float(z_sub["Salary"].mean()), 2),
            "cities": cities,
        })

    return {
        "labels": [int(x) for x in labels],
        "n_clusters": int(n_clusters),
        "n_noise": n_noise,
        "noise_pct": noise_pct,
        "silhouette": round(sil, 3) if sil is not None else None,
        "calinski_harabasz": round(ch, 2) if ch is not None else None,
        "davies_bouldin": round(db, 3) if db is not None else None,
        "ari_km4": round(ari_km4, 3),
        "sil_samples": [None if np.isnan(v) else round(float(v), 3) for v in sil_samples],
        "profiles": profiles,
    }


def build_dashboard_payload(path: Path = DATA_PATH) -> dict:
    """Считает все данные, модели и метрики ЛР1–3 для передачи в дашборд."""
    data = load_data(path)
    df = data["df"]
    X = data["X"]
    z_df = data["z_df"]
    xy_pca = data["xy_pca"]

    # Эталонное разбиение k-means (k=4) для расчёта ARI
    km4_raw = KMeans(n_clusters=4, n_init=20, random_state=RANDOM_STATE).fit(X)
    ref_km4 = relabel(km4_raw.labels_, df)

    # 1. Иерархическая кластеризация (Ward)
    Z = linkage(X, method="ward")
    heights_rev = Z[::-1, 2][:10]
    ward_heights = []
    for idx_k in range(1, 11):
        h = float(heights_rev[idx_k - 1])
        nxt = float(heights_rev[idx_k]) if idx_k < 10 else None
        ward_heights.append({
            "k": idx_k,
            "height": round(h, 2),
            "jump": round(h - nxt, 2) if nxt is not None else None,
        })

    ward_runs = {}
    for k in range(2, 9):
        lbl = relabel(fcluster(Z, k, criterion="maxclust"), df)
        ward_runs[str(k)] = _evaluate_run(df, X, z_df, lbl, ref_km4)

    # 2. k-means (k=2..8)
    gx = np.linspace(xy_pca[:, 0].min() - 0.6, xy_pca[:, 0].max() + 0.6, 45)
    gy = np.linspace(xy_pca[:, 1].min() - 0.6, xy_pca[:, 1].max() + 0.6, 45)
    xx, yy = np.meshgrid(gx, gy)
    pca_inv_grid = data["pca"].inverse_transform(np.c_[xx.ravel(), yy.ravel()])

    kmeans_runs = {}
    inertias = []
    for k in range(2, 9):
        m = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(X)
        lbl = relabel(m.labels_, df)
        old_to_new = pd.Series(lbl).groupby(m.labels_).first().sort_index()
        centers_z = m.cluster_centers_
        centers_orig = data["scaler"].inverse_transform(centers_z)
        centers_pca = data["pca"].transform(centers_z)
        centers_list = []
        for old_idx in range(k):
            new_idx = int(old_to_new.loc[old_idx])
            centers_list.append({
                "cluster": new_idx,
                "Work": round(float(centers_orig[old_idx, 0]), 1),
                "Price": round(float(centers_orig[old_idx, 1]), 1),
                "Salary": round(float(centers_orig[old_idx, 2]), 1),
                "PC1": round(float(centers_pca[old_idx, 0]), 3),
                "PC2": round(float(centers_pca[old_idx, 1]), 3),
            })
        centers_list.sort(key=lambda c: c["cluster"])
        grid_pred = old_to_new.values[m.predict(pca_inv_grid)].reshape(xx.shape)

        run = _evaluate_run(df, X, z_df, lbl, ref_km4)
        run["inertia"] = round(float(m.inertia_), 2)
        run["n_iter"] = int(m.n_iter_)
        run["centers"] = centers_list
        run["pca_grid"] = {
            "x": [round(float(v), 3) for v in gx],
            "y": [round(float(v), 3) for v in gy],
            "z": [[int(v) for v in row] for row in grid_pred],
        }
        kmeans_runs[str(k)] = run
        inertias.append((k, float(m.inertia_)))

    elbow = []
    for i, (k, iner) in enumerate(inertias):
        drop = None if i == 0 else round((inertias[i - 1][1] - iner) / inertias[i - 1][1] * 100, 1)
        elbow.append({
            "k": k,
            "inertia": round(iner, 2),
            "drop_pct": drop,
            "silhouette": kmeans_runs[str(k)]["silhouette"],
        })

    # 3. DBSCAN (eps=0.4..1.2, min_samples=3..5)
    nn = NearestNeighbors(n_neighbors=4).fit(X)
    dist4, _ = nn.kneighbors(X)
    k_dist = np.sort(dist4[:, -1])
    idx_arr = np.arange(len(k_dist))
    chord = k_dist[0] + (k_dist[-1] - k_dist[0]) * idx_arr / idx_arr[-1]
    knee = float(k_dist[np.argmax(chord - k_dist)])

    dbscan_runs = {}
    eps_values = [round(float(e), 1) for e in np.arange(0.4, 1.21, 0.1)]
    for ms in [3, 4, 5]:
        dbscan_runs[str(ms)] = {}
        for eps in eps_values:
            db_model = DBSCAN(eps=eps, min_samples=ms).fit(X)
            lbl = relabel(db_model.labels_, df)
            core = np.zeros(len(X), dtype=bool)
            core[db_model.core_sample_indices_] = True
            graph = radius_neighbors_graph(X, eps).tocoo()
            edges = [
                [int(i), int(j)]
                for i, j in zip(graph.row, graph.col)
                if i < j and (core[i] or core[j])
            ]
            run = _evaluate_run(df, X, z_df, lbl, ref_km4)
            run["core"] = [bool(c) for c in core]
            run["edges"] = edges
            dbscan_runs[str(ms)][f"{eps:.1f}"] = run

    # Расстояние до 3-го соседа для каждого города (при min_samples=4)
    dist_3rd = [round(float(d), 2) for d in dist4[:, -1]]

    # Точки городов
    cities = []
    for i, city_id in enumerate(df.index):
        row = df.iloc[i]
        z_row = z_df.iloc[i]
        cities.append({
            "id": city_id,
            "name": data["names"][i],
            "Work": round(float(row["Work"]), 1),
            "Price": round(float(row["Price"]), 1),
            "Salary": round(float(row["Salary"]), 1),
            "Salary_to_Price": round(float(row["Salary"] / row["Price"]), 2),
            "z_Work": round(float(z_row["Work"]), 2),
            "z_Price": round(float(z_row["Price"]), 2),
            "z_Salary": round(float(z_row["Salary"]), 2),
            "PC1": round(float(xy_pca[i, 0]), 3),
            "PC2": round(float(xy_pca[i, 1]), 3),
            "dist_3rd": dist_3rd[i],
        })

    # Описательная статистика и корреляции
    desc = df.describe().T[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]].round(2)
    desc_rows = [
        {"feature": col, **{k: float(desc.loc[col, k]) for k in desc.columns}}
        for col in desc.index
    ]
    corr = df.corr().round(2)
    corr_matrix = [[float(corr.iloc[r, c]) for c in range(len(df.columns))] for r in range(len(df.columns))]

    dropped_rows = [
        {
            "name": idx.replace("_", " "),
            "Work": None if pd.isna(r["Work"]) else float(r["Work"]),
            "Price": None if pd.isna(r["Price"]) else float(r["Price"]),
            "Salary": None if pd.isna(r["Salary"]) else float(r["Salary"]),
        }
        for idx, r in data["dropped"].iterrows()
    ]

    return {
        "meta": {
            "total_raw": int(len(data["df_raw"])),
            "total_clean": int(len(df)),
            "n_features": int(df.shape[1]),
            "features": list(df.columns),
            "dropped": dropped_rows,
            "pca_var": data["pca_var"],
            "knee_eps": round(knee, 3),
            "k_dist": [round(float(v), 3) for v in k_dist],
            "defaults": {
                "ward": {"k": 4},
                "kmeans": {"k": 4},
                "dbscan": {"min_samples": 4, "eps": "0.8"},
            },
            "cluster_names": {
                "k4": CLUSTER_NAMES_K4,
                "dbscan": CLUSTER_NAMES_DBSCAN,
            },
        },
        "cities": cities,
        "data_stats": {
            "describe": desc_rows,
            "corr": corr_matrix,
        },
        "ward": {
            "heights": ward_heights,
            "runs": ward_runs,
        },
        "kmeans": {
            "elbow": elbow,
            "runs": kmeans_runs,
        },
        "dbscan": {
            "eps_values": [f"{e:.1f}" for e in eps_values],
            "min_samples_values": [3, 4, 5],
            "runs": dbscan_runs,
        },
    }
