"""Генерация статического интерактивного дашборда в docs/index.html (стиль ИТМО + SVG-графики)."""
import base64
import json
from pathlib import Path
from dashboard_core import build_dashboard_payload

ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "docs" / "index.html"
LOGO_PATH = ROOT / "docs" / "itmo_logo.png"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" href="data:,">
  <title>Кластерный анализ городов</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      --bg: #f4f4f2;
      --surface: #ffffff;
      --lime: #c9ff33;
      --lime-soft: #f2fbd9;
      --green: #166534;
      --ink: #111111;
      --ink-2: #262626;
      --muted: #5c5c5c;
      --line: #dddddd;
      --danger: #b91c1c;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Golos Text", "ALS Sirius", Arial, Helvetica, sans-serif;
      font-size: 16px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    .shell {
      max-width: 1280px;
      margin: 24px auto 44px;
      background: var(--surface);
      border: 1px solid var(--ink);
    }

    .ribbon {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 30px;
      background: var(--lime);
      border-bottom: 1px solid var(--ink);
    }

    .ribbon-label {
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 0.3px;
      color: var(--ink);
    }

    .tabs {
      display: inline-flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .tab-btn {
      border: 1px solid var(--ink);
      background: var(--surface);
      color: var(--ink);
      padding: 8px 16px;
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }

    .tab-btn:hover {
      background: var(--lime-soft);
    }

    .tab-btn.active {
      background: var(--ink);
      color: var(--lime);
    }

    .hero {
      padding: 32px 30px 26px;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(30px, 4vw, 46px);
      line-height: 1.04;
      font-weight: 400;
      letter-spacing: -1.6px;
      color: var(--ink);
    }

    .hero p {
      margin: 14px 0 0;
      max-width: 740px;
      font-size: 17px;
      color: var(--ink-2);
    }

    .kpi-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      border-top: 1px solid var(--ink);
      border-bottom: 1px solid var(--ink);
    }

    .kpi-cell {
      padding: 18px 26px;
      border-right: 1px solid var(--line);
    }

    .kpi-cell:last-child {
      border-right: 0;
    }

    .kpi-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--muted);
    }

    .kpi-value {
      margin-top: 6px;
      font-size: 32px;
      font-weight: 500;
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
      color: var(--ink);
    }

    .kpi-sub {
      margin-top: 4px;
      font-size: 13px;
      color: var(--muted);
    }

    .kpi-sub:empty {
      display: none;
    }

    .controls {
      background: var(--lime-soft);
      border-bottom: 1px solid var(--ink);
      padding: 18px 30px;
      display: flex;
      flex-wrap: wrap;
      align-items: flex-end;
      gap: 18px;
    }

    .control-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .control-label {
      font-size: 13px;
      font-weight: 600;
      color: var(--ink-2);
    }

    .segmented {
      display: inline-flex;
      border: 1px solid var(--ink);
      background: var(--surface);
      height: 40px;
    }

    .seg-btn {
      border: 0;
      border-right: 1px solid var(--ink);
      background: transparent;
      color: var(--ink);
      padding: 0 16px;
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }

    .seg-btn:last-child {
      border-right: 0;
    }

    .seg-btn:hover {
      background: var(--lime-soft);
    }

    .seg-btn.active {
      background: var(--lime);
    }

    /* Кастомный выпадающий список в стиле style.html */
    .dd {
      position: relative;
      min-width: 180px;
    }

    .dd-trigger {
      width: 100%;
      height: 40px;
      padding: 0 36px 0 13px;
      border: 1px solid var(--ink);
      background: var(--surface);
      color: var(--ink);
      font-family: inherit;
      font-size: 14px;
      font-weight: 500;
      text-align: left;
      cursor: pointer;
      display: flex;
      align-items: center;
      position: relative;
      transition: background 0.15s;
    }

    .dd-trigger:hover {
      background: #fafafa;
    }

    .dd-trigger::after {
      content: "";
      position: absolute;
      right: 12px;
      top: 50%;
      width: 8px;
      height: 8px;
      border-right: 1.8px solid var(--ink);
      border-bottom: 1.8px solid var(--ink);
      transform: translateY(-65%) rotate(45deg);
      transition: transform 0.18s ease;
    }

    .dd.open .dd-trigger {
      background: var(--lime);
    }

    .dd.open .dd-trigger::after {
      transform: translateY(-30%) rotate(-135deg);
    }

    .dd-menu {
      position: absolute;
      left: 0;
      right: 0;
      top: calc(100% - 1px);
      background: var(--surface);
      border: 1px solid var(--ink);
      z-index: 60;
      display: none;
      max-height: 260px;
      overflow-y: auto;
    }

    .dd.open .dd-menu {
      display: block;
      animation: panelIn 0.16s ease;
    }

    .dd-item {
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: var(--surface);
      color: var(--ink);
      padding: 10px 13px;
      font-family: inherit;
      font-size: 14px;
      font-weight: 500;
      text-align: left;
      cursor: pointer;
      display: block;
    }

    .dd-item:last-child {
      border-bottom: 0;
    }

    .dd-item:hover {
      background: var(--lime-soft);
    }

    .dd-item.selected {
      background: var(--lime);
      font-weight: 700;
    }

    input[type="range"] {
      -webkit-appearance: none;
      appearance: none;
      height: 4px;
      background: var(--ink);
      outline: none;
      width: 118px;
    }

    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      background: var(--lime);
      border: 1.5px solid var(--ink);
      cursor: pointer;
    }

    .range-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      height: 40px;
    }

    .range-val {
      font-variant-numeric: tabular-nums;
      font-weight: 700;
      min-width: 36px;
      background: var(--surface);
      border: 1px solid var(--ink);
      padding: 4px 8px;
      text-align: center;
      font-size: 14px;
    }

    .btn-reset {
      margin-left: auto;
      height: 40px;
      border: 1px solid var(--ink);
      background: var(--surface);
      color: var(--ink);
      padding: 0 16px;
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }

    .btn-reset:hover {
      background: var(--lime);
    }

    .workspace {
      padding: 26px 30px 30px;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 22px;
      align-items: start;
    }

    .grid-2.equal-row {
      align-items: stretch;
    }

    .col-stack {
      display: flex;
      flex-direction: column;
      gap: 22px;
      min-width: 0;
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--ink);
      padding: 20px 22px;
      min-width: 0;
    }

    .card-full {
      grid-column: 1 / -1;
    }

    .card-header {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
      padding-bottom: 12px;
      margin-bottom: 14px;
      border-bottom: 1px solid var(--line);
    }

    .card-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: var(--ink);
    }

    .card-note {
      font-size: 13px;
      color: var(--muted);
    }

    .card-note:empty {
      display: none;
    }

    .plot-box {
      width: 100%;
      height: 390px;
    }

    .svg-wrap {
      width: 100%;
      overflow: hidden;
    }

    .svg-wrap svg {
      display: block;
      width: 100%;
      height: auto;
    }

    @keyframes panelIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: none; }
    }

    @keyframes growY {
      from { transform: scaleY(0); }
      to { transform: scaleY(1); }
    }

    @keyframes growX {
      from { transform: scaleX(0); }
      to { transform: scaleX(1); }
    }

    @keyframes draw {
      to { stroke-dashoffset: 0; }
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes logoIn {
      from { opacity: 0; filter: blur(6px); transform: translateY(10px) scale(0.97); }
      to { opacity: 1; filter: blur(0); transform: none; }
    }

    .tab-panel {
      animation: panelIn 0.28s cubic-bezier(.22, .61, .36, 1) both;
    }

    .svg-bar {
      transform-box: fill-box;
      transform-origin: bottom;
      animation: growY 0.55s cubic-bezier(.22, .61, .36, 1) both;
    }

    .svg-hbar {
      transform-box: fill-box;
      transform-origin: left;
      animation: growX 0.55s cubic-bezier(.22, .61, .36, 1) both;
    }

    .svg-hbar-neg {
      transform-box: fill-box;
      transform-origin: right;
      animation: growX 0.55s cubic-bezier(.22, .61, .36, 1) both;
    }

    .svg-draw {
      stroke-dasharray: 1;
      stroke-dashoffset: 1;
      animation: draw 0.7s cubic-bezier(.22, .61, .36, 1) forwards;
    }

    .svg-fade {
      animation: fadeIn 0.45s ease both;
    }

    #svg-tooltip {
      position: fixed;
      pointer-events: none;
      z-index: 999;
      background: var(--surface);
      border: 1px solid var(--ink);
      padding: 8px 12px;
      font-size: 13px;
      line-height: 1.45;
      color: var(--ink);
      display: none;
      max-width: 260px;
    }

    .table-scroll {
      width: 100%;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14.5px;
      font-variant-numeric: tabular-nums;
    }

    th, td {
      text-align: left;
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }

    th {
      font-size: 13px;
      font-weight: 600;
      color: var(--muted);
      border-bottom: 1px solid var(--ink);
    }

    td.num, th.num {
      text-align: right;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      font-weight: 600;
      white-space: nowrap;
    }

    .dot {
      width: 10px;
      height: 10px;
      display: inline-block;
      border: 1px solid var(--ink);
    }

    .note-box {
      margin-top: 14px;
      padding: 14px 16px;
      background: var(--lime-soft);
      border: 1px solid var(--ink);
      font-size: 14.5px;
      color: var(--ink-2);
    }

    .note-box p {
      margin: 0 0 8px;
    }

    .note-box p:last-child {
      margin-bottom: 0;
    }

    .filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      margin-bottom: 14px;
    }

    .hidden {
      display: none !important;
    }

    .footer {
      border-top: 1px solid var(--ink);
      padding: 24px 30px;
      background: var(--surface);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }

    .footer-logo-wrap {
      display: flex;
      align-items: center;
      gap: 18px;
      flex-wrap: wrap;
    }

    .itmo-logo-full {
      height: 32px;
      width: auto;
      display: block;
      animation: logoIn 0.7s cubic-bezier(.2, .72, .2, 1) 0.15s both;
    }

    .footer-course {
      font-size: 15px;
      font-weight: 600;
      color: var(--ink);
      border-left: 1px solid var(--line);
      padding-left: 16px;
    }

    .footer-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 14px;
      font-size: 15px;
      color: var(--ink-2);
      font-variant-numeric: tabular-nums;
    }

    .footer-meta strong {
      color: var(--ink);
      font-weight: 600;
    }

    @media (max-width: 960px) {
      .shell { margin: 0; border-left: 0; border-right: 0; border-top: 0; }
      .kpi-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .kpi-cell { border-bottom: 1px solid var(--line); }
      .grid-2 { grid-template-columns: 1fr; }
    }

    @media (max-width: 640px) {
      .ribbon, .hero, .controls, .workspace, .footer { padding-left: 14px; padding-right: 14px; }
      .tabs { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .tab-btn { padding: 9px 6px; font-size: 13px; text-align: center; }
      .control-group { width: 100%; }
      .dd { width: 100%; min-width: 0; }
      .segmented { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .seg-btn { padding: 0 6px; font-size: 13px; }
      input[type="range"] { flex: 1; width: auto; }
      .btn-reset { width: 100%; margin-left: 0; }
      .kpi-cell { padding: 14px; }
      .kpi-value { font-size: 24px; }
      .card { padding: 14px; }
      .plot-box { height: 320px; }
      .footer-course { border-left: 0; padding-left: 0; }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation: none !important; transition: none !important; }
      .svg-draw { stroke-dashoffset: 0 !important; }
      .itmo-logo-full { opacity: 1 !important; filter: none !important; transform: none !important; }
    }

    @media print {
      *, *::before, *::after { animation: none !important; transition: none !important; }
      body { background: #ffffff; }
      .shell { margin: 0; border: 0; }
      .controls, .tabs { display: none !important; }
      .card { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div id="svg-tooltip"></div>

  <div class="shell">
    <header class="ribbon">
      <div class="ribbon-label">Анализ данных на Python</div>
      <nav class="tabs" aria-label="Разделы дашборда">
        <button class="tab-btn active" data-tab="clusters">Кластеры</button>
        <button class="tab-btn" data-tab="data">Данные</button>
        <button class="tab-btn" data-tab="compare">Сравнение и выводы</button>
      </nav>
    </header>

    <section class="hero">
      <h1>Кластерный анализ городов</h1>
      <p>Сравнение метода Уорда, k-means и DBSCAN на выборке Economics of Cities 1991 года.</p>
    </section>

    <section class="kpi-strip" aria-label="Ключевые показатели">
      <div class="kpi-cell">
        <div class="kpi-title">Городов в анализе</div>
        <div class="kpi-value" id="kpi-n">46 / 48</div>
        <div class="kpi-sub">без Каира и Джакарты</div>
      </div>
      <div class="kpi-cell">
        <div class="kpi-title">Кластеры</div>
        <div class="kpi-value" id="kpi-clusters">4</div>
        <div class="kpi-sub" id="kpi-noise"></div>
      </div>
      <div class="kpi-cell">
        <div class="kpi-title">Силуэт</div>
        <div class="kpi-value" id="kpi-sil">0.366</div>
        <div class="kpi-sub" id="kpi-sil-sub"></div>
      </div>
      <div class="kpi-cell">
        <div class="kpi-title">ARI с k-means</div>
        <div class="kpi-value" id="kpi-ari">1.000</div>
      </div>
    </section>

    <section class="controls" aria-label="Параметры отображения">
      <div class="control-group">
        <span class="control-label">Алгоритм</span>
        <div class="segmented" id="algo-switch">
          <button class="seg-btn" data-algo="ward">Уорд</button>
          <button class="seg-btn active" data-algo="kmeans">k-means</button>
          <button class="seg-btn" data-algo="dbscan">DBSCAN</button>
        </div>
      </div>

      <div class="control-group" id="param-k-group">
        <span class="control-label">Число кластеров k</span>
        <div class="range-wrap">
          <input type="range" id="param-k" min="2" max="8" step="1" value="4">
          <span class="range-val" id="param-k-val">4</span>
        </div>
      </div>

      <div class="control-group hidden" id="param-eps-group">
        <span class="control-label">Радиус eps</span>
        <div class="range-wrap">
          <input type="range" id="param-eps" min="0.4" max="1.2" step="0.1" value="0.8">
          <span class="range-val" id="param-eps-val">0.8</span>
        </div>
      </div>

      <div class="control-group hidden" id="param-ms-group">
        <span class="control-label">min_samples</span>
        <div class="dd" id="dd-ms" style="min-width:110px"></div>
      </div>

      <div class="control-group">
        <span class="control-label">Пространство</span>
        <div class="dd" id="dd-axes" style="min-width:225px"></div>
      </div>

      <div class="control-group">
        <span class="control-label">Кластер</span>
        <div class="dd" id="dd-cluster" style="min-width:155px"></div>
      </div>

      <div class="control-group">
        <span class="control-label">Подписи</span>
        <div class="dd" id="dd-labels" style="min-width:148px"></div>
      </div>

      <button class="btn-reset" id="btn-reset">Сбросить</button>
    </section>

    <div class="workspace">
      <main id="tab-clusters" class="grid-2 tab-panel">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Пространство признаков</h2>
            <span class="card-note" id="scatter-badge"></span>
          </div>
          <div id="plot-scatter" class="plot-box"></div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title" id="tuning-title">Выбор параметров</h2>
            <span class="card-note" id="tuning-note"></span>
          </div>
          <div id="svg-tuning" class="svg-wrap"></div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Профили в z-оценках</h2>
          </div>
          <div id="svg-heatmap" class="svg-wrap"></div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Покупательная способность и размеры</h2>
            <span class="card-note">Salary / Price</span>
          </div>
          <div id="svg-power" class="svg-wrap"></div>
        </div>

        <div class="card card-full">
          <div class="card-header">
            <h2 class="card-title">Состав кластеров</h2>
          </div>
          <div id="profiles-table-wrap" class="table-scroll"></div>
          <div class="note-box" id="cluster-interpretation"></div>
        </div>
      </main>

      <main id="tab-data" class="grid-2 tab-panel hidden">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Распределения по кластерам</h2>
          </div>
          <div class="filter-row">
            <span class="control-label">Признак</span>
            <div class="dd" id="dd-dist-feat" style="min-width:190px"></div>
          </div>
          <div id="svg-dist" class="svg-wrap"></div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Корреляция признаков</h2>
          </div>
          <div id="svg-corr" class="svg-wrap"></div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Описательная статистика</h2>
          </div>
          <div id="describe-table-wrap" class="table-scroll"></div>
          <div class="note-box">
            <p>Стандартное отклонение Work составляет 174.3 часа, у Price и Salary 21–25 пунктов, поэтому перед расчётом расстояний применена стандартизация.</p>
            <p>У Каира и Джакарты отсутствуют 2 признака из 3, оба города исключены из выборки.</p>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Фильтр городов</h2>
            <span class="card-note" id="cities-count-note"></span>
          </div>
          <div class="filter-row">
            <span class="control-label">Мин. Salary</span>
            <input type="range" id="min-salary" min="0" max="100" step="5" value="0">
            <span class="range-val" id="min-salary-val">0</span>
            <span class="control-label">Макс. Work</span>
            <input type="range" id="max-work" min="1600" max="2400" step="50" value="2400">
            <span class="range-val" id="max-work-val">2400</span>
          </div>
          <div id="cities-table-wrap" class="table-scroll" style="max-height: 300px; overflow-y: auto;"></div>
        </div>
      </main>

      <main id="tab-compare" class="grid-2 tab-panel hidden">
        <div class="card card-full">
          <div class="card-header">
            <h2 class="card-title">Сравнительная таблица алгоритмов</h2>
          </div>
          <div id="compare-table-wrap" class="table-scroll"></div>
        </div>

        <div class="col-stack">
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">Матрица переходов</h2>
            </div>
            <div class="filter-row">
              <div class="dd" id="dd-cmp-a" style="min-width:155px"></div>
              <span class="control-label">и</span>
              <div class="dd" id="dd-cmp-b" style="min-width:155px"></div>
            </div>
            <div id="svg-crosstab" class="svg-wrap"></div>
          </div>

          <div class="card">
            <div class="card-header">
              <h2 class="card-title" id="diff-cities-title">Расхождения между методами</h2>
              <span class="card-note" id="diff-cities-note"></span>
            </div>
            <div id="diff-cities-wrap" class="table-scroll"></div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Силуэт по объектам</h2>
            <span class="card-note" id="sil-samples-note"></span>
          </div>
          <div id="svg-sil-samples" class="svg-wrap"></div>
        </div>

        <div class="card card-full">
          <div class="card-header">
            <h2 class="card-title">Итоговые выводы</h2>
          </div>
          <div class="note-box">
            <p><strong>Основной алгоритм: k-means при k = 4 и n_init = 20.</strong> Силуэт равен 0.366 против 0.355 у Уорда, отрицательный силуэт остаётся только у Тель-Авива (-0.029) против трёх городов у Уорда. При 20 запусках глобальный минимум воспроизводится в 90% случаев.</p>
            <p><strong>Метод Уорда при k = 4</strong> подтверждает общую структуру с ARI = 0.838, но из-за жадных ранних слияний относит 4 города с умеренным рабочим годом в группу с максимальной нагрузкой.</p>
            <p><strong>DBSCAN при eps = 0.8 и min_samples = 4</strong> объединяет небогатые города в один кластер, а 6 самых дорогих городов и 2 азиатских мегаполиса (Гонконг и Тайбэй) выделяет в шум, 17.4% выборки. Силуэт 0.512 выше за счёт исключения шума, поэтому метод полезен для поиска нетипичных городов, но уступает k-means в типологии.</p>
          </div>
        </div>
      </main>
    </div>

    <footer class="footer">
      <div class="footer-logo-wrap">
        <img class="itmo-logo-full" src="__ITMO_LOGO_URI__" alt="Университет ИТМО">
        <div class="footer-course">Анализ данных на Python</div>
      </div>
      <div class="footer-meta">
        <strong>Муравья Никита</strong>
        <span>ИСУ: 333652</span>
      </div>
    </footer>
  </div>

  <script>
    const PAYLOAD = __PAYLOAD_JSON__;

    /* Комплементарная зелёно-графитовая палитра в тонах style.html (#c9ff33 + #111111) */
    const PALETTE = ["#111111", "#7e8a78", "#84cc16", "#166534", "#4d7c0f", "#52525b", "#3f6212", "#14532d"];
    const NOISE_COLOR = "#a3a3a3";
    const PLOT_CFG = { displayModeBar: false, responsive: true };
    const BASE_LAYOUT = {
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      font: { family: '"Golos Text", Arial, sans-serif', size: 13, color: "#111111" },
      margin: { l: 56, r: 20, t: 24, b: 46 },
    };

    const state = {
      tab: "clusters",
      algo: "kmeans",
      k: 4,
      eps: "0.8",
      ms: "4",
      axes: "3d",
      clusterFilter: "all",
      labelMode: "focus",
      distFeature: "Work",
      minSalary: 0,
      maxWork: 2400,
      cmpA: "ward",
      cmpB: "kmeans",
    };

    /* Кастомный выпадающий список */
    function mountDropdown(id, options, value, onChange) {
      const root = document.getElementById(id);
      const current = options.find(o => String(o.value) === String(value)) || options[0];
      root.innerHTML = `
        <button type="button" class="dd-trigger" aria-expanded="false">${current.label}</button>
        <div class="dd-menu" role="listbox">
          ${options.map(o => `<button type="button" class="dd-item ${String(o.value) === String(current.value) ? "selected" : ""}" data-val="${o.value}">${o.label}</button>`).join("")}
        </div>
      `;
      const trigger = root.querySelector(".dd-trigger");
      trigger.addEventListener("click", e => {
        e.stopPropagation();
        const wasOpen = root.classList.contains("open");
        document.querySelectorAll(".dd.open").forEach(d => d.classList.remove("open"));
        if (!wasOpen) {
          root.classList.add("open");
          trigger.setAttribute("aria-expanded", "true");
        }
      });
      root.querySelectorAll(".dd-item").forEach(item => {
        item.addEventListener("click", e => {
          e.stopPropagation();
          root.classList.remove("open");
          onChange(item.dataset.val);
        });
      });
    }

    document.addEventListener("click", () => {
      document.querySelectorAll(".dd.open").forEach(d => d.classList.remove("open"));
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") {
        document.querySelectorAll(".dd.open").forEach(d => d.classList.remove("open"));
      }
    });

    const tip = document.getElementById("svg-tooltip");
    function bindSvgTooltips(container) {
      container.querySelectorAll("[data-tip]").forEach(el => {
        el.addEventListener("mouseenter", () => {
          tip.innerHTML = el.dataset.tip;
          tip.style.display = "block";
        });
        el.addEventListener("mousemove", e => {
          tip.style.left = Math.min(window.innerWidth - 265, e.clientX + 12) + "px";
          tip.style.top = (e.clientY + 14) + "px";
        });
        el.addEventListener("mouseleave", () => {
          tip.style.display = "none";
        });
      });
    }

    function colorFor(cl) {
      return cl === -1 ? NOISE_COLOR : PALETTE[cl % PALETTE.length];
    }

    function lerpColor(c1, c2, t) {
      const a = parseInt(c1.slice(1), 16), b = parseInt(c2.slice(1), 16);
      const r = Math.round(((a >> 16) & 255) + (((b >> 16) & 255) - ((a >> 16) & 255)) * t);
      const g = Math.round(((a >> 8) & 255) + (((b >> 8) & 255) - ((a >> 8) & 255)) * t);
      const bl = Math.round((a & 255) + ((b & 255) - (a & 255)) * t);
      return `rgb(${r},${g},${bl})`;
    }

    /* Графитово-лаймовая шкала для тепловых карт в тон style.html */
    function divergingColor(v, maxAbs) {
      const t = Math.max(-1, Math.min(1, v / maxAbs));
      if (t >= 0) {
        return t < 0.55 ? lerpColor("#f5f5f5", "#c9ff33", t / 0.55) : lerpColor("#c9ff33", "#166534", (t - 0.55) / 0.45);
      }
      return lerpColor("#f5f5f5", "#27272a", -t);
    }

    function textOnDiverging(v, maxAbs) {
      const t = v / maxAbs;
      if (t < -0.45 || t > 0.72) return "#ffffff";
      return "#111111";
    }

    function clusterTitle(algo, kParam, cl) {
      if (cl === -1) return "Шум";
      if (algo === "dbscan" && PAYLOAD.meta.cluster_names.dbscan[String(cl)] && state.eps === "0.8" && state.ms === "4") {
        return `Кластер ${cl}: ${PAYLOAD.meta.cluster_names.dbscan[String(cl)]}`;
      }
      if ((algo === "ward" || algo === "kmeans") && Number(kParam) === 4) {
        return `Кластер ${cl}: ${PAYLOAD.meta.cluster_names.k4[String(cl)]}`;
      }
      return `Кластер ${cl}`;
    }

    function getActiveRun() {
      if (state.algo === "ward") return PAYLOAD.ward.runs[String(state.k)];
      if (state.algo === "kmeans") return PAYLOAD.kmeans.runs[String(state.k)];
      return PAYLOAD.dbscan.runs[state.ms][state.eps];
    }

    function updateControlsVisibility() {
      const isDb = state.algo === "dbscan";
      document.getElementById("param-k-group").classList.toggle("hidden", isDb);
      document.getElementById("param-eps-group").classList.toggle("hidden", !isDb);
      document.getElementById("param-ms-group").classList.toggle("hidden", !isDb);

      document.querySelectorAll("#algo-switch .seg-btn").forEach(b => {
        b.classList.toggle("active", b.dataset.algo === state.algo);
      });
    }

    function renderDropdowns(run) {
      mountDropdown("dd-ms", [
        { value: "3", label: "3" },
        { value: "4", label: "4" },
        { value: "5", label: "5" },
      ], state.ms, v => { state.ms = v; renderAll(); });

      mountDropdown("dd-axes", [
        { value: "3d", label: "3D: Work × Price × Salary" },
        { value: "pca", label: "2D: PC1 и PC2" },
        { value: "price_salary", label: "2D: Price и Salary" },
        { value: "work_salary", label: "2D: Work и Salary" },
      ], state.axes, v => { state.axes = v; renderAll(); });

      const unique = [...new Set(run.labels)].sort((a, b) => a - b);
      if (state.clusterFilter !== "all" && !unique.map(String).includes(state.clusterFilter)) {
        state.clusterFilter = "all";
      }
      mountDropdown("dd-cluster", [
        { value: "all", label: "Все группы" },
        ...unique.map(c => ({ value: String(c), label: c === -1 ? "Шум" : `Кластер ${c}` })),
      ], state.clusterFilter, v => { state.clusterFilter = v; renderAll(); });

      mountDropdown("dd-labels", [
        { value: "focus", label: "При фокусе" },
        { value: "all", label: "Все города" },
        { value: "none", label: "Скрыть" },
      ], state.labelMode, v => { state.labelMode = v; renderAll(); });

      mountDropdown("dd-dist-feat", [
        { value: "Work", label: "Work, ч/год" },
        { value: "Price", label: "Price" },
        { value: "Salary", label: "Salary" },
        { value: "Salary_to_Price", label: "Salary / Price" },
      ], state.distFeature, v => { state.distFeature = v; renderAll(); });

      const cmpOpts = [
        { value: "ward", label: "Уорд, k = 4" },
        { value: "kmeans", label: "k-means, k = 4" },
        { value: "dbscan", label: "DBSCAN, eps = 0.8" },
      ];
      mountDropdown("dd-cmp-a", cmpOpts, state.cmpA, v => { state.cmpA = v; renderAll(); });
      mountDropdown("dd-cmp-b", cmpOpts, state.cmpB, v => { state.cmpB = v; renderAll(); });
    }

    function renderKPIs(run) {
      document.getElementById("kpi-clusters").textContent = run.n_clusters;
      document.getElementById("kpi-noise").textContent =
        run.n_noise > 0 ? `шум: ${run.n_noise}, ${run.noise_pct}%` : "";
      document.getElementById("kpi-sil").textContent = run.silhouette !== null ? run.silhouette.toFixed(3) : "н/д";
      document.getElementById("kpi-sil-sub").textContent = run.n_noise > 0 ? "без учёта шума" : "";
      document.getElementById("kpi-ari").textContent = run.ari_km4.toFixed(3);
    }

    function shouldShowLabels(cl) {
      if (state.labelMode === "all") return true;
      if (state.labelMode === "none") return false;
      return state.clusterFilter !== "all" && state.clusterFilter === String(cl);
    }

    function cityHover(c, s) {
      return `<b>${c.name}</b><br>Work: ${c.Work} ч<br>Price: ${c.Price}<br>Salary: ${c.Salary}<br>Salary/Price: ${c.Salary_to_Price}<br>Силуэт: ${s === null ? "шум" : s}`;
    }

    function renderScatter(run) {
      const badge = document.getElementById("scatter-badge");
      const unique = [...new Set(run.labels)].sort((a, b) => a - b);

      if (state.axes === "3d") {
        badge.textContent = "";
        const traces = [];

        unique.filter(cl => cl !== -1).forEach(cl => {
          const idx = run.labels.map((l, i) => (l === cl ? i : -1)).filter(i => i >= 0);
          if (idx.length >= 4) {
            const focused = state.clusterFilter === "all" || state.clusterFilter === String(cl);
            traces.push({
              type: "mesh3d",
              x: idx.map(i => PAYLOAD.cities[i].Work),
              y: idx.map(i => PAYLOAD.cities[i].Price),
              z: idx.map(i => PAYLOAD.cities[i].Salary),
              alphahull: 0,
              color: colorFor(cl),
              opacity: focused ? 0.14 : 0.03,
              hoverinfo: "skip",
              showlegend: false,
            });
          }
        });

        if (state.algo === "dbscan" && run.edges && run.edges.length > 0) {
          const ex = [], ey = [], ez = [];
          run.edges.forEach(([i, j]) => {
            ex.push(PAYLOAD.cities[i].Work, PAYLOAD.cities[j].Work, null);
            ey.push(PAYLOAD.cities[i].Price, PAYLOAD.cities[j].Price, null);
            ez.push(PAYLOAD.cities[i].Salary, PAYLOAD.cities[j].Salary, null);
          });
          traces.push({
            type: "scatter3d",
            mode: "lines",
            name: "ε-связи",
            x: ex, y: ey, z: ez,
            line: { color: "rgba(17, 17, 17, 0.32)", width: 2 },
            hoverinfo: "skip",
          });
        }

        unique.forEach(cl => {
          const idx = run.labels.map((l, i) => (l === cl ? i : -1)).filter(i => i >= 0);
          const focused = state.clusterFilter === "all" || state.clusterFilter === String(cl);
          const showTxt = shouldShowLabels(cl);
          traces.push({
            type: "scatter3d",
            mode: showTxt ? "markers+text" : "markers",
            name: cl === -1 ? "Шум" : `Кластер ${cl}`,
            x: idx.map(i => PAYLOAD.cities[i].Work),
            y: idx.map(i => PAYLOAD.cities[i].Price),
            z: idx.map(i => PAYLOAD.cities[i].Salary),
            text: idx.map(i => PAYLOAD.cities[i].name),
            textposition: "top center",
            textfont: { size: 10, color: "#111111" },
            hovertext: idx.map(i => cityHover(PAYLOAD.cities[i], run.sil_samples[i])),
            hoverinfo: "text",
            marker: {
              size: cl === -1 ? 5 : 6.5,
              symbol: cl === -1 ? "x" : "circle",
              color: colorFor(cl),
              opacity: focused ? 0.96 : 0.16,
              line: { color: "#111111", width: cl === -1 ? 0 : 0.8 },
            },
          });
        });

        if (state.algo === "kmeans" && run.centers) {
          traces.push({
            type: "scatter3d",
            mode: "markers",
            name: "Центроиды",
            x: run.centers.map(c => c.Work),
            y: run.centers.map(c => c.Price),
            z: run.centers.map(c => c.Salary),
            hovertext: run.centers.map(c => `<b>Центроид ${c.cluster}</b><br>Work: ${c.Work} ч<br>Price: ${c.Price}<br>Salary: ${c.Salary}`),
            hoverinfo: "text",
            marker: {
              size: 9,
              symbol: "diamond",
              color: "#c9ff33",
              line: { color: "#111111", width: 2 },
            },
          });
        }

        Plotly.react("plot-scatter", traces, {
          ...BASE_LAYOUT,
          margin: { l: 0, r: 0, t: 8, b: 0 },
          scene: {
            xaxis: { title: "Work, ч", gridcolor: "#dddddd", backgroundcolor: "#ffffff" },
            yaxis: { title: "Price", gridcolor: "#dddddd", backgroundcolor: "#ffffff" },
            zaxis: { title: "Salary", gridcolor: "#dddddd", backgroundcolor: "#ffffff" },
            camera: { eye: { x: 1.55, y: 1.45, z: 1.15 } },
          },
          legend: { orientation: "h", y: 1.05, x: 0, font: { size: 11 }, itemwidth: 24 },
        }, PLOT_CFG);
        return;
      }

      badge.textContent = "";
      const axisMap = {
        price_salary: { x: "Price", y: "Salary", xl: "Индекс цен", yl: "Индекс зарплаты" },
        work_salary: { x: "Work", y: "Salary", xl: "Рабочих часов в год", yl: "Индекс зарплаты" },
        pca: { x: "PC1", y: "PC2", xl: "PC1", yl: "PC2" },
      }[state.axes];

      const traces = [];
      if (state.axes === "pca" && state.algo === "kmeans" && run.pca_grid) {
        const kCount = run.n_clusters;
        const scale = Array.from({ length: kCount }, (_, i) => {
          const c = PALETTE[i % PALETTE.length];
          return [[i / kCount, c], [(i + 1) / kCount, c]];
        }).flat();
        traces.push({
          type: "heatmap",
          x: run.pca_grid.x,
          y: run.pca_grid.y,
          z: run.pca_grid.z,
          colorscale: scale,
          zmin: -0.5,
          zmax: kCount - 0.5,
          opacity: 0.13,
          showscale: false,
          hoverinfo: "skip",
        });
      } else if (state.algo === "dbscan" && run.edges) {
        const ex = [], ey = [];
        run.edges.forEach(([i, j]) => {
          ex.push(PAYLOAD.cities[i][axisMap.x], PAYLOAD.cities[j][axisMap.x], null);
          ey.push(PAYLOAD.cities[i][axisMap.y], PAYLOAD.cities[j][axisMap.y], null);
        });
        traces.push({
          type: "scatter",
          mode: "lines",
          name: "ε-связи",
          x: ex, y: ey,
          line: { color: "rgba(17, 17, 17, 0.3)", width: 1.2 },
          hoverinfo: "skip",
        });
      }

      unique.forEach(cl => {
        const idx = run.labels.map((l, i) => (l === cl ? i : -1)).filter(i => i >= 0);
        const focused = state.clusterFilter === "all" || state.clusterFilter === String(cl);
        const showTxt = shouldShowLabels(cl);
        traces.push({
          type: "scatter",
          mode: showTxt ? "markers+text" : "markers",
          name: cl === -1 ? "Шум" : `Кластер ${cl}`,
          x: idx.map(i => PAYLOAD.cities[i][axisMap.x]),
          y: idx.map(i => PAYLOAD.cities[i][axisMap.y]),
          text: idx.map(i => PAYLOAD.cities[i].name),
          textposition: "top center",
          textfont: { size: 10.5, color: "#111111" },
          hovertext: idx.map(i => cityHover(PAYLOAD.cities[i], run.sil_samples[i])),
          hoverinfo: "text",
          marker: {
            size: cl === -1 ? 9 : 11,
            symbol: cl === -1 ? "x" : "circle",
            color: colorFor(cl),
            opacity: focused ? 0.96 : 0.16,
            line: { color: "#111111", width: cl === -1 ? 0 : 1 },
          },
        });
      });

      if (state.algo === "kmeans" && run.centers) {
        traces.push({
          type: "scatter",
          mode: "markers",
          name: "Центроиды",
          x: run.centers.map(c => c[axisMap.x]),
          y: run.centers.map(c => c[axisMap.y]),
          hovertext: run.centers.map(c => `<b>Центроид ${c.cluster}</b><br>Work: ${c.Work} ч<br>Price: ${c.Price}<br>Salary: ${c.Salary}`),
          hoverinfo: "text",
          marker: {
            size: 14,
            symbol: "diamond",
            color: "#c9ff33",
            line: { color: "#111111", width: 1.6 },
          },
        });
      }

      Plotly.react("plot-scatter", traces, {
        ...BASE_LAYOUT,
        margin: { l: 56, r: 22, t: 32, b: 46 },
        xaxis: { title: axisMap.xl, gridcolor: "#dddddd", zeroline: false },
        yaxis: { title: axisMap.yl, gridcolor: "#dddddd", zeroline: false, automargin: true },
        legend: { orientation: "h", y: 1.13, x: 0 },
      }, PLOT_CFG);
    }

    function renderTuningSvg() {
      const title = document.getElementById("tuning-title");
      const note = document.getElementById("tuning-note");
      const wrap = document.getElementById("svg-tuning");
      const W = 560, H = 350, pad = { l: 50, r: 46, t: 30, b: 46 };
      const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;

      if (state.algo === "ward") {
        title.textContent = "Высоты слияния";
        note.textContent = `k = ${state.k}`;
        const rows = PAYLOAD.ward.heights;
        const maxY = 13.5;
        const sx = k => pad.l + ((k - 1) / 9) * pw;
        const sy = v => pad.t + ph - (v / maxY) * ph;

        let grid = "";
        for (let v = 0; v <= 12; v += 3) {
          const y = sy(v);
          grid += `<line x1="${pad.l}" y1="${y}" x2="${W - pad.r}" y2="${y}" stroke="#e5e5e5" stroke-width="1"/>
                   <text x="${pad.l - 9}" y="${y + 4}" text-anchor="end" font-size="12.5" fill="#5c5c5c">${v}</text>`;
        }
        const bars = rows.filter(r => r.jump !== null).map((r, i) => {
          const x = sx(r.k) - 11, y = sy(r.jump), bh = sy(0) - y;
          return `<rect class="svg-bar" style="animation-delay:${i * 35}ms" x="${x}" y="${y}" width="22" height="${bh}" fill="#c9ff33" stroke="#111111" stroke-width="1" data-tip="<b>k = ${r.k}</b><br>Высота: ${r.height}<br>Скачок: ${r.jump}"/>`;
        }).join("");
        const linePath = rows.map((r, i) => `${i === 0 ? "M" : "L"}${sx(r.k).toFixed(1)},${sy(r.height).toFixed(1)}`).join(" ");
        const pts = rows.map(r => `<circle cx="${sx(r.k)}" cy="${sy(r.height)}" r="4.5" fill="#111111" data-tip="<b>k = ${r.k}</b><br>Высота: ${r.height}"/>`).join("");
        const xTicks = rows.map(r => `<text x="${sx(r.k)}" y="${H - 20}" text-anchor="middle" font-size="12.5" fill="#5c5c5c">${r.k}</text>`).join("");
        const kx = sx(state.k);

        wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}">
          ${grid}
          <line x1="${pad.l}" y1="${sy(0)}" x2="${W - pad.r}" y2="${sy(0)}" stroke="#111111" stroke-width="1.2"/>
          ${bars}
          <path class="svg-draw" pathLength="1" d="${linePath}" fill="none" stroke="#111111" stroke-width="2.4"/>
          ${pts}
          <line x1="${kx}" y1="${pad.t}" x2="${kx}" y2="${sy(0)}" stroke="#166534" stroke-width="1.8" stroke-dasharray="5 4"/>
          <text x="${kx + 6}" y="${pad.t + 14}" font-size="12.5" font-weight="600" fill="#166534">k = ${state.k}</text>
          ${xTicks}
          <text x="${pad.l + pw / 2}" y="${H - 2}" text-anchor="middle" font-size="12.5" fill="#5c5c5c">Число кластеров k</text>
          <rect x="${pad.l}" y="6" width="11" height="11" fill="#c9ff33" stroke="#111111"/>
          <text x="${pad.l + 17}" y="16" font-size="12.5" fill="#111111">Скачок</text>
          <line x1="${pad.l + 86}" y1="11" x2="${pad.l + 106}" y2="11" stroke="#111111" stroke-width="2.4"/>
          <text x="${pad.l + 112}" y="16" font-size="12.5" fill="#111111">Высота слияния</text>
        </svg>`;
      } else if (state.algo === "kmeans") {
        title.textContent = "Метод локтя и силуэт";
        note.textContent = `k = ${state.k}`;
        const rows = PAYLOAD.kmeans.elbow;
        const sx = k => pad.l + ((k - 2) / 6) * pw;
        const syJ = v => pad.t + ph - ((v - 10) / 56) * ph;
        const syS = v => pad.t + ph - ((v - 0.25) / 0.30) * ph;

        let grid = "";
        [15, 30, 45, 60].forEach(v => {
          const y = syJ(v);
          grid += `<line x1="${pad.l}" y1="${y}" x2="${W - pad.r}" y2="${y}" stroke="#e5e5e5" stroke-width="1"/>
                   <text x="${pad.l - 9}" y="${y + 4}" text-anchor="end" font-size="12.5" fill="#111111">${v}</text>`;
        });
        [0.3, 0.4, 0.5].forEach(v => {
          const y = syS(v);
          grid += `<text x="${W - pad.r + 9}" y="${y + 4}" text-anchor="start" font-size="12.5" fill="#166534">${v.toFixed(1)}</text>`;
        });
        const pathJ = rows.map((r, i) => `${i === 0 ? "M" : "L"}${sx(r.k).toFixed(1)},${syJ(r.inertia).toFixed(1)}`).join(" ");
        const pathS = rows.map((r, i) => `${i === 0 ? "M" : "L"}${sx(r.k).toFixed(1)},${syS(r.silhouette).toFixed(1)}`).join(" ");
        const pts = rows.map(r => `
          <circle cx="${sx(r.k)}" cy="${syJ(r.inertia)}" r="5" fill="#111111" data-tip="<b>k = ${r.k}</b><br>Инерция J: ${r.inertia}<br>Падение: ${r.drop_pct ?? 0}%"/>
          <circle cx="${sx(r.k)}" cy="${syS(r.silhouette)}" r="5" fill="#166534" data-tip="<b>k = ${r.k}</b><br>Силуэт: ${r.silhouette}"/>
        `).join("");
        const xTicks = rows.map(r => `<text x="${sx(r.k)}" y="${H - 20}" text-anchor="middle" font-size="12.5" fill="#5c5c5c">${r.k}</text>`).join("");
        const kx = sx(state.k);

        wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}">
          ${grid}
          <line x1="${pad.l}" y1="${pad.t + ph}" x2="${W - pad.r}" y2="${pad.t + ph}" stroke="#111111" stroke-width="1.2"/>
          <path class="svg-draw" pathLength="1" d="${pathJ}" fill="none" stroke="#111111" stroke-width="2.5"/>
          <path class="svg-draw" style="animation-delay:0.15s" pathLength="1" d="${pathS}" fill="none" stroke="#166534" stroke-width="2.5"/>
          ${pts}
          <line x1="${kx}" y1="${pad.t}" x2="${kx}" y2="${pad.t + ph}" stroke="#111111" stroke-width="1.5" stroke-dasharray="5 4"/>
          <text x="${kx + 6}" y="${pad.t + 14}" font-size="12.5" font-weight="600" fill="#111111">k = ${state.k}</text>
          ${xTicks}
          <text x="${pad.l + pw / 2}" y="${H - 2}" text-anchor="middle" font-size="12.5" fill="#5c5c5c">Число кластеров k</text>
          <line x1="${pad.l}" y1="11" x2="${pad.l + 20}" y2="11" stroke="#111111" stroke-width="2.5"/>
          <text x="${pad.l + 26}" y="16" font-size="12.5" fill="#111111">Инерция J</text>
          <line x1="${pad.l + 115}" y1="11" x2="${pad.l + 135}" y2="11" stroke="#166534" stroke-width="2.5"/>
          <text x="${pad.l + 141}" y="16" font-size="12.5" fill="#166534">Силуэт</text>
        </svg>`;
      } else {
        title.textContent = "График 3-расстояний";
        note.textContent = `колено ${PAYLOAD.meta.knee_eps}, eps = ${state.eps}`;
        const kd = PAYLOAD.meta.k_dist;
        const maxY = Math.max(...kd) * 1.08;
        const sx = i => pad.l + (i / (kd.length - 1)) * pw;
        const sy = v => pad.t + ph - (v / maxY) * ph;

        let grid = "";
        [0, 0.5, 1.0, 1.5, 2.0].forEach(v => {
          if (v <= maxY) {
            const y = sy(v);
            grid += `<line x1="${pad.l}" y1="${y}" x2="${W - pad.r}" y2="${y}" stroke="#e5e5e5" stroke-width="1"/>
                     <text x="${pad.l - 9}" y="${y + 4}" text-anchor="end" font-size="12.5" fill="#5c5c5c">${v.toFixed(1)}</text>`;
          }
        });
        const path = kd.map((v, i) => `${i === 0 ? "M" : "L"}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
        const pts = kd.map((v, i) => `<circle cx="${sx(i)}" cy="${sy(v)}" r="3.5" fill="#166534" data-tip="Город #${i + 1}<br>3-расстояние: ${v}"/>`).join("");
        const ey = sy(Number(state.eps));

        wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}">
          ${grid}
          <line x1="${pad.l}" y1="${pad.t + ph}" x2="${W - pad.r}" y2="${pad.t + ph}" stroke="#111111" stroke-width="1.2"/>
          <path class="svg-draw" pathLength="1" d="${path}" fill="none" stroke="#111111" stroke-width="2.4"/>
          ${pts}
          <line x1="${pad.l}" y1="${ey}" x2="${W - pad.r}" y2="${ey}" stroke="#166534" stroke-width="1.8" stroke-dasharray="5 4"/>
          <text x="${pad.l + 6}" y="${ey - 7}" font-size="12.5" font-weight="600" fill="#166534">eps = ${state.eps}</text>
          <text x="${pad.l + pw / 2}" y="${H - 6}" text-anchor="middle" font-size="12.5" fill="#5c5c5c">Города по возрастанию расстояния</text>
        </svg>`;
      }
      bindSvgTooltips(wrap);
    }

    function renderHeatmapSvg(run) {
      const wrap = document.getElementById("svg-heatmap");
      const prof = run.profiles;
      const cols = ["Work", "Price", "Salary"];
      const W = 540, rowH = 48, top = 36, left = 104, right = 16;
      const H = top + prof.length * rowH + 14;
      const colW = (W - left - right) / 3;

      let cells = "";
      cols.forEach((c, ci) => {
        cells += `<text x="${left + ci * colW + colW / 2}" y="22" text-anchor="middle" font-size="13.5" font-weight="600" fill="#111111">${c}</text>`;
      });

      prof.forEach((p, ri) => {
        const y = top + ri * rowH;
        const lbl = p.cluster === -1 ? "Шум" : `Кластер ${p.cluster}`;
        cells += `<text x="${left - 12}" y="${y + rowH / 2 + 5}" text-anchor="end" font-size="13.5" fill="#111111">${lbl}</text>`;
        [p.z_Work, p.z_Price, p.z_Salary].forEach((v, ci) => {
          const x = left + ci * colW;
          const bg = divergingColor(v, 2.1);
          const fg = textOnDiverging(v, 2.1);
          cells += `<g class="svg-fade" style="animation-delay:${(ri * 3 + ci) * 28}ms" data-tip="<b>${lbl}</b><br>${cols[ci]}: ${v > 0 ? "+" : ""}${v.toFixed(2)}">
            <rect x="${x}" y="${y}" width="${colW}" height="${rowH}" fill="${bg}" stroke="#ffffff" stroke-width="2"/>
            <text x="${x + colW / 2}" y="${y + rowH / 2 + 5}" text-anchor="middle" font-size="14" font-weight="600" fill="${fg}">${v.toFixed(2)}</text>
          </g>`;
        });
      });

      wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${cells}</svg>`;
      bindSvgTooltips(wrap);
    }

    function renderPowerSvg(run) {
      const wrap = document.getElementById("svg-power");
      const prof = run.profiles;
      const W = 540, rowH = 48, top = 36, left = 104, right = 78;
      const H = top + prof.length * rowH + 14;
      const maxP = 0.85;
      const pw = W - left - right;

      let svg = `<text x="${left}" y="22" font-size="12.5" font-weight="600" fill="#5c5c5c">0.0</text>
                 <text x="${left + pw * 0.5 / maxP}" y="22" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5c5c5c">0.5</text>
                 <line x1="${left}" y1="${top - 4}" x2="${left}" y2="${H - 12}" stroke="#111111" stroke-width="1"/>
                 <line x1="${left + pw * 0.5 / maxP}" y1="${top - 4}" x2="${left + pw * 0.5 / maxP}" y2="${H - 12}" stroke="#e5e5e5" stroke-width="1"/>`;

      prof.forEach((p, ri) => {
        const y = top + ri * rowH;
        const lbl = p.cluster === -1 ? "Шум" : `Кластер ${p.cluster}`;
        const bw = Math.max(4, (p.Salary_to_Price / maxP) * pw);
        const col = colorFor(p.cluster);
        const pct = Math.round((p.size / 46) * 100);
        svg += `<text x="${left - 12}" y="${y + rowH / 2 + 5}" text-anchor="end" font-size="13.5" fill="#111111">${lbl}</text>
                <rect class="svg-hbar" style="animation-delay:${ri * 60}ms" x="${left}" y="${y + 10}" width="${bw}" height="${rowH - 20}" fill="${col}" stroke="#111111" stroke-width="1" data-tip="<b>${lbl}</b><br>Salary/Price: ${p.Salary_to_Price.toFixed(2)}<br>Городов: ${p.size} (${pct}%)"/>
                <text x="${left + bw + 8}" y="${y + rowH / 2 + 5}" font-size="13" font-weight="600" fill="#111111">${p.Salary_to_Price.toFixed(2)}, ${p.size} гор.</text>`;
      });

      wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${svg}</svg>`;
      bindSvgTooltips(wrap);
    }

    function renderProfilesTable(run) {
      const rows = run.profiles.map(p => {
        const highlight = state.clusterFilter !== "all" && String(p.cluster) !== state.clusterFilter ? 'style="opacity:0.42"' : "";
        return `<tr ${highlight}>
          <td><span class="badge"><span class="dot" style="background:${colorFor(p.cluster)}"></span>${p.cluster === -1 ? "Шум" : p.cluster}</span></td>
          <td class="num">${p.size}</td>
          <td class="num">${p.Work.toFixed(0)}</td>
          <td class="num">${p.Price.toFixed(1)}</td>
          <td class="num">${p.Salary.toFixed(1)}</td>
          <td class="num">${p.Salary_to_Price.toFixed(2)}</td>
          <td>${p.cities.join(", ")}</td>
        </tr>`;
      }).join("");

      document.getElementById("profiles-table-wrap").innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Группа</th><th class="num">N</th><th class="num">Work</th><th class="num">Price</th><th class="num">Salary</th><th class="num">Sal/Pr</th><th>Города</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>`;

      const box = document.getElementById("cluster-interpretation");
      if (state.clusterFilter !== "all") {
        const target = run.profiles.find(p => String(p.cluster) === state.clusterFilter);
        if (target) {
          box.innerHTML = `<p><strong>${clusterTitle(state.algo, state.k, target.cluster)}.</strong> Работа ${target.Work} ч, цены ${target.Price}, зарплата ${target.Salary}, отношение ${target.Salary_to_Price}.</p>`;
          return;
        }
      }
      if (state.algo === "dbscan") {
        box.innerHTML = `<p>При eps = ${state.eps} и min_samples = ${state.ms} плотность выделяет базовые скопления и изолирует экстремальные города в шум. При eps = 0.8 в шум уходят 6 самых дорогих городов, Гонконг и Тайбэй.</p>`;
      } else if (state.algo === "ward") {
        box.innerHTML = `<p>Метод Уорда при k = 4 делит города на 4 типа по уровню доходов и длине рабочего года. Максимальная покупательная способность у кластера 2: 0.72 против 0.67 у самого дорогого кластера 3.</p>`;
      } else {
        box.innerHTML = `<p>При k = 4 k-means переносит 4 города с умеренным рабочим годом из кластера 0 в кластер 1 по сравнению с Уордом, оставляя в кластере 0 только города с самым длинным рабочим годом.</p>`;
      }
    }

    function quantile(sorted, q) {
      const pos = (sorted.length - 1) * q;
      const lo = Math.floor(pos), hi = Math.ceil(pos);
      return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
    }

    function renderDataTab(run) {
      const feat = state.distFeature;
      const unique = [...new Set(run.labels)].sort((a, b) => a - b);
      const wrapDist = document.getElementById("svg-dist");
      const allVals = PAYLOAD.cities.map(c => c[feat]);
      const minV = Math.min(...allVals), maxV = Math.max(...allVals);
      const span = (maxV - minV) || 1;
      const W = 540, H = 300, pad = { l: 56, r: 20, t: 18, b: 38 };
      const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;
      const sy = v => pad.t + ph - ((v - minV) / span) * ph;

      let svg = "";
      for (let i = 0; i <= 4; i++) {
        const v = minV + (span * i) / 4;
        const y = sy(v);
        svg += `<line x1="${pad.l}" y1="${y}" x2="${W - pad.r}" y2="${y}" stroke="#e5e5e5" stroke-width="1"/>
                <text x="${pad.l - 9}" y="${y + 4}" text-anchor="end" font-size="12.5" fill="#5c5c5c">${v < 2 ? v.toFixed(2) : Math.round(v)}</text>`;
      }

      const step = pw / unique.length;
      unique.forEach((cl, idx) => {
        const items = run.labels.map((l, i) => (l === cl ? PAYLOAD.cities[i] : null)).filter(Boolean);
        const vals = items.map(c => c[feat]).sort((a, b) => a - b);
        const cx = pad.l + idx * step + step / 2;
        const q1 = quantile(vals, 0.25), med = quantile(vals, 0.5), q3 = quantile(vals, 0.75);
        const col = colorFor(cl);
        const bw = Math.min(48, step * 0.44);
        const lbl = cl === -1 ? "Шум" : `Кл. ${cl}`;

        svg += `<line x1="${cx}" y1="${sy(vals[vals.length - 1])}" x2="${cx}" y2="${sy(vals[0])}" stroke="#111111" stroke-width="1.3"/>
                <rect class="svg-bar" style="animation-delay:${idx * 60}ms" x="${cx - bw / 2}" y="${sy(q3)}" width="${bw}" height="${Math.max(2, sy(q1) - sy(q3))}" fill="${col}" fill-opacity="0.24" stroke="${col}" stroke-width="1.6" data-tip="<b>${lbl}</b><br>Медиана: ${med.toFixed(2)}<br>Q1–Q3: ${q1.toFixed(1)}–${q3.toFixed(1)}"/>
                <line x1="${cx - bw / 2}" y1="${sy(med)}" x2="${cx + bw / 2}" y2="${sy(med)}" stroke="#111111" stroke-width="2.4"/>
                <text x="${cx}" y="${H - 12}" text-anchor="middle" font-size="13" fill="#111111">${lbl}</text>`;

        items.forEach((c, j) => {
          const jx = cx + ((j % 5) - 2) * 3.8;
          svg += `<circle cx="${jx}" cy="${sy(c[feat])}" r="3.6" fill="${col}" stroke="#111111" stroke-width="0.6" data-tip="<b>${c.name}</b><br>${feat}: ${c[feat]}"/>`;
        });
      });

      wrapDist.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${svg}</svg>`;
      bindSvgTooltips(wrapDist);

      const wrapCorr = document.getElementById("svg-corr");
      const cols = PAYLOAD.meta.features;
      const corr = PAYLOAD.data_stats.corr;
      const CW = 460, CH = 250, cl = 82, ct = 34, cw = (CW - cl - 20) / 3, ch = (CH - ct - 16) / 3;
      let csvg = "";
      cols.forEach((c, i) => {
        csvg += `<text x="${cl + i * cw + cw / 2}" y="22" text-anchor="middle" font-size="13.5" font-weight="600" fill="#111111">${c}</text>
                 <text x="${cl - 10}" y="${ct + i * ch + ch / 2 + 5}" text-anchor="end" font-size="13.5" font-weight="600" fill="#111111">${c}</text>`;
      });
      corr.forEach((row, r) => row.forEach((v, c) => {
        const bg = divergingColor(v, 1.0);
        const fg = textOnDiverging(v, 1.0);
        csvg += `<g class="svg-fade" style="animation-delay:${(r * 3 + c) * 30}ms" data-tip="${cols[r]} и ${cols[c]}: r = ${v.toFixed(2)}">
          <rect x="${cl + c * cw}" y="${ct + r * ch}" width="${cw}" height="${ch}" fill="${bg}" stroke="#ffffff" stroke-width="2"/>
          <text x="${cl + c * cw + cw / 2}" y="${ct + r * ch + ch / 2 + 5}" text-anchor="middle" font-size="14" font-weight="600" fill="${fg}">${v.toFixed(2)}</text>
        </g>`;
      }));
      wrapCorr.innerHTML = `<svg viewBox="0 0 ${CW} ${CH}">${csvg}</svg>`;
      bindSvgTooltips(wrapCorr);

      const descRows = PAYLOAD.data_stats.describe.map(r => `<tr>
        <td><strong>${r.feature}</strong></td>
        <td class="num">${r.mean.toFixed(1)}</td>
        <td class="num">${r.std.toFixed(1)}</td>
        <td class="num">${r.min.toFixed(1)}</td>
        <td class="num">${r["50%"].toFixed(1)}</td>
        <td class="num">${r.max.toFixed(1)}</td>
      </tr>`).join("");

      document.getElementById("describe-table-wrap").innerHTML = `
        <table>
          <thead><tr><th>Признак</th><th class="num">Среднее</th><th class="num">Std</th><th class="num">Min</th><th class="num">Медиана</th><th class="num">Max</th></tr></thead>
          <tbody>${descRows}</tbody>
        </table>`;

      const filtered = PAYLOAD.cities
        .map((c, i) => ({ ...c, cl: run.labels[i] }))
        .filter(c => c.Salary >= state.minSalary && c.Work <= state.maxWork)
        .filter(c => state.clusterFilter === "all" || String(c.cl) === state.clusterFilter);

      document.getElementById("cities-count-note").textContent = `${filtered.length} из 46`;
      const cityRows = filtered.map(c => `<tr>
        <td>${c.name}</td>
        <td><span class="badge"><span class="dot" style="background:${colorFor(c.cl)}"></span>${c.cl === -1 ? "Шум" : c.cl}</span></td>
        <td class="num">${c.Work}</td>
        <td class="num">${c.Price}</td>
        <td class="num">${c.Salary}</td>
        <td class="num">${c.Salary_to_Price}</td>
      </tr>`).join("");

      document.getElementById("cities-table-wrap").innerHTML = `
        <table>
          <thead><tr><th>Город</th><th>Группа</th><th class="num">Work</th><th class="num">Price</th><th class="num">Salary</th><th class="num">Sal/Pr</th></tr></thead>
          <tbody>${cityRows}</tbody>
        </table>`;
    }

    function getReferenceLabels(key) {
      if (key === "ward") return PAYLOAD.ward.runs["4"];
      if (key === "kmeans") return PAYLOAD.kmeans.runs["4"];
      return PAYLOAD.dbscan.runs["4"]["0.8"];
    }

    function renderCompareTab(run) {
      const refs = [
        { name: "Уорд, k = 4", r: getReferenceLabels("ward") },
        { name: "k-means, k = 4", r: getReferenceLabels("kmeans") },
        { name: "DBSCAN, eps = 0.8", r: getReferenceLabels("dbscan") },
      ];

      document.getElementById("compare-table-wrap").innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Алгоритм</th>
              <th class="num">Кластеры</th>
              <th class="num">Шум</th>
              <th class="num">Silhouette</th>
              <th class="num">Davies-Bouldin</th>
              <th class="num">Calinski-Harabasz</th>
              <th class="num">ARI с k-means</th>
            </tr>
          </thead>
          <tbody>
            ${refs.map(({ name, r }) => `<tr>
              <td><strong>${name}</strong></td>
              <td class="num">${r.n_clusters}</td>
              <td class="num">${r.n_noise > 0 ? `${r.n_noise}, ${r.noise_pct}%` : "0"}</td>
              <td class="num">${r.silhouette.toFixed(3)}</td>
              <td class="num">${r.davies_bouldin.toFixed(3)}</td>
              <td class="num">${r.calinski_harabasz.toFixed(2)}</td>
              <td class="num">${r.ari_km4.toFixed(3)}</td>
            </tr>`).join("")}
          </tbody>
        </table>`;

      const la = getReferenceLabels(state.cmpA).labels;
      const lb = getReferenceLabels(state.cmpB).labels;
      const ua = [...new Set(la)].sort((a, b) => a - b);
      const ub = [...new Set(lb)].sort((a, b) => a - b);
      const mat = ua.map(a => ub.map(b => la.filter((v, i) => v === a && lb[i] === b).length));
      const maxM = Math.max(1, ...mat.flat());

      const wrapCt = document.getElementById("svg-crosstab");
      const W = 500, rowH = 48, left = 86, top = 36;
      const H = top + ua.length * rowH + 16;
      const colW = (W - left - 16) / ub.length;
      let ctSvg = "";
      ub.forEach((b, ci) => {
        ctSvg += `<text x="${left + ci * colW + colW / 2}" y="22" text-anchor="middle" font-size="13.5" font-weight="600" fill="#111111">${b === -1 ? "Шум" : "Кл. " + b}</text>`;
      });
      ua.forEach((a, ri) => {
        const y = top + ri * rowH;
        ctSvg += `<text x="${left - 12}" y="${y + rowH / 2 + 5}" text-anchor="end" font-size="13.5" fill="#111111">${a === -1 ? "Шум" : "Кл. " + a}</text>`;
        ub.forEach((b, ci) => {
          const v = mat[ri][ci];
          const t = v / maxM;
          const bg = v === 0 ? "#f5f5f5" : (t < 0.5 ? lerpColor("#f2fbd9", "#c9ff33", t * 2) : lerpColor("#c9ff33", "#166534", (t - 0.5) * 2));
          const fg = t > 0.72 ? "#ffffff" : "#111111";
          ctSvg += `<g class="svg-fade" style="animation-delay:${(ri * ub.length + ci) * 25}ms" data-tip="Совпадений: ${v}">
            <rect x="${left + ci * colW}" y="${y}" width="${colW}" height="${rowH}" fill="${bg}" stroke="#ffffff" stroke-width="2"/>
            <text x="${left + ci * colW + colW / 2}" y="${y + rowH / 2 + 5}" text-anchor="middle" font-size="14" font-weight="${v > 0 ? 700 : 400}" fill="${fg}">${v}</text>
          </g>`;
        });
      });
      wrapCt.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${ctSvg}</svg>`;
      bindSvgTooltips(wrapCt);

      /* Таблица расхождений или шумовых городов под матрицей переходов */
      const diffTitle = document.getElementById("diff-cities-title");
      const diffNote = document.getElementById("diff-cities-note");
      const diffWrap = document.getElementById("diff-cities-wrap");
      if (state.cmpA === "dbscan" || state.cmpB === "dbscan") {
        const dbRun = getReferenceLabels("dbscan");
        const noiseCities = PAYLOAD.cities
          .map((c, i) => ({ ...c, lbl: dbRun.labels[i] }))
          .filter(c => c.lbl === -1)
          .sort((a, b) => b.dist_3rd - a.dist_3rd);
        diffTitle.textContent = "Шумовые города DBSCAN";
        diffNote.textContent = `${noiseCities.length} городов`;
        diffWrap.innerHTML = `
          <table>
            <thead><tr><th>Город</th><th class="num">Work</th><th class="num">Price</th><th class="num">Salary</th><th class="num">3-dist</th></tr></thead>
            <tbody>${noiseCities.map(c => `<tr>
              <td><strong>${c.name}</strong></td>
              <td class="num">${c.Work}</td>
              <td class="num">${c.Price}</td>
              <td class="num">${c.Salary}</td>
              <td class="num">${c.dist_3rd.toFixed(2)}</td>
            </tr>`).join("")}</tbody>
          </table>`;
      } else {
        const moved = PAYLOAD.cities
          .map((c, i) => ({ ...c, a: la[i], b: lb[i] }))
          .filter(c => c.a !== c.b);
        diffTitle.textContent = "Расхождения между методами";
        diffNote.textContent = moved.length > 0 ? `${moved.length} города` : "полное совпадение";
        if (moved.length === 0) {
          diffWrap.innerHTML = `<p style="margin:6px 0;color:#5c5c5c;">Выбран один и тот же метод, разбиения совпадают.</p>`;
        } else {
          diffWrap.innerHTML = `
            <table>
              <thead><tr><th>Город</th><th class="num">Work</th><th class="num">Price</th><th class="num">Salary</th><th class="num">${state.cmpA}</th><th class="num">${state.cmpB}</th></tr></thead>
              <tbody>${moved.map(c => `<tr>
                <td><strong>${c.name}</strong></td>
                <td class="num">${c.Work}</td>
                <td class="num">${c.Price}</td>
                <td class="num">${c.Salary}</td>
                <td class="num">${c.a}</td>
                <td class="num">${c.b}</td>
              </tr>`).join("")}</tbody>
            </table>`;
        }
      }

      const items = PAYLOAD.cities
        .map((c, i) => ({ name: c.name, sil: run.sil_samples[i], cl: run.labels[i] }))
        .filter(x => x.sil !== null)
        .sort((a, b) => a.sil - b.sil);

      const negCount = items.filter(x => x.sil < 0).length;
      document.getElementById("sil-samples-note").textContent = negCount > 0 ? `отрицательных: ${negCount}` : "";

      const wrapSil = document.getElementById("svg-sil-samples");
      const SW = 540, sRow = 13.5, sLeft = 114, sRight = 24, sTop = 14;
      const SH = sTop + items.length * sRow + 26;
      const sMin = Math.min(-0.25, ...items.map(x => x.sil));
      const sMax = Math.max(0.75, ...items.map(x => x.sil));
      const sx = v => sLeft + ((v - sMin) / (sMax - sMin)) * (SW - sLeft - sRight);
      const x0 = sx(0);

      let sSvg = `<line x1="${x0}" y1="${sTop}" x2="${x0}" y2="${SH - 22}" stroke="#111111" stroke-width="1.2"/>`;
      items.forEach((it, idx) => {
        const y = sTop + idx * sRow;
        const xVal = sx(it.sil);
        const rx = it.sil >= 0 ? x0 : xVal;
        const rw = Math.max(1.5, Math.abs(xVal - x0));
        const col = it.sil < 0 ? "#b91c1c" : colorFor(it.cl);
        const cls = it.sil < 0 ? "svg-hbar-neg" : "svg-hbar";
        sSvg += `<text x="${sLeft - 8}" y="${y + 10}" text-anchor="end" font-size="10.5" fill="#262626">${it.name}</text>
                 <rect class="${cls}" style="animation-delay:${idx * 10}ms" x="${rx}" y="${y + 1.5}" width="${rw}" height="9.5" fill="${col}" data-tip="<b>${it.name}</b><br>Силуэт: ${it.sil.toFixed(3)}"/>`;
      });
      [0, 0.2, 0.4, 0.6].forEach(v => {
        if (v <= sMax) {
          sSvg += `<text x="${sx(v)}" y="${SH - 6}" text-anchor="middle" font-size="11.5" fill="#5c5c5c">${v.toFixed(1)}</text>`;
        }
      });
      wrapSil.innerHTML = `<svg viewBox="0 0 ${SW} ${SH}">${sSvg}</svg>`;
      bindSvgTooltips(wrapSil);
    }

    function renderAll() {
      updateControlsVisibility();
      const run = getActiveRun();
      renderDropdowns(run);
      renderKPIs(run);

      document.getElementById("tab-clusters").classList.toggle("hidden", state.tab !== "clusters");
      document.getElementById("tab-data").classList.toggle("hidden", state.tab !== "data");
      document.getElementById("tab-compare").classList.toggle("hidden", state.tab !== "compare");

      if (state.tab === "clusters") {
        renderScatter(run);
        renderTuningSvg();
        renderHeatmapSvg(run);
        renderPowerSvg(run);
        renderProfilesTable(run);
      } else if (state.tab === "data") {
        renderDataTab(run);
      } else {
        renderCompareTab(run);
      }
    }

    document.querySelectorAll(".tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        state.tab = btn.dataset.tab;
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
        renderAll();
      });
    });

    document.querySelectorAll("#algo-switch .seg-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        state.algo = btn.dataset.algo;
        state.clusterFilter = "all";
        renderAll();
      });
    });

    document.getElementById("param-k").addEventListener("input", e => {
      state.k = Number(e.target.value);
      document.getElementById("param-k-val").textContent = e.target.value;
      renderAll();
    });

    document.getElementById("param-eps").addEventListener("input", e => {
      state.eps = Number(e.target.value).toFixed(1);
      document.getElementById("param-eps-val").textContent = state.eps;
      renderAll();
    });

    document.getElementById("min-salary").addEventListener("input", e => {
      state.minSalary = Number(e.target.value);
      document.getElementById("min-salary-val").textContent = e.target.value;
      renderAll();
    });

    document.getElementById("max-work").addEventListener("input", e => {
      state.maxWork = Number(e.target.value);
      document.getElementById("max-work-val").textContent = e.target.value;
      renderAll();
    });

    document.getElementById("btn-reset").addEventListener("click", () => {
      state.k = 4;
      state.eps = "0.8";
      state.ms = "4";
      state.clusterFilter = "all";
      document.getElementById("param-k").value = "4";
      document.getElementById("param-k-val").textContent = "4";
      document.getElementById("param-eps").value = "0.8";
      document.getElementById("param-eps-val").textContent = "0.8";
      renderAll();
    });

    window.addEventListener("resize", () => {
      const el = document.getElementById("plot-scatter");
      if (el && el.data && !el.closest(".hidden")) {
        Plotly.Plots.resize(el);
      }
    });

    renderAll();
  </script>
</body>
</html>
"""


def build_html(out_path: Path = OUT_PATH) -> Path:
    payload = build_dashboard_payload()
    logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    logo_uri = f"data:image/png;base64,{logo_b64}"
    html = (
        HTML_TEMPLATE
        .replace("__PAYLOAD_JSON__", json.dumps(payload, ensure_ascii=False))
        .replace("__ITMO_LOGO_URI__", logo_uri)
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    p = build_html()
    print(f"Собрано: {p} ({p.stat().st_size // 1024} КБ)")
