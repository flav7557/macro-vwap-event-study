#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
 MACRO EVENT BACKTESTER — SINGLE COUNTRY / ~20 STOCKS
==============================================================================
 Usage : python3 macro_event_backtester_single_country_20stocks.py

 BUT
 ---
 Screening d'un univers d'actions d'UN SEUL pays (defaut : US, ~20 actions).
 Pour chaque action : signal macro + execution VWAP + batterie complete de
 tests de robustesse, puis classement automatique (A/B/C/D) et tableaux
 maitres comparatifs pour decider quelles actions creuser ensuite.

 WORKFLOW
 --------
   1. Charger UNE fois le classeur (feuilles `data` + `METRIQ_FINISH`).
   2. Choisir le pays (defaut : US ; Entree = US).
   3. Selectionner plusieurs CSV de prix (~20 actions) en une multi-selection.
   4. Pour chaque action : robustness lab condense + classement.
   5. Exporter les tableaux maitres + rapport console global.

 Reutilise le moteur vectorise du robustness lab (rapide sur 20 actions).
==============================================================================
"""

import os
import re
import sys
import glob
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------- #
#  PARAMETRES (modifiables en tete de fichier)                                #
# --------------------------------------------------------------------------- #
COUNTRY_DEFAULT = "US"               # pays teste par defaut (Entree = US)

# --- signal macro ---
HORIZONS_MIN = [15, 30, 60, 120]
ADD_CLOSE_HORIZON = True
MIN_IMPORTANCE = 4
MIN_VALID_OBS = 50
SIGNAL_THRESHOLD = 0.5
EXCLUDE_MIXED = True
MAX_ENTRY_DELAY_MIN = 60

# --- regle VWAP ---
VWAP_RETURN_MODES = ["strict", "tol_bps", "tol_atr"]
VWAP_TOL_BPS = 10.0
VWAP_TOL_ATR_MULT = 0.25
VWAP_WAIT_WINDOWS_MIN = [30, 60, 120]
TOUCH_ENTRY_PRICE = "vwap"

# --- robustesse ---
COST_BPS_GRID = [0, 5, 10, 20, 30, 50]
N_RANDOM_RUNS = 100                  # allege pour le batch
RANDOM_SEED = 42
TRAIN_RATIO = 0.70
MIN_TRADES_FOR_CONFIG = 50
SHIFT_DAYS = [-1, +1]

# --- batch / exports ---
EXPORT_ALL_TRADES = False            # True -> exporte aussi batch_all_trades_light.csv

# --- reporting trader / graphs ---
GENERATE_TRADER_REPORT = True          # cree scorecard + graphes PNG pour presentation trader
REPORT_TOP_N = 12                      # nombre max d'assets visibles dans les graphes top-N
TRADER_REPORT_DPI = 180                # resolution des graphes PNG
MIN_RELEASES_FOR_COUNTRY = 20        # en dessous : warning + skip pays
MIN_TRADES_FOR_ACTION = 30           # en dessous : INSUFFICIENT_DATA

# --- seuils de classification ---
CLS_SHARPE_MIN = 2.0                 # Sharpe mini pour A
CLS_RANDOM_PCT_MIN = 95.0            # percentile mini vs random pour A
CLS_COST_BREAKEVEN_MIN = 10.0        # break-even mini (bps) pour A
CLS_WF_POS_RATIO_MIN = 0.6           # ratio annees positives mini pour A

# --- divers ---
DIRECTION_MAP = {"YES": 1.0, "NO": -1.0, "MIXED": 0.0}
# --------------------------------------------------------------------------- #
def banner(txt):
    print("\n" + "=" * 70)
    print(f"  {txt}")
    print("=" * 70)


def ask_path(prompt, filetypes=None, title="Selectionne un fichier"):
    """Fenetre de selection de fichier (tkinter), repli saisie manuelle."""
    print(prompt)
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        ft = filetypes or [("Tous les fichiers", "*.*")]
        path = filedialog.askopenfilename(title=title, filetypes=ft)
        root.update()
        root.destroy()
        if path and os.path.isfile(path):
            print(f"    selectionne : {path}")
            return path
        print("  -> selection annulee, passe en saisie manuelle.")
    except Exception:
        print("  -> pas d'interface graphique, passe en saisie manuelle.")
    while True:
        p = input("  > Chemin du fichier : ").strip().strip('"').strip("'")
        if not p:
            print("  -> chemin vide, reessaie.")
            continue
        p = os.path.expanduser(p)
        if os.path.isfile(p):
            return p
        print(f"  -> introuvable : {p}")


def to_float_eu(series):
    """Texte -> float en gerant decimales europeennes et separateurs milliers."""
    def conv(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip()
        if s == "" or s.lower() in ("nan", "none", "-"):
            return np.nan
        s = s.replace("%", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return np.nan
    return series.map(conv)


def clean_event_name(s):
    """'CPI MoM (Dec)' -> 'CPI MoM'."""
    s = str(s)
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)
    return s.strip()


def detect_engine(path):
    return "odf" if os.path.splitext(path)[1].lower() == ".ods" else "openpyxl"


def find_sheets(path, engine):
    xl = pd.ExcelFile(path, engine=engine)
    names = xl.sheet_names
    data_sheet = metriq_sheet = None
    for n in names:
        key = n.strip().lower().replace(" ", "_")
        if key == "data" and data_sheet is None:
            data_sheet = n
        if key.startswith("metriq") and metriq_sheet is None:
            metriq_sheet = n
    if data_sheet is None or metriq_sheet is None:
        print(f"\n  Feuilles trouvees : {names}")
        if data_sheet is None:
            data_sheet = input("  Nom EXACT de la feuille events (data) : ").strip()
        if metriq_sheet is None:
            metriq_sheet = input("  Nom EXACT de la feuille metriques     : ").strip()
    return data_sheet, metriq_sheet


def load_metriq(path, sheet, engine):
    m = pd.read_excel(path, sheet_name=sheet, engine=engine)
    m.columns = [c.strip() for c in m.columns]
    needed = ["Country", "events", "macro_family", "higher_is_good",
              "event_importance_guess", "valid_obs_count",
              "surprise_avg_10y", "surprise_std_10y", "beat_rate_10y"]
    for c in needed:
        if c not in m.columns:
            raise KeyError(f"Colonne manquante dans METRIQ : '{c}'")
    m["event_key"] = m["events"].astype(str).str.strip()
    m["Country"] = m["Country"].astype(str).str.strip()
    for c in ["surprise_avg_10y", "surprise_std_10y", "beat_rate_10y",
              "event_importance_guess", "valid_obs_count"]:
        m[c] = pd.to_numeric(m[c], errors="coerce")
    return m


def load_events(path, sheet, engine):
    cols = ["event_date", "country", "event", "estimate", "actual", "impact"]
    raw = pd.read_excel(path, sheet_name=sheet, engine=engine)
    raw.columns = [c.strip() for c in raw.columns]
    keep = [c for c in cols if c in raw.columns]
    d = raw[keep].copy()
    d["event_date"] = pd.to_datetime(d["event_date"], utc=True, errors="coerce")
    d["country"] = d["country"].astype(str).str.strip()
    d["event_key"] = d["event"].apply(clean_event_name)
    d["estimate_f"] = to_float_eu(d["estimate"])
    d["actual_f"] = to_float_eu(d["actual"])
    return d


def load_prices(path):
    px = pd.read_csv(path)
    px.columns = [c.strip().lower() for c in px.columns]
    req = {"timestamp", "open", "high", "low", "close", "volume"}
    if not req.issubset(set(px.columns)):
        raise KeyError(f"CSV prix : colonnes attendues {req}, trouvees {set(px.columns)}")
    px["timestamp"] = pd.to_datetime(px["timestamp"], utc=True, errors="coerce")
    px = px.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    for c in ["open", "high", "low", "close", "volume"]:
        px[c] = pd.to_numeric(px[c], errors="coerce")
    px["date"] = px["timestamp"].dt.date
    # VWAP ancree au jour (reset quotidien)
    typical = (px["high"] + px["low"] + px["close"]) / 3.0
    pv = typical * px["volume"]
    cum_pv = pv.groupby(px["date"]).cumsum()
    cum_v = px["volume"].groupby(px["date"]).cumsum()
    px["vwap"] = (cum_pv / cum_v.replace(0, np.nan)).fillna(px["close"])
    # ATR-like intraday pour la tolerance dynamique
    tr = (px["high"] - px["low"]).abs()
    px["atr_like"] = tr.groupby(px["date"]).transform(
        lambda s: s.rolling(14, min_periods=3).mean()
    ).fillna(tr)
    return px


def build_signals(events, metriq, country):
    """Joint events <-> metriques, calcule surprise_z et signal directionnel."""
    ev = events[events["country"] == country].copy()
    me = metriq[metriq["Country"] == country].copy()
    if ev.empty:
        raise ValueError(f"Aucun event pour '{country}' dans data.")
    if me.empty:
        raise ValueError(f"Aucune metrique pour '{country}' dans METRIQ.")
    me_small = me[["event_key", "macro_family", "higher_is_good",
                   "event_importance_guess", "valid_obs_count",
                   "surprise_avg_10y", "surprise_std_10y", "beat_rate_10y"]]
    j = ev.merge(me_small, on="event_key", how="inner")
    j = j[j["event_importance_guess"] >= MIN_IMPORTANCE]
    j = j[j["valid_obs_count"] >= MIN_VALID_OBS]
    if EXCLUDE_MIXED:
        j = j[j["higher_is_good"].str.upper() != "MIXED"]
    j = j.dropna(subset=["event_date", "estimate_f", "actual_f",
                         "surprise_avg_10y", "surprise_std_10y"])
    j = j[j["surprise_std_10y"] > 0]
    j["surprise_raw"] = j["actual_f"] - j["estimate_f"]
    j["surprise_z"] = (j["surprise_raw"] - j["surprise_avg_10y"]) / j["surprise_std_10y"]
    j["direction"] = j["higher_is_good"].str.upper().map(DIRECTION_MAP).fillna(0.0)
    j["signal"] = j["surprise_z"] * j["direction"]
    j = j[j["direction"] != 0.0]
    j = j[j["signal"].abs() >= SIGNAL_THRESHOLD]
    j = j.sort_values("event_date").reset_index(drop=True)
    return j


# --------------------------------------------------------------------------- #
#  MOTEUR DE BACKTEST UNIFIE                                                    #
# --------------------------------------------------------------------------- #
# Idee : tout test (macro, random side, random timestamps, placebo) se ramene a
# une liste d'ORDRES = (event_dt, trade_sign, meta...). Le moteur trouve le prix
# candidat, applique la regle VWAP choisie, puis mesure le rendement BRUT sur
# chaque horizon. Les couts sont appliques APRES, dans l'agregation.


# --- Precalcul des tableaux numpy (vitesse) ---------------------------------
class PA:
    """
    Conteneur de tableaux numpy precalcules a partir du DataFrame de prix.
    Evite les acces pandas (.iloc / masques booleens) dans les boucles chaudes.
    """
    __slots__ = ("ts", "ts64", "close", "high", "low", "vwap", "atr", "day_code",
                 "day_end_idx", "day_first_idx", "first_open_ts", "n",
                 "day_to_first_idx")

    def __init__(self, px):
        self.ts = px["timestamp"].to_numpy()                       # datetime64[ns, UTC]
        self.ts64 = px["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
        self.close = px["close"].to_numpy(dtype=float)
        self.high = px["high"].to_numpy(dtype=float)
        self.low = px["low"].to_numpy(dtype=float)
        self.vwap = px["vwap"].to_numpy(dtype=float)
        self.atr = px["atr_like"].to_numpy(dtype=float)
        self.n = len(px)
        # codes entiers de jour (pour comparaisons rapides "meme jour ?")
        day_str = px["date"].astype(str).to_numpy()
        uniq, inv = np.unique(day_str, return_inverse=True)
        self.day_code = inv
        # index du dernier prix de chaque jour (close du jour)
        last_idx = {}
        first_idx = {}
        for i in range(self.n):
            c = inv[i]
            last_idx[c] = i
            if c not in first_idx:
                first_idx[c] = i
        self.day_end_idx = last_idx
        self.day_first_idx = first_idx
        # map date(python) -> index du 1er prix du jour (pour pre-open)
        self.day_to_first_idx = {}
        dates_py = px["date"].to_numpy()
        for c, i in first_idx.items():
            self.day_to_first_idx[dates_py[i]] = i


def find_entry_fast(pa, event_dt):
    """Version array de find_entry. Retourne (cand_idx, mode) ou (None, mode)."""
    day = event_dt.date()
    # cas pre-ouverture : news avant le 1er prix du jour -> open du meme jour
    fi = pa.day_to_first_idx.get(day, None)
    if fi is not None:
        first_t = pd.Timestamp(pa.ts[fi])
        if event_dt <= first_t:
            return fi, "PRE_OPEN_SAME_DAY"
    # cas intraday : 1er prix >= timestamp de la news
    pos = np.searchsorted(pa.ts64, np.datetime64(event_dt.tz_convert("UTC").tz_localize(None)))
    if pos >= pa.n:
        return None, "AFTER_LAST_PRICE"
    pos_ts = pd.Timestamp(pa.ts[pos])
    if pos_ts.date() != day:
        return None, "NO_TRADE_DAY"   # jour sans cotation pour cet event
    delay = (pos_ts - event_dt).total_seconds() / 60.0
    if delay > MAX_ENTRY_DELAY_MIN:
        return None, f"ENTRY_DELAY_{delay:.0f}min"
    return pos, "INTRADAY"


def _same_day(pa, i, day_c):
    return 0 <= i < pa.n and pa.day_code[i] == day_c


def resolve_close_cross_fast(pa, cand_idx, trade_sign, mode, wait_minutes):
    """Version array de CLOSE_CROSS."""
    price0, vwap0 = pa.close[cand_idx], pa.vwap[cand_idx]
    if not np.isfinite(vwap0) or vwap0 <= 0:
        return None, None, "VWAP_NA", np.nan
    if (price0 <= vwap0) if trade_sign > 0 else (price0 >= vwap0):
        return cand_idx, price0, "VWAP_IMMEDIATE", 0.0
    day_c = pa.day_code[cand_idx]
    t0 = pa.ts64[cand_idx]
    deadline = t0 + np.timedelta64(int(wait_minutes), "m")
    prev_diff = price0 - vwap0
    j = cand_idx + 1
    while j < pa.n and pa.day_code[j] == day_c and pa.ts64[j] <= deadline:
        p, v, a = pa.close[j], pa.vwap[j], pa.atr[j]
        if not np.isfinite(v) or v <= 0:
            j += 1
            continue
        hit = False
        if mode == "strict":
            cur_diff = p - v
            if np.sign(cur_diff) != np.sign(prev_diff) or abs(cur_diff) < 1e-9:
                hit = True
            prev_diff = cur_diff
        elif mode == "tol_bps":
            hit = abs(p - v) / v <= (VWAP_TOL_BPS / 1e4)
        elif mode == "tol_atr":
            tol = VWAP_TOL_ATR_MULT * (a if np.isfinite(a) else 0.0)
            hit = abs(p - v) <= max(tol, 1e-9)
        if hit:
            wait_eff = (pa.ts64[j] - t0) / np.timedelta64(1, "m")
            return j, p, f"VWAP_RETURN_{mode}", float(wait_eff)
        j += 1
    return None, None, "VWAP_NO_RETURN", np.nan


def resolve_limit_touch_fast(pa, cand_idx, trade_sign, wait_minutes):
    """Version array de LIMIT_TOUCH (ordre limite a la VWAP)."""
    price0, vwap0 = pa.close[cand_idx], pa.vwap[cand_idx]
    if not np.isfinite(vwap0) or vwap0 <= 0:
        return None, None, "VWAP_NA", np.nan
    if (price0 <= vwap0) if trade_sign > 0 else (price0 >= vwap0):
        return cand_idx, price0, "VWAP_IMMEDIATE", 0.0
    day_c = pa.day_code[cand_idx]
    t0 = pa.ts64[cand_idx]
    deadline = t0 + np.timedelta64(int(wait_minutes), "m")
    j = cand_idx + 1
    while j < pa.n and pa.day_code[j] == day_c and pa.ts64[j] <= deadline:
        v = pa.vwap[j]
        if not np.isfinite(v) or v <= 0:
            j += 1
            continue
        touched = (pa.low[j] <= v) if trade_sign > 0 else (pa.high[j] >= v)
        if touched:
            entry_price = v if TOUCH_ENTRY_PRICE == "vwap" else pa.close[j]
            wait_eff = (pa.ts64[j] - t0) / np.timedelta64(1, "m")
            return j, entry_price, "VWAP_TOUCH", float(wait_eff)
        j += 1
    return None, None, "VWAP_NO_RETURN", np.nan


def exit_price_fast(pa, entry_idx, day_c, minutes):
    """Close du 1er prix >= entry_time+minutes, borne au jour (sinon close du jour)."""
    target = pa.ts64[entry_idx] + np.timedelta64(int(minutes), "m")
    pos = np.searchsorted(pa.ts64, target)
    if pos >= pa.n:
        pos = pa.n - 1
    if pa.day_code[pos] != day_c:
        end_i = pa.day_end_idx[day_c]
        return pa.close[end_i], pa.ts[end_i]
    return pa.close[pos], pa.ts[pos]


# --- MOTEUR UNIFIE (array-based) -------------------------------------------- #
def run_engine(orders, px_or_pa, vwap_method, vwap_mode=None, wait_min=0,
               model_name="MODEL", pa=None):
    """
    Transforme une liste d'ordres en trade records (rendements BRUTS).
    Accepte soit un DataFrame px (et construit un PA), soit directement un PA
    via l'argument `pa` (recommande pour la vitesse : on le reutilise).
    Retourne (records_df, skipped_dict).
    raw_ret est oriente sens du trade (positif=gagnant), AVANT couts.
    """
    if pa is None:
        pa = px_or_pa if isinstance(px_or_pa, PA) else PA(px_or_pa)

    horizons = list(HORIZONS_MIN)
    rows, skipped = [], {}

    for od in orders:
        edt = od["event_dt"]
        trade_sign = od["trade_sign"]
        cand_idx, entry_mode = find_entry_fast(pa, edt)
        if cand_idx is None:
            skipped[entry_mode] = skipped.get(entry_mode, 0) + 1
            continue
        c0 = pa.close[cand_idx]
        if not np.isfinite(c0) or c0 <= 0:
            skipped["BAD_ENTRY_PX"] = skipped.get("BAD_ENTRY_PX", 0) + 1
            continue

        if vwap_method == "none":
            entry_idx, entry_price, vreason, wait_eff = cand_idx, c0, "NO_VWAP", 0.0
        elif vwap_method == "close_cross":
            entry_idx, entry_price, vreason, wait_eff = resolve_close_cross_fast(
                pa, cand_idx, trade_sign, vwap_mode, wait_min)
        elif vwap_method == "limit_touch":
            entry_idx, entry_price, vreason, wait_eff = resolve_limit_touch_fast(
                pa, cand_idx, trade_sign, wait_min)
        else:
            raise ValueError(f"vwap_method inconnue : {vwap_method}")

        if entry_idx is None:
            skipped[vreason] = skipped.get(vreason, 0) + 1
            continue
        if not np.isfinite(entry_price) or entry_price <= 0:
            skipped["BAD_ENTRY_PX"] = skipped.get("BAD_ENTRY_PX", 0) + 1
            continue

        e_time = pa.ts[entry_idx]
        day_c = pa.day_code[entry_idx]
        cand_t = pa.ts[cand_idx]
        entry_delay = (pd.Timestamp(cand_t) - edt).total_seconds() / 60.0

        # horizons intraday
        for h in horizons:
            exit_px, exit_t = exit_price_fast(pa, entry_idx, day_c, h)
            if not np.isfinite(exit_px) or exit_px <= 0:
                continue
            raw_dir = (exit_px / entry_price - 1.0)
            raw_ret = trade_sign * raw_dir
            rows.append(_record(od, model_name, vwap_mode, wait_min, vwap_method,
                                e_time, entry_price, exit_t, exit_px, f"{h}min",
                                raw_dir, raw_ret, vreason, entry_mode, entry_delay,
                                wait_eff, trade_sign))
        # close du jour
        if ADD_CLOSE_HORIZON:
            end_i = pa.day_end_idx[day_c]
            close_px = pa.close[end_i]
            if np.isfinite(close_px) and close_px > 0:
                raw_dir = (close_px / entry_price - 1.0)
                raw_ret = trade_sign * raw_dir
                rows.append(_record(od, model_name, vwap_mode, wait_min, vwap_method,
                                    e_time, entry_price, pa.ts[end_i], close_px, "close",
                                    raw_dir, raw_ret, vreason, entry_mode, entry_delay,
                                    wait_eff, trade_sign))
    return pd.DataFrame(rows), skipped


def _record(od, model_name, vwap_mode, wait_min, vwap_method, e_time, entry_price,
            exit_t, exit_px, hlabel, raw_dir, raw_ret, vreason, entry_mode,
            entry_delay, wait_eff, trade_sign):
    """Construit une ligne de trade record (schema unifie)."""
    return {
        "model_name": model_name,
        "event_date": od["event_dt"],
        "event_key": od.get("event_key", ""),
        "macro_family": od.get("macro_family", ""),
        "hypothese": od.get("hypothese", ""),
        "signal": od.get("signal", np.nan),
        "trade_sign": trade_sign,
        "vwap_mode": vwap_mode if vwap_mode else "",
        "wait_min": wait_min,
        "entry_method": vwap_method,
        "entry_time": e_time,
        "entry_price": entry_price,
        "exit_time": exit_t,
        "exit_price": exit_px,
        "horizon": hlabel,
        "raw_ret": raw_ret,
        "ret_before_cost": raw_ret,
        "raw_dir": raw_dir,
        "vwap_entry_reason": vreason,
        "entry_mode": entry_mode,
        "entry_delay_min": entry_delay,
        "wait_eff_min": wait_eff,
        "year": pd.Timestamp(od["event_dt"]).year,
    }


# --------------------------------------------------------------------------- #
#  CONSTRUCTEURS D'ORDRES                                                       #
# --------------------------------------------------------------------------- #
def macro_orders(signals, hypothese):
    """
    Construit les ordres macro. DRIFT = suivre le signal ; FADE = inverser.
    trade_sign = sign(signal) * (+1 DRIFT / -1 FADE).
    """
    mult = 1.0 if hypothese == "DRIFT" else -1.0
    orders = []
    for _, s in signals.iterrows():
        sgn = np.sign(s["signal"])
        if sgn == 0:
            continue
        orders.append({
            "event_dt": s["event_date"], "trade_sign": sgn * mult,
            "event_key": s["event_key"], "macro_family": s["macro_family"],
            "signal": s["signal"], "hypothese": hypothese,
        })
    return orders


def random_side_orders(signals, rng):
    """Memes dates/events que la macro, mais sens LONG/SHORT tire au hasard."""
    orders = []
    signs = rng.choice([-1.0, 1.0], size=len(signals))
    for (idx, s), sg in zip(signals.iterrows(), signs):
        orders.append({
            "event_dt": s["event_date"], "trade_sign": float(sg),
            "event_key": s["event_key"], "macro_family": s["macro_family"],
            "signal": s["signal"], "hypothese": "RANDOM_SIDE",
        })
    return orders


def random_timestamp_orders(px, n_orders, rng, side_dist=None):
    """
    Timestamps aleatoires pris dans les barres disponibles (hors-news).
    side_dist : None -> sens random ; ou (p_long) pour imiter la distribution macro.
    """
    n_px = len(px)
    idxs = rng.integers(0, n_px, size=n_orders)
    if side_dist is None:
        signs = rng.choice([-1.0, 1.0], size=n_orders)
    else:
        signs = np.where(rng.random(n_orders) < side_dist, 1.0, -1.0)
    orders = []
    for i, sg in zip(idxs, signs):
        ts = px.iloc[int(i)]["timestamp"]
        # decaler d'une minute pour eviter de matcher exactement la barre i
        orders.append({
            "event_dt": ts - pd.Timedelta(minutes=1), "trade_sign": float(sg),
            "event_key": "RANDOM_TS", "macro_family": "", "signal": np.nan,
            "hypothese": "RANDOM_TS",
        })
    return orders


def time_shift_orders(signals, hypothese, shift_days):
    """Placebo : memes signaux, dates decalees de shift_days jours."""
    base = macro_orders(signals, hypothese)
    shifted = []
    for od in base:
        od2 = dict(od)
        od2["event_dt"] = od["event_dt"] + pd.Timedelta(days=shift_days)
        od2["hypothese"] = f"{hypothese}_SHIFT{shift_days:+d}"
        shifted.append(od2)
    return shifted


# --------------------------------------------------------------------------- #
#  AGREGATION + APPLICATION DES COUTS                                          #
# --------------------------------------------------------------------------- #
def apply_cost(raw_ret_series, cost_bps):
    """Applique un cout aller-retour (bps) au rendement brut deja oriente."""
    return raw_ret_series - (cost_bps / 1e4)


def agg_stats(ret_series):
    """Stats standard d'une serie de rendements (deja nets de cout)."""
    r = ret_series.dropna()
    n = len(r)
    if n == 0:
        return dict(n_trades=0, ret_moy_pct=np.nan, hit_rate_pct=np.nan,
                    ret_total_pct=np.nan, ret_median_pct=np.nan, std_pct=np.nan,
                    sharpe_pertrade=np.nan)
    mean = r.mean()
    std = r.std(ddof=1) if n > 1 else np.nan
    sharpe = (mean / std * np.sqrt(n)) if (std and std > 0) else np.nan
    return dict(
        n_trades=n, ret_moy_pct=mean * 100, hit_rate_pct=(r > 0).mean() * 100,
        ret_total_pct=r.sum() * 100, ret_median_pct=r.median() * 100,
        std_pct=(std * 100 if std == std else np.nan), sharpe_pertrade=sharpe,
    )


def summary_by_config(records, cost_grid=(0,)):
    """
    Resume par (model_name, hypothese, vwap_mode, wait_min, entry_method, horizon, cost_bps).
    Les couts sont appliques ici sur le rendement brut -> pas de re-backtest.
    """
    if records.empty:
        return pd.DataFrame()
    keys = ["model_name", "hypothese", "vwap_mode", "wait_min", "entry_method", "horizon"]
    out = []
    for cost in cost_grid:
        tmp = records.copy()
        tmp["net"] = apply_cost(tmp["raw_ret"], cost)
        g = tmp.groupby(keys, dropna=False)
        for kv, sub in g:
            st = agg_stats(sub["net"])
            row = dict(zip(keys, kv))
            row["cost_bps"] = cost
            row.update({
                "n_trades": st["n_trades"], "ret_moy_%": st["ret_moy_pct"],
                "hit_rate_%": st["hit_rate_pct"], "ret_total_%": st["ret_total_pct"],
                "ret_median_%": st["ret_median_pct"], "std_%": st["std_pct"],
                "sharpe_pertrade": st["sharpe_pertrade"],
            })
            out.append(row)
    return pd.DataFrame(out)


def print_table(df, title, max_rows=25):
    print(f"\n  {title}")
    print("  " + "-" * 66)
    if df is None or df.empty:
        print("  (vide)")
        return
    with pd.option_context("display.float_format", lambda v: f"{v:,.3f}",
                           "display.max_rows", max_rows, "display.width", 220):
        print(df.head(max_rows).to_string(index=False))


# --------------------------------------------------------------------------- #
#  MODELES PRINCIPAUX                                                           #
# --------------------------------------------------------------------------- #
def build_main_records(signals, px, pa=None):
    """
    Calcule les trade records pour les 3 modeles principaux x DRIFT/FADE.
      - MACRO_NO_VWAP          : entry_method="none"
      - MACRO_VWAP_CLOSE_CROSS : entry_method="close_cross" x modes x fenetres
      - MACRO_VWAP_LIMIT_TOUCH : entry_method="limit_touch" x fenetres
    Retourne (records_df, skipped_total).
    """
    if pa is None:
        pa = PA(px)
    all_records, skipped_total = [], {}

    for hyp in ["DRIFT", "FADE"]:
        orders = macro_orders(signals, hyp)

        # 1) MACRO_NO_VWAP
        rec, sk = run_engine(orders, None, "none", model_name="MACRO_NO_VWAP", pa=pa)
        all_records.append(rec)
        _merge_skip(skipped_total, sk, "MACRO_NO_VWAP")

        # 2) MACRO_VWAP_CLOSE_CROSS
        for mode in VWAP_RETURN_MODES:
            for wait in VWAP_WAIT_WINDOWS_MIN:
                rec, sk = run_engine(orders, None, "close_cross", vwap_mode=mode,
                                     wait_min=wait, model_name="MACRO_VWAP_CLOSE_CROSS", pa=pa)
                all_records.append(rec)
                _merge_skip(skipped_total, sk, "MACRO_VWAP_CLOSE_CROSS")

        # 3) MACRO_VWAP_LIMIT_TOUCH
        for wait in VWAP_WAIT_WINDOWS_MIN:
            rec, sk = run_engine(orders, None, "limit_touch", vwap_mode="touch",
                                 wait_min=wait, model_name="MACRO_VWAP_LIMIT_TOUCH", pa=pa)
            all_records.append(rec)
            _merge_skip(skipped_total, sk, "MACRO_VWAP_LIMIT_TOUCH")

    records = pd.concat([r for r in all_records if not r.empty], ignore_index=True) \
        if any(not r.empty for r in all_records) else pd.DataFrame()
    return records, skipped_total


def _merge_skip(total, sk, prefix):
    for k, v in sk.items():
        key = f"{prefix}:{k}"
        total[key] = total.get(key, 0) + v


# --------------------------------------------------------------------------- #
#  TESTS RANDOM (MONTE CARLO)                                                   #
# --------------------------------------------------------------------------- #
def run_random_tests(signals, px, best_cfg, rng, pa=None):
    """
    Lance les Monte Carlo :
      - VWAP_RANDOM_SIDE       : memes events, sens random.
      - VWAP_RANDOM_TIMESTAMPS : timestamps hors-news, sens random ET sens biaise.
    On evalue chaque run a la config VWAP de la meilleure config macro (best_cfg),
    pour comparer a iso-execution. Retourne un DataFrame long (1 ligne / run).
    """
    if pa is None:
        pa = PA(px)
    method = best_cfg["entry_method"]
    mode = best_cfg["vwap_mode"] if best_cfg["vwap_mode"] else None
    wait = int(best_cfg["wait_min"])
    horizon = best_cfg["horizon"]
    cost = 0

    macro_long_share = float((signals["signal"] > 0).mean())
    rows = []
    n_orders = len(signals)

    for run_id in range(N_RANDOM_RUNS):
        # RANDOM_SIDE
        orders = random_side_orders(signals, rng)
        rec, _ = run_engine(orders, None, method, vwap_mode=mode, wait_min=wait,
                            model_name="VWAP_RANDOM_SIDE", pa=pa)
        rows.append(_mc_row("RANDOM_SIDE", run_id, "VWAP_RANDOM_SIDE", rec, horizon, cost))
        # RANDOM_TIMESTAMPS (sens random)
        orders = random_timestamp_orders(px, n_orders, rng, side_dist=None)
        rec, _ = run_engine(orders, None, method, vwap_mode=mode, wait_min=wait,
                            model_name="VWAP_RANDOM_TS", pa=pa)
        rows.append(_mc_row("RANDOM_TS_RANDSIDE", run_id, "VWAP_RANDOM_TS", rec, horizon, cost))
        # RANDOM_TIMESTAMPS (sens biaise comme la macro)
        orders = random_timestamp_orders(px, n_orders, rng, side_dist=macro_long_share)
        rec, _ = run_engine(orders, None, method, vwap_mode=mode, wait_min=wait,
                            model_name="VWAP_RANDOM_TS_BIASED", pa=pa)
        rows.append(_mc_row("RANDOM_TS_BIASEDSIDE", run_id, "VWAP_RANDOM_TS_BIASED", rec, horizon, cost))

    return pd.DataFrame(rows)


def _mc_row(test_type, run_id, model_name, rec, horizon, cost):
    sub = rec[rec["horizon"] == horizon] if not rec.empty else rec
    st = agg_stats(apply_cost(sub["raw_ret"], cost)) if not sub.empty else agg_stats(pd.Series([], dtype=float))
    return {
        "random_test_type": test_type, "run_id": run_id, "model_name": model_name,
        "horizon": horizon, "cost_bps": cost, "n_trades": st["n_trades"],
        "ret_moy_%": st["ret_moy_pct"], "hit_rate_%": st["hit_rate_pct"],
        "ret_total_%": st["ret_total_pct"], "ret_median_%": st["ret_median_pct"],
        "sharpe_pertrade": st["sharpe_pertrade"],
    }


def percentile_of(value, distribution):
    """Percentile (0-100) de `value` dans `distribution`."""
    d = np.asarray([x for x in distribution if x == x], dtype=float)
    if len(d) == 0 or value != value:
        return np.nan
    return (d < value).mean() * 100.0


# --------------------------------------------------------------------------- #
#  PLACEBO TIME-SHIFT                                                           #
# --------------------------------------------------------------------------- #
def run_time_shift(signals, px, best_cfg, pa=None):
    """
    Recompute les records macro avec dates decalees de +/-1 jour,
    a la meme config VWAP que la meilleure config macro reelle.
    Retourne un DataFrame de records (model_name=MACRO_TIME_SHIFT_PLACEBO).
    """
    if pa is None:
        pa = PA(px)
    method = best_cfg["entry_method"]
    mode = best_cfg["vwap_mode"] if best_cfg["vwap_mode"] else None
    wait = int(best_cfg["wait_min"])
    hyp = best_cfg["hypothese"]
    # le placebo n'a de sens que sur une hypothese macro (DRIFT/FADE)
    if hyp not in ("DRIFT", "FADE"):
        hyp = "DRIFT"

    recs = []
    for shift in SHIFT_DAYS:
        orders = time_shift_orders(signals, hyp, shift)
        rec, _ = run_engine(orders, None, method, vwap_mode=mode, wait_min=wait,
                            model_name="MACRO_TIME_SHIFT_PLACEBO", pa=pa)
        if not rec.empty:
            rec["shift_days"] = shift
            recs.append(rec)
    return pd.concat(recs, ignore_index=True) if recs else pd.DataFrame()


# --------------------------------------------------------------------------- #
#  SELECTION DE CONFIG + TRAIN/TEST + WALK-FORWARD                              #
# --------------------------------------------------------------------------- #
def pick_best_config(records, cost_bps=0, min_trades=MIN_TRADES_FOR_CONFIG,
                     models=None):
    """
    Choisit la meilleure config (par Sharpe) sur un set de records donne.
    Filtre n_trades >= min_trades. Optionnellement restreint a `models`.
    Retourne un dict de config (ou None).
    """
    rec = records if models is None else records[records["model_name"].isin(models)]
    summ = summary_by_config(rec, cost_grid=[cost_bps])
    if summ.empty:
        return None
    elig = summ[summ["n_trades"] >= min_trades].dropna(subset=["sharpe_pertrade"])
    if elig.empty:
        elig = summ.dropna(subset=["sharpe_pertrade"])
    if elig.empty:
        return None
    best = elig.sort_values("sharpe_pertrade", ascending=False).iloc[0]
    return best.to_dict()


def filter_records_by_config(records, cfg):
    """Sous-ensemble de records correspondant a une config (sans le cout)."""
    m = (records["model_name"] == cfg["model_name"]) & \
        (records["hypothese"] == cfg["hypothese"]) & \
        (records["entry_method"] == cfg["entry_method"]) & \
        (records["horizon"] == cfg["horizon"]) & \
        (records["wait_min"] == cfg["wait_min"])
    vm = cfg["vwap_mode"]
    if vm == "" or pd.isna(vm):
        m &= (records["vwap_mode"].isin(["", np.nan]) | records["vwap_mode"].isna())
    else:
        m &= (records["vwap_mode"] == vm)
    return records[m]


def run_train_test(records, cost_bps=0):
    """
    Split chronologique 70/30 sur les dates d'events.
    Selectionne la meilleure config sur le TRAIN, l'applique sur le TEST.
    Retourne (df_resultat, dict_resume).
    """
    if records.empty:
        return pd.DataFrame(), {}
    dates = np.sort(records["event_date"].unique())
    cut = dates[int(len(dates) * TRAIN_RATIO)] if len(dates) > 2 else dates[-1]
    train = records[records["event_date"] < cut]
    test = records[records["event_date"] >= cut]

    cfg = pick_best_config(train, cost_bps=cost_bps)
    if cfg is None:
        return pd.DataFrame(), {}

    tr_rec = filter_records_by_config(train, cfg)
    te_rec = filter_records_by_config(test, cfg)
    tr_stats = agg_stats(apply_cost(tr_rec["raw_ret"], cost_bps))
    te_stats = agg_stats(apply_cost(te_rec["raw_ret"], cost_bps))

    rows = [
        _tt_row("TRAIN", cfg, tr_stats),
        _tt_row("TEST", cfg, te_stats),
    ]
    df = pd.DataFrame(rows)
    resume = {
        "cut_date": pd.Timestamp(cut),
        "config": cfg,
        "train": tr_stats, "test": te_stats,
        "sharpe_drop": (tr_stats["sharpe_pertrade"] - te_stats["sharpe_pertrade"]),
    }
    return df, resume


def _tt_row(split, cfg, st):
    return {
        "split": split, "model_name": cfg["model_name"], "hypothese": cfg["hypothese"],
        "vwap_mode": cfg["vwap_mode"], "wait_min": cfg["wait_min"],
        "entry_method": cfg["entry_method"], "horizon": cfg["horizon"],
        "n_trades": st["n_trades"], "ret_moy_%": st["ret_moy_pct"],
        "hit_rate_%": st["hit_rate_pct"], "ret_total_%": st["ret_total_pct"],
        "ret_median_%": st["ret_median_pct"], "sharpe_pertrade": st["sharpe_pertrade"],
    }


def run_walk_forward(records, cost_bps=0):
    """
    Pour chaque annee de test : choisir la meilleure config sur TOUTES les annees
    precedentes, puis tester sur l'annee. Retourne un DataFrame par annee.
    """
    if records.empty:
        return pd.DataFrame()
    years = sorted(records["year"].unique())
    rows = []
    for i, ty in enumerate(years):
        if i == 0:
            continue  # pas d'historique pour la 1ere annee
        train = records[records["year"] < ty]
        test = records[records["year"] == ty]
        cfg = pick_best_config(train, cost_bps=cost_bps)
        if cfg is None:
            continue
        te_rec = filter_records_by_config(test, cfg)
        st = agg_stats(apply_cost(te_rec["raw_ret"], cost_bps))
        rows.append({
            "test_year": ty, "chosen_model": cfg["model_name"],
            "chosen_hypothese": cfg["hypothese"], "chosen_vwap_mode": cfg["vwap_mode"],
            "chosen_wait_min": cfg["wait_min"], "chosen_horizon": cfg["horizon"],
            "n_trades": st["n_trades"], "ret_moy_%": st["ret_moy_pct"],
            "hit_rate_%": st["hit_rate_pct"], "ret_total_%": st["ret_total_pct"],
            "ret_median_%": st["ret_median_pct"], "sharpe_pertrade": st["sharpe_pertrade"],
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
#  DIAGNOSTICS                                                                  #
# --------------------------------------------------------------------------- #
def build_diagnostics(records):
    """Compte les modes d'entree, retours VWAP, delais, retours nuls, etc."""
    if records.empty:
        return pd.DataFrame([{"diagnostic": "AUCUN_TRADE", "valeur": 0}])
    d = {}
    # par entry_mode
    for k, v in records["entry_mode"].value_counts().items():
        d[f"entry_mode::{k}"] = int(v)
    # par raison VWAP
    for k, v in records["vwap_entry_reason"].value_counts().items():
        d[f"vwap_reason::{k}"] = int(v)
    # retours a zero (rendement brut exactement nul)
    d["pct_retours_zero_%"] = round((records["raw_ret"] == 0).mean() * 100, 3)
    # delais
    d["entry_delay_moyen_min"] = round(records["entry_delay_min"].mean(), 2)
    d["entry_delay_median_min"] = round(records["entry_delay_min"].median(), 2)
    # temps d'attente avant retour VWAP (>0 seulement)
    wait_pos = records.loc[records["wait_eff_min"] > 0, "wait_eff_min"]
    d["wait_vwap_moyen_min"] = round(wait_pos.mean(), 2) if len(wait_pos) else 0.0
    d["wait_vwap_median_min"] = round(wait_pos.median(), 2) if len(wait_pos) else 0.0
    return pd.DataFrame([{"diagnostic": k, "valeur": v} for k, v in d.items()])




# =========================================================================== #
#  COUCHE BATCH MULTI-PAYS / MULTI-ACTIONS                                     #
# =========================================================================== #

def ask_paths(prompt, filetypes=None, title="Selectionne des fichiers"):
    """
    Selection MULTIPLE de fichiers (tkinter). Repli : saisie manuelle de chemins
    separes par des virgules, OU d'un motif glob (ex: /data/US/*.csv).
    Retourne une liste de chemins valides (peut etre vide).
    """
    print(prompt)
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        ft = filetypes or [("Tous les fichiers", "*.*")]
        paths = filedialog.askopenfilenames(title=title, filetypes=ft)
        root.update()
        root.destroy()
        paths = [p for p in paths if os.path.isfile(p)]
        if paths:
            print(f"    {len(paths)} fichier(s) selectionne(s).")
            return list(paths)
        print("  -> selection annulee/vide, passe en saisie manuelle.")
    except Exception:
        print("  -> pas d'interface graphique, passe en saisie manuelle.")

    # repli manuel : chemins separes par des virgules, ou motif glob, ou vide pour passer
    raw = input("  > Chemins CSV (separes par des virgules) ou motif glob (vide=passer) : ").strip()
    if not raw:
        return []
    out = []
    for part in raw.split(","):
        part = part.strip().strip('"').strip("'")
        if not part:
            continue
        part = os.path.expanduser(part)
        if any(ch in part for ch in "*?[]"):
            out.extend(sorted(glob.glob(part)))
        elif os.path.isfile(part):
            out.append(part)
        else:
            print(f"    -> introuvable, ignore : {part}")
    return [p for p in out if os.path.isfile(p)]


def extract_ticker(path):
    """
    Extrait un ticker depuis le nom de fichier, en MAJUSCULES.
    Exemples :
      'sam_dataset.csv'                 -> SAM
      'LMB_1min.csv'                    -> LMB
      'lmb_dataset_London-Strategic'    -> LONDON-STRATEGIC (apres prefixe connu)
      nom complique                     -> nom de fichier sans extension, uppercase.
    """
    base = os.path.splitext(os.path.basename(path))[0]
    # prefixe connu "lmb_dataset_XXX" -> garder la partie utile
    m = re.match(r"(?:lmb_dataset[_-]?)(.+)", base, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip("_- ").upper()
    # 1er token avant un separateur (_, espace, tiret) ou un suffixe type "1min", "dataset"
    # ex: 'sam_dataset' -> SAM ; 'LMB_1min' -> LMB ; 'AAPL-minute' -> AAPL
    m = re.match(r"([A-Za-z0-9\.]+?)(?:[_\s\-].*)?$", base)
    if m and m.group(1):
        return m.group(1).upper()
    return base.upper()


# --------------------------------------------------------------------------- #
#  TRAITEMENT D'UNE ACTION (toute la robustesse condensee en 1 dict)           #
# --------------------------------------------------------------------------- #
def process_action(signals, px, country, ticker, price_file, rng):
    """
    Lance toute la batterie sur UNE action et retourne :
      (master_row, configs_rows, random_rows, tt_rows, wf_rows, all_trades_or_None)
    Robuste : en cas de donnees insuffisantes -> classification INSUFFICIENT_DATA.
    """
    pa = PA(px)

    # --- records principaux (NO_VWAP / CLOSE_CROSS / LIMIT_TOUCH) ---
    records, skipped = build_main_records(signals, px, pa=pa)
    n_traded = records["event_date"].nunique() if not records.empty else 0

    base_master = {
        "country": country, "ticker": ticker, "price_file": os.path.basename(price_file),
        "start_price_date": str(px["timestamp"].min()), "end_price_date": str(px["timestamp"].max()),
        "n_price_bars": len(px), "n_releases_retained": len(signals),
        "n_releases_traded": n_traded, "error_message": "",
    }

    # donnees insuffisantes -> on sort tot
    if records.empty or len(records) < MIN_TRADES_FOR_ACTION:
        row = dict(base_master)
        row.update(_empty_master_fields())
        row["classification"] = "INSUFFICIENT_DATA"
        row["confidence_score"] = 0
        row["main_warning"] = "Pas assez de trades pour evaluer."
        row["interpretation_short"] = "Donnees insuffisantes."
        return row, [], [], [], [], None

    summary = summary_by_config(records, cost_grid=COST_BPS_GRID)

    # --- baseline macro (NO_VWAP) ---
    base = summary[(summary["model_name"] == "MACRO_NO_VWAP") & (summary["cost_bps"] == 0)]
    base = base.dropna(subset=["sharpe_pertrade"]).sort_values("sharpe_pertrade", ascending=False)
    baseline = base.iloc[0] if not base.empty else None

    # --- meilleure config macro+VWAP optimiste (close_cross + limit_touch) ---
    best_cfg = pick_best_config(records, cost_bps=0,
                                models=["MACRO_VWAP_CLOSE_CROSS", "MACRO_VWAP_LIMIT_TOUCH"])
    if best_cfg is None:
        best_cfg = pick_best_config(records, cost_bps=0)

    # --- meilleure config limit_touch (conservatrice) ---
    lt_cfg = pick_best_config(records, cost_bps=0, models=["MACRO_VWAP_LIMIT_TOUCH"])

    # --- random tests (allege) ---
    random_df = run_random_tests_light(signals, px, best_cfg, rng, pa=pa)
    rs = random_df[random_df["random_test_type"] == "RANDOM_SIDE"]["ret_moy_%"].values
    rts = random_df[random_df["random_test_type"] == "RANDOM_TS_RANDSIDE"]["ret_moy_%"].values
    true_ret = best_cfg["ret_moy_%"]
    rs_pct = percentile_of(true_ret, rs)
    rts_pct = percentile_of(true_ret, rts)

    # --- placebo time-shift ---
    shift_records = run_time_shift(signals, px, best_cfg, pa=pa)
    shift_vals = {}
    for sh in SHIFT_DAYS:
        sr = shift_records[(shift_records.get("shift_days") == sh) &
                           (shift_records["horizon"] == best_cfg["horizon"])] \
            if not shift_records.empty else pd.DataFrame()
        st = agg_stats(sr["raw_ret"]) if not sr.empty else None
        shift_vals[sh] = st["ret_moy_pct"] if st else np.nan
    # decay score : a quel point les shifts sont plus faibles que le vrai (positif = bon)
    shift_max = np.nanmax([abs(v) for v in shift_vals.values()]) if shift_vals else np.nan
    decay_score = (true_ret - shift_max) / abs(true_ret) if (true_ret and true_ret == true_ret and true_ret != 0) else np.nan

    # --- couts ---
    bc_rec = filter_records_by_config(records, best_cfg)
    cost_break = None
    cost_rets = {}
    for c in COST_BPS_GRID:
        rm = apply_cost(bc_rec["raw_ret"], c).mean() * 100
        cost_rets[c] = rm
        if cost_break is None and rm < 0:
            cost_break = c
    if cost_break is None:
        cost_break = COST_BPS_GRID[-1] + 1  # survit a tout le grid

    # --- train/test ---
    tt_df, tt_resume = run_train_test(records, cost_bps=0)
    tr = tt_resume.get("train") if tt_resume else None
    te = tt_resume.get("test") if tt_resume else None

    # --- walk-forward ---
    wf_df = run_walk_forward(records, cost_bps=0)
    wf_years = len(wf_df)
    wf_pos = int((wf_df["ret_moy_%"] > 0).sum()) if not wf_df.empty else 0
    wf_ratio = (wf_pos / wf_years) if wf_years else np.nan
    worst_year = worst_ret = np.nan
    concentration_warn = ""
    if not wf_df.empty:
        worst = wf_df.sort_values("ret_moy_%").iloc[0]
        worst_year, worst_ret = int(worst["test_year"]), worst["ret_moy_%"]
        tot = wf_df["ret_total_%"].sum()
        if tot and tot == tot:
            top = wf_df.sort_values("ret_total_%", ascending=False).iloc[0]
            share = top["ret_total_%"] / tot
            if share == share and share > 0.7:
                concentration_warn = f"~{share*100:.0f}% perf sur {int(top['test_year'])}"

    # --- diagnostics ---
    diag = build_diagnostics(records)
    diag_map = dict(zip(diag["diagnostic"], diag["valeur"]))
    n_preopen = diag_map.get("entry_mode::PRE_OPEN_SAME_DAY", 0)
    n_intraday = diag_map.get("entry_mode::INTRADAY", 0)
    n_tot_modes = max(n_preopen + n_intraday, 1)
    pct_preopen = 100.0 * n_preopen / n_tot_modes
    pct_intraday = 100.0 * n_intraday / n_tot_modes

    # --- assemblage de la ligne maitre ---
    row = dict(base_master)
    row.update({
        # baseline
        "baseline_best_model": "MACRO_NO_VWAP",
        "baseline_best_hypothese": baseline["hypothese"] if baseline is not None else "",
        "baseline_best_horizon": baseline["horizon"] if baseline is not None else "",
        "baseline_ret_moy_pct": baseline["ret_moy_%"] if baseline is not None else np.nan,
        "baseline_sharpe": baseline["sharpe_pertrade"] if baseline is not None else np.nan,
        "baseline_n_trades": int(baseline["n_trades"]) if baseline is not None else 0,
        # best optimiste
        "best_model": best_cfg["model_name"], "best_hypothese": best_cfg["hypothese"],
        "best_vwap_mode": best_cfg["vwap_mode"], "best_wait_min": best_cfg["wait_min"],
        "best_horizon": best_cfg["horizon"], "best_ret_moy_pct": best_cfg["ret_moy_%"],
        "best_hit_rate_pct": best_cfg["hit_rate_%"], "best_sharpe": best_cfg["sharpe_pertrade"],
        "best_n_trades": int(best_cfg["n_trades"]),
        # limit touch
        "limit_touch_best_ret_moy_pct": lt_cfg["ret_moy_%"] if lt_cfg else np.nan,
        "limit_touch_best_sharpe": lt_cfg["sharpe_pertrade"] if lt_cfg else np.nan,
        "limit_touch_best_horizon": lt_cfg["horizon"] if lt_cfg else "",
        "limit_touch_best_wait_min": lt_cfg["wait_min"] if lt_cfg else np.nan,
        # random
        "random_side_median_ret_pct": float(np.nanmedian(rs)) if len(rs) else np.nan,
        "random_side_p95_ret_pct": float(np.nanpercentile(rs, 95)) if len(rs) else np.nan,
        "random_side_percentile": rs_pct,
        "random_ts_median_ret_pct": float(np.nanmedian(rts)) if len(rts) else np.nan,
        "random_ts_p95_ret_pct": float(np.nanpercentile(rts, 95)) if len(rts) else np.nan,
        "random_ts_percentile": rts_pct,
        # placebo
        "shift_minus_1_ret_pct": shift_vals.get(-1, np.nan),
        "shift_plus_1_ret_pct": shift_vals.get(+1, np.nan),
        "time_shift_decay_score": decay_score,
        "placebo_warning": "shift reste fort" if (decay_score == decay_score and decay_score < 0.3) else "",
        # couts
        "cost_break_even_bps": cost_break,
        "ret_after_10bps_pct": cost_rets.get(10, np.nan),
        "ret_after_20bps_pct": cost_rets.get(20, np.nan),
        "ret_after_30bps_pct": cost_rets.get(30, np.nan),
        # train/test
        "train_ret_moy_pct": tr["ret_moy_pct"] if tr else np.nan,
        "train_sharpe": tr["sharpe_pertrade"] if tr else np.nan,
        "test_ret_moy_pct": te["ret_moy_pct"] if te else np.nan,
        "test_sharpe": te["sharpe_pertrade"] if te else np.nan,
        "train_test_decay": (tr["sharpe_pertrade"] - te["sharpe_pertrade"]) if (tr and te) else np.nan,
        "train_test_warning": "",
        # walk-forward
        "walk_forward_years": wf_years, "walk_forward_positive_years": wf_pos,
        "walk_forward_positive_ratio": wf_ratio,
        "worst_walk_forward_year": worst_year, "worst_walk_forward_ret_pct": worst_ret,
        "perf_concentration_warning": concentration_warn,
        # diagnostics
        "pct_preopen_entries": round(pct_preopen, 1), "pct_intraday_entries": round(pct_intraday, 1),
        "pct_zero_returns": diag_map.get("pct_retours_zero_%", np.nan),
        "median_entry_delay_min": diag_map.get("entry_delay_median_min", np.nan),
        "median_vwap_wait_min": diag_map.get("wait_vwap_median_min", np.nan),
    })
    # warning train/test
    if te and (te["ret_moy_pct"] != te["ret_moy_pct"] or te["ret_moy_pct"] < 0):
        row["train_test_warning"] = "TEST <= 0 (overfit probable)"
    elif tr and te and te["sharpe_pertrade"] == te["sharpe_pertrade"] and \
            te["sharpe_pertrade"] < 0.5 * (tr["sharpe_pertrade"] or 1):
        row["train_test_warning"] = "Sharpe TEST s'effondre"

    # --- classification + score ---
    cls, score, warn, interp = classify_action(row)
    row["classification"] = cls
    row["confidence_score"] = score
    row["main_warning"] = warn
    row["interpretation_short"] = interp

    # --- rows annexes pour exports ---
    cfg_rows = _config_rows(summary, country, ticker)
    rnd_rows = _random_rows(random_df, country, ticker)
    tt_rows = _tt_export_rows(tt_df, country, ticker)
    wf_rows = _wf_export_rows(wf_df, country, ticker)
    trades = None
    if EXPORT_ALL_TRADES:
        bc_rec2 = bc_rec.copy()
        bc_rec2.insert(0, "ticker", ticker)
        bc_rec2.insert(0, "country", country)
        trades = bc_rec2

    return row, cfg_rows, rnd_rows, tt_rows, wf_rows, trades


def run_random_tests_light(signals, px, best_cfg, rng, pa=None):
    """Version allegee : RANDOM_SIDE + RANDOM_TS_RANDSIDE seulement (pas le biaise)."""
    if pa is None:
        pa = PA(px)
    method = best_cfg["entry_method"]
    mode = best_cfg["vwap_mode"] if best_cfg["vwap_mode"] else None
    wait = int(best_cfg["wait_min"])
    horizon = best_cfg["horizon"]
    rows = []
    n_orders = len(signals)
    for run_id in range(N_RANDOM_RUNS):
        orders = random_side_orders(signals, rng)
        rec, _ = run_engine(orders, None, method, vwap_mode=mode, wait_min=wait,
                            model_name="VWAP_RANDOM_SIDE", pa=pa)
        rows.append(_mc_row("RANDOM_SIDE", run_id, "VWAP_RANDOM_SIDE", rec, horizon, 0))
        orders = random_timestamp_orders(px, n_orders, rng, side_dist=None)
        rec, _ = run_engine(orders, None, method, vwap_mode=mode, wait_min=wait,
                            model_name="VWAP_RANDOM_TS", pa=pa)
        rows.append(_mc_row("RANDOM_TS_RANDSIDE", run_id, "VWAP_RANDOM_TS", rec, horizon, 0))
    return pd.DataFrame(rows)


def _empty_master_fields():
    """Champs maitres vides pour les actions a donnees insuffisantes."""
    keys = [
        "baseline_best_model", "baseline_best_hypothese", "baseline_best_horizon",
        "baseline_ret_moy_pct", "baseline_sharpe", "baseline_n_trades",
        "best_model", "best_hypothese", "best_vwap_mode", "best_wait_min", "best_horizon",
        "best_ret_moy_pct", "best_hit_rate_pct", "best_sharpe", "best_n_trades",
        "limit_touch_best_ret_moy_pct", "limit_touch_best_sharpe",
        "limit_touch_best_horizon", "limit_touch_best_wait_min",
        "random_side_median_ret_pct", "random_side_p95_ret_pct", "random_side_percentile",
        "random_ts_median_ret_pct", "random_ts_p95_ret_pct", "random_ts_percentile",
        "shift_minus_1_ret_pct", "shift_plus_1_ret_pct", "time_shift_decay_score",
        "placebo_warning", "cost_break_even_bps", "ret_after_10bps_pct",
        "ret_after_20bps_pct", "ret_after_30bps_pct", "train_ret_moy_pct", "train_sharpe",
        "test_ret_moy_pct", "test_sharpe", "train_test_decay", "train_test_warning",
        "walk_forward_years", "walk_forward_positive_years", "walk_forward_positive_ratio",
        "worst_walk_forward_year", "worst_walk_forward_ret_pct", "perf_concentration_warning",
        "pct_preopen_entries", "pct_intraday_entries", "pct_zero_returns",
        "median_entry_delay_min", "median_vwap_wait_min",
    ]
    return {k: np.nan for k in keys}


# --------------------------------------------------------------------------- #
#  CLASSIFICATION AUTOMATIQUE                                                   #
# --------------------------------------------------------------------------- #
def classify_action(row):
    """
    Classe une action en A/B/C/D et calcule un confidence_score (0-100).
    Retourne (classification, score, main_warning, interpretation_short).
    Logique indicative (pas un oracle) : voir cahier des charges.
    """
    def g(k, default=np.nan):
        v = row.get(k, default)
        return v if v is not None else default

    best_ret = g("best_ret_moy_pct")
    best_sharpe = g("best_sharpe")
    rs_pct = g("random_side_percentile")
    rts_pct = g("random_ts_percentile")
    decay = g("time_shift_decay_score")
    test_ret = g("test_ret_moy_pct")
    wf_ratio = g("walk_forward_positive_ratio")
    cost_be = g("cost_break_even_bps")
    lt_ret = g("limit_touch_best_ret_moy_pct")
    pct_preopen = g("pct_preopen_entries")
    concentration = str(g("perf_concentration_warning", "") or "")

    def ok(v):
        return v == v and v is not None  # not NaN

    # ----- score 0..100 (somme de composantes ponderees) -----
    score = 0.0
    # random side (le plus discriminant) : 0..25
    if ok(rs_pct):
        score += np.clip((rs_pct - 50) / 50, 0, 1) * 25
    # random ts : 0..10
    if ok(rts_pct):
        score += np.clip((rts_pct - 50) / 50, 0, 1) * 10
    # time-shift decay : 0..15
    if ok(decay):
        score += np.clip(decay, 0, 1) * 15
    # test positif + sharpe : 0..20
    if ok(test_ret) and test_ret > 0:
        score += 12
        if ok(best_sharpe):
            score += np.clip(best_sharpe / 4, 0, 1) * 8
    # walk-forward : 0..12
    if ok(wf_ratio):
        score += np.clip(wf_ratio, 0, 1) * 12
    # limit_touch positif : 0..10
    if ok(lt_ret) and lt_ret > 0:
        score += 10
    # cost break-even : 0..8
    if ok(cost_be):
        score += np.clip(cost_be / 30, 0, 1) * 8

    # ----- penalites -----
    if concentration:
        score -= 8
    if ok(pct_preopen) and pct_preopen > 90:
        score -= 6
    if ok(rs_pct) and rs_pct < 80:
        score -= 10          # random side presque aussi bon -> direction macro douteuse
    if ok(test_ret) and test_ret < 0:
        score -= 12
    if ok(cost_be) and cost_be < 5:
        score -= 8

    score = float(np.clip(score, 0, 100))

    # ----- classification -----
    # conditions A
    cond_A = all([
        ok(best_ret) and best_ret > 0,
        ok(best_sharpe) and best_sharpe > CLS_SHARPE_MIN,
        ok(rs_pct) and rs_pct >= CLS_RANDOM_PCT_MIN,
        ok(rts_pct) and rts_pct >= CLS_RANDOM_PCT_MIN,
        ok(decay) and decay > 0.3,
        ok(test_ret) and test_ret > 0,
        ok(wf_ratio) and wf_ratio >= CLS_WF_POS_RATIO_MIN,
        ok(cost_be) and cost_be >= CLS_COST_BREAKEVEN_MIN,
        ok(lt_ret) and lt_ret > 0,
    ])
    # signature "VWAP-driven" : random side faible OU time-shift reste fort
    vwap_driven = (ok(rs_pct) and rs_pct < 80) or (ok(decay) and decay < 0.3)
    # signature "rejet" : test <=0, ne bat pas random ts, couts tuent tout, sharpe faible
    cond_D = any([
        (ok(test_ret) and test_ret <= 0),
        (ok(rts_pct) and rts_pct < 80),
        (ok(cost_be) and cost_be < 5),
        (ok(best_sharpe) and best_sharpe < 1.0),
    ])

    if cond_A:
        cls = "A_CLEAN_MACRO_SIGNAL"
        interp = "Signal macro propre, robuste, execution VWAP credible."
        warn = ""
    elif ok(best_ret) and best_ret > 0 and vwap_driven and not cond_D:
        cls = "C_VWAP_DRIVEN_OR_SUSPECT"
        interp = "Edge surtout VWAP/intraday, peu lie a la direction macro."
        warn = "random side proche du vrai modele ou time-shift fort."
    elif cond_D:
        cls = "D_REJECT"
        interp = "Fragile : test faible/negatif, couts, ou ne bat pas random."
        warn = "ne survit pas a un ou plusieurs tests cles."
    else:
        cls = "B_INTERESTING_BUT_FRAGILE"
        interp = "Resultat brut correct mais 1-2 faiblesses (cout/test/WF/limit)."
        warn = "a confirmer avant tout deploiement."

    # warning principal le plus parlant
    main_warn = warn
    if concentration:
        main_warn = (main_warn + " | " if main_warn else "") + concentration
    if ok(pct_preopen) and pct_preopen > 90:
        main_warn = (main_warn + " | " if main_warn else "") + "PRE_OPEN dominant"

    return cls, round(score), main_warn, interp


# --------------------------------------------------------------------------- #
#  HELPERS D'EXPORT (lignes annexes)                                           #
# --------------------------------------------------------------------------- #
def _config_rows(summary, country, ticker):
    """Toutes les configs agregees d'une action (pour batch_all_configs_summary)."""
    if summary.empty:
        return []
    s = summary.copy()
    s.insert(0, "ticker", ticker)
    s.insert(0, "country", country)
    keep = ["country", "ticker", "model_name", "hypothese", "vwap_mode", "wait_min",
            "horizon", "cost_bps", "n_trades", "ret_moy_%", "hit_rate_%",
            "ret_median_%", "sharpe_pertrade"]
    s = s[keep].rename(columns={
        "ret_moy_%": "ret_moy_pct", "hit_rate_%": "hit_rate_pct",
        "ret_median_%": "ret_median_pct"})
    return s.to_dict("records")


def _random_rows(random_df, country, ticker):
    if random_df.empty:
        return []
    r = random_df.copy()
    r.insert(0, "ticker", ticker)
    r.insert(0, "country", country)
    return r.to_dict("records")


def _tt_export_rows(tt_df, country, ticker):
    if tt_df is None or tt_df.empty:
        return []
    t = tt_df.copy()
    t.insert(0, "ticker", ticker)
    t.insert(0, "country", country)
    return t.to_dict("records")


def _wf_export_rows(wf_df, country, ticker):
    if wf_df is None or wf_df.empty:
        return []
    w = wf_df.copy()
    w.insert(0, "ticker", ticker)
    w.insert(0, "country", country)
    return w.to_dict("records")


# --------------------------------------------------------------------------- #
#  AGREGATION PAR PAYS                                                          #
# --------------------------------------------------------------------------- #
def build_country_summary(master_df):
    """Une ligne par pays a partir du tableau maitre."""
    rows = []
    for country, sub in master_df.groupby("country"):
        n = len(sub)
        nA = (sub["classification"] == "A_CLEAN_MACRO_SIGNAL").sum()
        nB = (sub["classification"] == "B_INTERESTING_BUT_FRAGILE").sum()
        nC = (sub["classification"] == "C_VWAP_DRIVEN_OR_SUSPECT").sum()
        nD = (sub["classification"].isin(["D_REJECT", "INSUFFICIENT_DATA"])).sum()
        valid = sub.dropna(subset=["best_ret_moy_pct"])
        # meilleure / pire action par confidence puis test_ret
        ranked = sub.sort_values(["confidence_score", "test_ret_moy_pct"], ascending=False)
        best_t = ranked.iloc[0]["ticker"] if not ranked.empty else ""
        worst_t = ranked.iloc[-1]["ticker"] if not ranked.empty else ""
        comment = _country_comment(nA, nB, nC, nD, n)
        rows.append({
            "country": country, "n_actions_tested": n,
            "n_A_clean_signals": int(nA), "n_B_interesting": int(nB),
            "n_C_vwap_driven_or_fragile": int(nC), "n_D_rejected": int(nD),
            "avg_best_ret_moy_pct": valid["best_ret_moy_pct"].mean() if not valid.empty else np.nan,
            "median_best_ret_moy_pct": valid["best_ret_moy_pct"].median() if not valid.empty else np.nan,
            "avg_test_ret_moy_pct": sub["test_ret_moy_pct"].mean(),
            "avg_cost_break_even_bps": sub["cost_break_even_bps"].mean(),
            "best_ticker": best_t, "worst_ticker": worst_t,
            "country_comment": comment,
        })
    return pd.DataFrame(rows)


def _country_comment(nA, nB, nC, nD, n):
    if nA >= 1:
        return f"{nA} signal(s) propre(s) -> a creuser en priorite."
    if nC >= max(1, n // 2):
        return "Majorite VWAP-driven -> edge peu specifique a la macro."
    if nD >= max(1, n // 2):
        return "Majorite rejetee -> pays peu porteur sur ce framework."
    return "Resultats mitiges -> a confirmer."


# --------------------------------------------------------------------------- #
#  RAPPORT CONSOLE GLOBAL                                                       #
# --------------------------------------------------------------------------- #
def print_global_report(master_df, country):
    """Rapport console pour un seul pays."""
    banner(f"RAPPORT GLOBAL — {country} ({len(master_df)} actions)")

    # 1) resume global
    cls_counts = master_df["classification"].value_counts().to_dict()
    nA = cls_counts.get("A_CLEAN_MACRO_SIGNAL", 0)
    nB = cls_counts.get("B_INTERESTING_BUT_FRAGILE", 0)
    nC = cls_counts.get("C_VWAP_DRIVEN_OR_SUSPECT", 0)
    nD = cls_counts.get("D_REJECT", 0)
    nINS = cls_counts.get("INSUFFICIENT_DATA", 0)
    print(f"\n  [1] RESUME GLOBAL")
    print(f"    Pays teste         : {country}")
    print(f"    Actions testees    : {len(master_df)}")
    print(f"    A (signal propre)  : {nA}")
    print(f"    B (fragile)        : {nB}")
    print(f"    C (VWAP-driven)    : {nC}")
    print(f"    D (rejet)          : {nD}")
    print(f"    INSUFFICIENT_DATA  : {nINS}")

    # 2) top 10 actions
    print(f"\n  [2] TOP 10 ACTIONS (par confidence_score puis test_ret)")
    top = master_df.sort_values(["confidence_score", "test_ret_moy_pct"],
                                ascending=False).head(10)
    cols = ["ticker", "classification", "best_hypothese", "best_vwap_mode",
            "best_horizon", "best_ret_moy_pct", "test_ret_moy_pct",
            "random_side_percentile", "random_ts_percentile",
            "cost_break_even_bps", "confidence_score"]
    cols = [c for c in cols if c in top.columns]
    print_table(top[cols], "Meilleures actions", max_rows=10)

    # 3) actions rejetees
    print(f"\n  [3] ACTIONS REJETEES (D / INSUFFICIENT_DATA)")
    rej = master_df[master_df["classification"].isin(["D_REJECT", "INSUFFICIENT_DATA"])]
    if rej.empty:
        print("    (aucune)")
    else:
        rcols = ["ticker", "classification", "best_ret_moy_pct", "test_ret_moy_pct",
                 "main_warning", "error_message"]
        rcols = [c for c in rcols if c in rej.columns]
        print_table(rej[rcols], "Rejets", max_rows=40)

    # 4) warnings globaux
    print(f"\n  [4] WARNINGS GLOBAUX")
    valid = master_df.dropna(subset=["best_ret_moy_pct"]) \
        if "best_ret_moy_pct" in master_df else master_df.iloc[0:0]
    fired = False
    if "pct_preopen_entries" in master_df:
        share_preopen = (master_df["pct_preopen_entries"] > 90).mean()
        if share_preopen > 0.5:
            fired = True
            print(f"    [!] {share_preopen*100:.0f}% des actions ont PRE_OPEN_SAME_DAY dominant :")
            print(f"        ce test ressemble plus a 'jour de news + VWAP' qu'a une vraie")
            print(f"        reaction minute par minute. Les news US sortent avant l'open.")
    if not valid.empty:
        gap = (valid["best_ret_moy_pct"] - valid["limit_touch_best_ret_moy_pct"])
        share_gap = (gap > 0.5 * valid["best_ret_moy_pct"].abs()).mean()
        if share_gap > 0.5:
            fired = True
            print(f"    [!] {share_gap*100:.0f}% des actions : close_cross >> limit_touch.")
            print(f"        L'edge optimiste depend de l'entree au close de croisement (peu realiste).")
        share_cost = (valid["cost_break_even_bps"] < 10).mean()
        if share_cost > 0.5:
            fired = True
            print(f"    [!] {share_cost*100:.0f}% des actions ne survivent pas a 10 bps de couts.")
            print(f"        Tradabilite douteuse sur actions peu liquides.")
    if not fired:
        print("    (aucun warning global majeur)")
    # DRIFT vs FADE sur l'univers
    if not valid.empty:
        vc = valid["best_hypothese"].value_counts()
        if len(vc):
            print(f"    -> Hypothese dominante (meilleures configs) : {vc.idxmax()} "
                  f"({vc.to_dict()})")



# --------------------------------------------------------------------------- #
#  TRADER REPORT : SCORECARD + GRAPHES PNG                                    #
# --------------------------------------------------------------------------- #
def _dedupe_for_report(master_df):
    """Nettoie les doublons de tickers pour le reporting visuel."""
    if master_df is None or master_df.empty:
        return pd.DataFrame()
    df = master_df.copy()
    if "ticker" not in df.columns:
        return df
    sort_cols = [c for c in ["confidence_score", "test_ret_moy_pct", "best_ret_moy_pct"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=False)
    return df.drop_duplicates(subset=["ticker"], keep="first").reset_index(drop=True)


def _safe_num(df, col, default=np.nan):
    if col not in df.columns:
        return pd.Series([default] * len(df), index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def _clean_label(x, max_len=22):
    s = str(x)
    return s if len(s) <= max_len else s[:max_len - 1] + "…"


def build_trader_asset_scorecard(master_df):
    """
    Scorecard propre par asset pour discussion trader.
    Fichier plus lisible que le master brut : une ligne par ticker, triée par score.
    """
    df = _dedupe_for_report(master_df)
    if df.empty:
        return df
    keep = [
        "ticker", "classification", "confidence_score", "best_hypothese",
        "best_model", "best_vwap_mode", "best_wait_min", "best_horizon",
        "best_ret_moy_pct", "test_ret_moy_pct", "best_sharpe", "best_n_trades",
        "random_side_percentile", "random_ts_percentile", "cost_break_even_bps",
        "limit_touch_best_ret_moy_pct", "train_ret_moy_pct", "train_sharpe",
        "test_sharpe", "walk_forward_positive_ratio", "pct_preopen_entries",
        "main_warning", "interpretation_short"
    ]
    keep = [c for c in keep if c in df.columns]
    out = df[keep].copy()
    out.insert(0, "rank", range(1, len(out) + 1))
    if "classification" in out.columns:
        out["research_bucket"] = out["classification"].map({
            "A_CLEAN_MACRO_SIGNAL": "Core candidate",
            "B_INTERESTING_BUT_FRAGILE": "Watchlist",
            "C_VWAP_DRIVEN_OR_SUSPECT": "VWAP-driven / suspect",
            "D_REJECT": "Reject",
            "INSUFFICIENT_DATA": "Insufficient data",
        }).fillna(out["classification"])
    return out


def generate_trader_report(master_df, cfg_df, random_df, train_test_df, walk_forward_df, outdir, country):
    """
    Cree un dossier trader_report avec :
      - trader_asset_scorecard.csv
      - trader_talking_points.txt
      - 4/5 graphes PNG propres pour un trader
    """
    if not GENERATE_TRADER_REPORT:
        return []
    report_dir = os.path.join(outdir, "trader_report")
    os.makedirs(report_dir, exist_ok=True)
    df = _dedupe_for_report(master_df)
    if df.empty:
        return []

    generated = []
    scorecard = build_trader_asset_scorecard(df)
    scorecard_path = os.path.join(report_dir, "trader_asset_scorecard.csv")
    scorecard.to_csv(scorecard_path, index=False)
    generated.append(scorecard_path)

    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.figsize": (11, 6.5),
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.autolayout": True,
    })

    def savefig(name):
        path = os.path.join(report_dir, name)
        plt.savefig(path, dpi=TRADER_REPORT_DPI, bbox_inches="tight")
        plt.close()
        generated.append(path)

    # 1) Mix de classifications
    order = ["A_CLEAN_MACRO_SIGNAL", "B_INTERESTING_BUT_FRAGILE", "C_VWAP_DRIVEN_OR_SUSPECT", "D_REJECT", "INSUFFICIENT_DATA"]
    counts = df["classification"].value_counts().reindex(order).fillna(0).astype(int)
    labels = ["A clean", "B fragile", "C VWAP/suspect", "D reject", "Insufficient"]
    fig, ax = plt.subplots()
    ax.bar(labels, counts.values)
    ax.set_title(f"{country} macro + VWAP screening — classification mix")
    ax.set_ylabel("Number of assets")
    ax.grid(axis="y", alpha=0.25)
    for i, v in enumerate(counts.values):
        ax.text(i, v + max(counts.max() * 0.02, 0.05), str(v), ha="center", va="bottom")
    savefig("01_classification_mix.png")

    # 2) Top assets par confidence score
    top = df.sort_values(["confidence_score", "test_ret_moy_pct"], ascending=False).head(REPORT_TOP_N).copy().iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 7))
    ylabels = [f"{_clean_label(t)} | {str(c).split('_')[0]}" for t, c in zip(top["ticker"], top["classification"])]
    ax.barh(ylabels, _safe_num(top, "confidence_score"))
    ax.set_title("Top assets by confidence score")
    ax.set_xlabel("Confidence score (0–100)")
    ax.grid(axis="x", alpha=0.25)
    for i, v in enumerate(_safe_num(top, "confidence_score")):
        if v == v:
            ax.text(v + 1, i, f"{v:.0f}", va="center")
    savefig("02_top_assets_confidence.png")

    # 3) Full-period vs test edge
    plot_df = df.dropna(subset=["best_ret_moy_pct", "test_ret_moy_pct"]).copy()
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(plot_df["best_ret_moy_pct"], plot_df["test_ret_moy_pct"], s=55, alpha=0.8)
    ax.axhline(0, linewidth=1)
    ax.axvline(0, linewidth=1)
    ax.set_title("Full-period edge vs chronological test edge")
    ax.set_xlabel("Best full-period return per trade (%)")
    ax.set_ylabel("Out-of-sample test return per trade (%)")
    ax.grid(alpha=0.25)
    ann = plot_df.sort_values(["confidence_score", "test_ret_moy_pct"], ascending=False).head(10)
    for _, r in ann.iterrows():
        ax.annotate(str(r["ticker"]), (r["best_ret_moy_pct"], r["test_ret_moy_pct"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    savefig("03_full_vs_test_edge.png")

    # 4) Random percentile vs cost break-even
    plot_df = df.dropna(subset=["random_side_percentile", "cost_break_even_bps"]).copy()
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(plot_df["random_side_percentile"], plot_df["cost_break_even_bps"], s=55, alpha=0.8)
    ax.axvline(95, linestyle="--", linewidth=1)
    ax.axhline(10, linestyle="--", linewidth=1)
    ax.set_title("Robustness map — directional edge vs cost tolerance")
    ax.set_xlabel("Percentile vs random side (%)")
    ax.set_ylabel("Cost break-even (bps)")
    ax.grid(alpha=0.25)
    ann = plot_df.sort_values(["confidence_score", "test_ret_moy_pct"], ascending=False).head(10)
    for _, r in ann.iterrows():
        ax.annotate(str(r["ticker"]), (r["random_side_percentile"], r["cost_break_even_bps"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    savefig("04_random_vs_cost_robustness.png")

    # 5) Walk-forward consistency
    if "walk_forward_positive_ratio" in df.columns:
        wf = df.dropna(subset=["walk_forward_positive_ratio"]).sort_values(
            ["walk_forward_positive_ratio", "confidence_score"], ascending=False
        ).head(REPORT_TOP_N).iloc[::-1]
        if not wf.empty:
            fig, ax = plt.subplots(figsize=(11, 7))
            ax.barh(wf["ticker"], wf["walk_forward_positive_ratio"] * 100)
            ax.set_title("Walk-forward consistency by asset")
            ax.set_xlabel("Positive walk-forward years (%)")
            ax.grid(axis="x", alpha=0.25)
            for i, v in enumerate(wf["walk_forward_positive_ratio"] * 100):
                if v == v:
                    ax.text(v + 1, i, f"{v:.0f}%", va="center")
            savefig("05_walk_forward_consistency.png")

    # Talking points texte
    tp_path = os.path.join(report_dir, "trader_talking_points.txt")
    with open(tp_path, "w", encoding="utf-8") as f:
        n = len(df)
        counts_dict = df["classification"].value_counts().to_dict()
        top3 = df.sort_values(["confidence_score", "test_ret_moy_pct"], ascending=False).head(3)
        f.write(f"Macro + VWAP screening — {country}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Universe tested: {n} assets.\n")
        f.write("Classification mix: " + ", ".join(f"{k}={v}" for k, v in counts_dict.items()) + "\n\n")
        f.write("Top candidates:\n")
        for _, r in top3.iterrows():
            f.write(
                f"- {r.get('ticker')}: {r.get('classification')} | "
                f"{r.get('best_hypothese')} {r.get('best_vwap_mode')} {r.get('best_horizon')} | "
                f"full={r.get('best_ret_moy_pct'):.3f}% | test={r.get('test_ret_moy_pct'):.3f}% | "
                f"random_pct={r.get('random_side_percentile'):.0f}% | cost_BE={r.get('cost_break_even_bps')}bps | score={r.get('confidence_score')}\n"
            )
        f.write("\nKey caveats:\n")
        f.write("- PRE_OPEN dominance means this should be described as macro calendar day + VWAP intraday, not exact minute-by-minute release trading.\n")
        f.write("- Close-cross VWAP execution is the optimistic version; limit-touch is the conservative check.\n")
        f.write("- Focus should be on assets that survive random side, random timestamps, costs, and chronological test.\n")
    generated.append(tp_path)

    return generated


# --------------------------------------------------------------------------- #
#  MAIN — SINGLE COUNTRY                                                        #
# --------------------------------------------------------------------------- #
def main():
    banner("MACRO EVENT BACKTESTER — SINGLE COUNTRY / ~20 STOCKS")

    # --- 1. classeur macro ---
    print("  Etape 1 : classeur events + metriques (.xlsx ou .ods)")
    wb_path = ask_path(
        "  > Selectionne le classeur (data + METRIQ_FINISH) dans la fenetre...",
        filetypes=[("Classeurs", "*.xlsx *.ods *.xlsm"), ("Tous les fichiers", "*.*")],
        title="Classeur events + metriques",
    )
    engine = detect_engine(wb_path)
    print("\n  Lecture des feuilles... (le .ods volumineux peut prendre 1-2 min)")
    data_sheet, metriq_sheet = find_sheets(wb_path, engine)
    metriq = load_metriq(wb_path, metriq_sheet, engine)
    events = load_events(wb_path, data_sheet, engine)
    print(f"    -> {len(events):,} events | {len(metriq):,} metriques")

    # --- 2. choix du pays ---
    pays_dispo = sorted(set(events["country"]) & set(metriq["Country"]))
    print(f"\n  Pays disponibles : {', '.join(pays_dispo)}")
    raw = input(f"  > Pays a analyser ? [{COUNTRY_DEFAULT}] : ").strip().upper()
    country = raw if raw else COUNTRY_DEFAULT
    if country not in pays_dispo:
        print(f"  [!] '{country}' indisponible. Choisis parmi : {', '.join(pays_dispo)}")
        while True:
            country = input("  > Pays : ").strip().upper()
            if country in pays_dispo:
                break
            print(f"     indisponible. Parmi : {', '.join(pays_dispo)}")
    print(f"    -> pays retenu : {country}")

    # signaux du pays (une fois)
    try:
        signals = build_signals(events, metriq, country)
    except Exception as e:
        print(f"  [!] Impossible de construire les signaux pour {country} ({e}). Fin.")
        sys.exit(0)
    if len(signals) < MIN_RELEASES_FOR_COUNTRY:
        print(f"  [!] Seulement {len(signals)} releases (< {MIN_RELEASES_FOR_COUNTRY}). "
              f"Resultats peu fiables, on continue quand meme.")
    print(f"  {len(signals):,} releases macro retenues pour {country}.")

    # --- 3. selection des CSV ---
    csvs = ask_paths(
        f"  > Selectionne les CSV de prix pour les actions {country} (multi-selection, ~20)...",
        filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
        title=f"CSV de prix — {country}",
    )
    if not csvs:
        print("  Aucun CSV selectionne. Fin.")
        sys.exit(0)
    print(f"  {len(csvs)} action(s) a traiter.")

    rng = np.random.default_rng(RANDOM_SEED)
    master_rows, cfg_all, rnd_all, tt_all, wf_all, trades_all = [], [], [], [], [], []

    # --- 4. boucle actions ---
    for i, csv in enumerate(csvs, 1):
        ticker = extract_ticker(csv)
        print(f"  Processing {i}/{len(csvs)} — {ticker} ...", flush=True)
        # chargement
        try:
            px = load_prices(csv)
        except Exception as e:
            print(f"    {ticker} | ERREUR chargement -> INSUFFICIENT_DATA ({e})")
            master_rows.append(_failed_row(country, ticker, csv,
                                           f"load_error: {e}", "CSV illisible/mal formate"))
            continue
        if len(px) < 200:
            print(f"    {ticker} | CSV trop court ({len(px)} barres) -> INSUFFICIENT_DATA")
            master_rows.append(_failed_row(country, ticker, csv,
                                           "csv_too_short", "CSV trop court"))
            continue
        # traitement
        try:
            row, cfgs, rnds, tts, wfs, trades = process_action(
                signals, px, country, ticker, csv, rng)
            master_rows.append(row)
            cfg_all.extend(cfgs); rnd_all.extend(rnds)
            tt_all.extend(tts); wf_all.extend(wfs)
            if trades is not None:
                trades_all.append(trades)
            print(f"    {ticker} | best={row.get('best_hypothese','?')} "
                  f"{row.get('best_vwap_mode','')} {row.get('best_horizon','')} | "
                  f"ret={row.get('best_ret_moy_pct',float('nan')):.3f}% | "
                  f"Sharpe={row.get('best_sharpe',float('nan')):.2f} | "
                  f"test={row.get('test_ret_moy_pct',float('nan')):.3f}% | "
                  f"class={row.get('classification','?')} "
                  f"(score {row.get('confidence_score','?')})")
        except Exception as e:
            print(f"    {ticker} | ERREUR traitement -> INSUFFICIENT_DATA ({e})")
            master_rows.append(_failed_row(country, ticker, csv,
                                           f"process_error: {e}", "Echec du traitement"))
            continue

    if not master_rows:
        print("\n  Aucune action traitee. Fin.")
        sys.exit(0)

    master_df = pd.DataFrame(master_rows)
    if "error_message" not in master_df.columns:
        master_df["error_message"] = ""
    master_df["error_message"] = master_df["error_message"].fillna("")

    # --- 5. rapport console ---
    print_global_report(master_df, country)

    # --- 6. exports ---
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_out = os.path.dirname(os.path.abspath(wb_path))
    if not os.access(base_out, os.W_OK):
        base_out = os.path.expanduser("~")
    outdir = os.path.join(base_out, f"macro_vwap_single_country_results_{stamp}")
    os.makedirs(outdir, exist_ok=True)

    exports = {
        "single_country_master_summary.csv": master_df,
        "single_country_all_configs_summary.csv": pd.DataFrame(cfg_all),
        "single_country_random_tests.csv": pd.DataFrame(rnd_all),
        "single_country_train_test.csv": pd.DataFrame(tt_all),
        "single_country_walk_forward.csv": pd.DataFrame(wf_all),
    }
    if EXPORT_ALL_TRADES and trades_all:
        exports["single_country_all_trades_light.csv"] = pd.concat(trades_all, ignore_index=True)

    print(f"\n  Exports -> {outdir}")
    for fname, df in exports.items():
        path = os.path.join(outdir, fname)
        try:
            (df if df is not None else pd.DataFrame()).to_csv(path, index=False)
            print(f"    - {fname} ({len(df) if df is not None else 0} lignes)")
        except Exception as e:
            print(f"    - {fname} : ECHEC ({e})")

    # --- 7. trader report / graphes ---
    if GENERATE_TRADER_REPORT:
        try:
            graph_paths = generate_trader_report(
                master_df=master_df,
                cfg_df=pd.DataFrame(cfg_all),
                random_df=pd.DataFrame(rnd_all),
                train_test_df=pd.DataFrame(tt_all),
                walk_forward_df=pd.DataFrame(wf_all),
                outdir=outdir,
                country=country,
            )
            if graph_paths:
                print("    - trader_report/ (scorecard + graphes PNG)")
        except Exception as e:
            print(f"    - trader_report : ECHEC ({e})")

    banner("FIN")


def _failed_row(country, ticker, csv, error_message, warning):
    """Ligne maitre minimale pour une action en echec (schema coherent)."""
    row = {
        "country": country, "ticker": ticker, "price_file": os.path.basename(csv),
        "start_price_date": "", "end_price_date": "", "n_price_bars": 0,
        "n_releases_retained": 0, "n_releases_traded": 0, "error_message": error_message,
    }
    row.update(_empty_master_fields())
    row["classification"] = "INSUFFICIENT_DATA"
    row["confidence_score"] = 0
    row["main_warning"] = warning
    row["interpretation_short"] = "Donnees insuffisantes / echec."
    return row




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompu.")
    except Exception as e:
        import traceback
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)
