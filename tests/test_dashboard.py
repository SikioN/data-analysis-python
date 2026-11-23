"""Проверка расчётного ядра и собранного HTML-дашборда ЛР4."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_dashboard import build_html
from dashboard_core import build_dashboard_payload

DASHBOARD_HTML = ROOT / "docs" / "index.html"


def test_core_matches_labs_1_to_3():
    payload = build_dashboard_payload()
    assert payload["meta"]["total_raw"] == 48
    assert payload["meta"]["total_clean"] == 46
    dropped_names = {d["name"] for d in payload["meta"]["dropped"]}
    assert dropped_names == {"Cairo", "Jakarta"}

    ward4 = payload["ward"]["runs"]["4"]
    assert ward4["n_clusters"] == 4
    assert ward4["silhouette"] == 0.355
    assert ward4["ari_km4"] == 0.838

    km4 = payload["kmeans"]["runs"]["4"]
    assert km4["n_clusters"] == 4
    assert km4["silhouette"] == 0.366
    assert km4["ari_km4"] == 1.0

    db = payload["dbscan"]["runs"]["4"]["0.8"]
    assert db["n_clusters"] == 2
    assert db["n_noise"] == 8
    assert db["silhouette"] == 0.512
    assert db["ari_km4"] == 0.743


def test_dashboard_html_built_and_clean():
    out = build_html()
    assert out == DASHBOARD_HTML
    html = out.read_text(encoding="utf-8")

    # Извлекаем встроенный JSON и проверяем валидность
    m = re.search(r"const PAYLOAD = (\{.*?\});\n", html, re.S)
    assert m is not None
    parsed = json.loads(m.group(1))
    assert len(parsed["cities"]) == 46

    # Проверяем заголовки: без точек в конце и без длинных тире
    headings = re.findall(r"<h[12][^>]*>(.*?)</h[12]>", html, re.S)
    assert headings
    for h in headings:
        clean = re.sub(r"<[^>]+>", "", h).strip()
        assert not clean.endswith("."), f"Точка в заголовке: {clean}"
        assert "—" not in clean, f"Длинное тире в заголовке: {clean}"

    # Проверяем видимую разметку до <script>: без длинных тире и интерпункта
    body_html = html.split("<script>")[0]
    visible_text = re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", body_html, flags=re.S))
    assert "—" not in visible_text
    assert "·" not in html
    assert "Анализ данных на Python" in visible_text
    assert "333652" in visible_text
    assert "Университет ИТМО" in body_html
    assert "<select" not in body_html
    for forbidden in ["(-9999)", "Согласие с базовым разбиением", "Отклонение от среднего в единицах std",
                      "Нумерация по возрастанию Salary"]:
        assert forbidden not in html, f"Лишнее пояснение: {forbidden}"
