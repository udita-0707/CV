"""Named values and tables for the write-ups, read only from files under ``results/``.

Markdown templates reference values as ``{{key}}`` and tables as ``{{table:name}}``
(``src/render_reports.py``); the LaTeX paper uses ``\\val{key}`` and
``\\input{generated/tab_<name>}`` (``paper/make_tables.py``). Every number in those
documents is formatted here from a saved CSV/JSON, never typed by hand.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

MINUS = "−"


@dataclass(frozen=True)
class Table:
    columns: list[tuple[str, str]]  # (header, kind)
    rows: list[list[object]]
    align: str  # one character per column: l / r / c


def _signed(text: str, target: str) -> str:
    if not text.startswith("-"):
        return text
    return (MINUS + text[1:]) if target == "md" else f"$-${text[1:]}"


def tex_escape(text: str) -> str:
    for char, replacement in (("\\", r"\textbackslash{}"), ("_", r"\_"), ("%", r"\%"), ("&", r"\&"), ("#", r"\#"), ("$", r"\$")):
        text = text.replace(char, replacement)
    for char, replacement in ((MINUS, "$-$"), ("\u2265", r"$\geq$"), ("\u2264", r"$\leq$"), ("\u0394", r"$\Delta$"), (">=", r"$\geq$"), ("<=", r"$\leq$"), ("<", "$<$"), (">", "$>$"), ("\u2013", "--")):
        text = text.replace(char, replacement)
    return text


def fmt(value: object, kind: str, target: str = "md") -> str:
    """Format one value; ``target`` is ``md`` or ``tex``."""
    if kind == "str":
        return str(value) if target == "md" else tex_escape(str(value))
    if kind == "code":
        return f"`{value}`" if target == "md" else r"\texttt{" + tex_escape(str(value)) + "}"
    if kind == "int":
        text = f"{int(value):,}"
        return text if target == "md" else text.replace(",", "{,}")
    if kind in {"pct1", "pct2"}:
        text = f"{100 * float(value):.{kind[-1]}f}"
        return _signed(text, target) + ("%" if target == "md" else r"\%")
    if kind in {"pp1", "pp2", "spp2"}:
        digits = kind[-1]
        text = f"{float(value):+.{digits}f}" if kind.startswith("s") else f"{float(value):.{digits}f}"
        return _signed(text, target) + (" pp" if target == "md" else r"\,pp")
    if kind in {"num2", "num3", "num4", "snum2"}:
        text = f"{float(value):+.{kind[-1]}f}" if kind.startswith("s") else f"{float(value):.{kind[-1]}f}"
        return _signed(text, target)
    if kind == "ci_pp":
        low, high = value
        inner = f"{fmt(low, 'num2', target)}, {fmt(high, 'num2', target)}"
        return f"[{inner}] pp" if target == "md" else f"[{inner}]\\,pp"
    if kind == "ci2":
        low, high = value
        return f"[{fmt(low, 'num2', target)}, {fmt(high, 'num2', target)}]"
    raise ValueError(f"unknown kind {kind!r}")


def preregistration_commit(root: Path) -> dict[str, tuple[str, str]]:
    """First commit that added the M3 hypothesis file, read from git history."""
    output = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%h|%ad", "--date=format:%d %b %Y %H:%M %z", "--", "milestones/M3/hypothesis.md"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    commit, date = output[-1].split("|")
    return {"prereg_commit": (commit, "str"), "prereg_commit_date": (date, "str")}


def _read(root: Path, relative: str) -> pd.DataFrame:
    return pd.read_csv(root / "results" / relative, keep_default_na=False, na_values=[""])


def collect(root: Path) -> tuple[dict[str, tuple[object, str]], dict[str, Table]]:
    """Return (values, tables); each value is (raw, kind)."""
    v: dict[str, tuple[object, str]] = {}
    t: dict[str, Table] = {}

    # ---------------------------------------------------------------- M2 baseline and published values
    baseline = _read(root, "baseline/baseline_results.csv").set_index("metric")
    comparison = _read(root, "baseline/published_vs_measured.csv").set_index("metric")
    folds_m2 = _read(root, "baseline/fold_summary.csv")
    short = {"accuracy": "acc", "sensitivity_recall": "sens", "specificity": "spec", "auc": "auc", "f1": "f1"}
    for metric, key in short.items():
        kind = "num4" if metric == "auc" else "pct2"
        v[f"m2_{key}_mean"] = (baseline.at[metric, "mean"], kind)
        v[f"m2_{key}_sd"] = (100 * baseline.at[metric, "standard_deviation"] if kind == "pct2" else baseline.at[metric, "standard_deviation"], "pp2" if kind == "pct2" else "num4")
        if metric in comparison.index:
            v[f"pub_{key}"] = (comparison.at[metric, "published_value"], "num3" if metric == "auc" else "pct1")
            delta = comparison.at[metric, "measured_minus_published"]
            v[f"delta_{key}"] = (100 * delta, "spp2") if kind == "pct2" else (delta, "num4")
    rows = []
    for metric, label in (("accuracy", "Accuracy"), ("sensitivity_recall", "Sensitivity (recall)"), ("specificity", "Specificity"), ("auc", "AUC")):
        row = comparison.loc[metric]
        if metric == "auc":
            rows.append([label, (row.published_value, "num3"), (row.measured_mean, "num4"), (row.measured_fold_sd, "num4"), (row.measured_minus_published, "num4")])
        else:
            rows.append([label, (row.published_value, "pct1"), (row.measured_mean, "pct2"), (100 * row.measured_fold_sd, "pp2"), (100 * row.measured_minus_published, "spp2")])
    t["reproduction"] = Table(
        [("Metric", "str"), ("Published", "cell"), ("Measured (M2)", "cell"), ("Fold SD", "cell"), ("Difference", "cell")],
        rows,
        "lrrrr",
    )
    v["m2_test_fold_sizes"] = (" / ".join(f"{n:,}" for n in folds_m2.test_samples), "str")
    v.update(preregistration_commit(root))
    config = json.loads((root / "results" / "baseline" / "run_environment.json").read_text())["config"]
    for key in ("image_size", "hidden_units", "epochs", "seed", "n_splits"):
        v[f"cfg_{key}"] = (config[key], "int")
    v["cfg_dropout"] = (config["dropout"], "str")
    v["cfg_learning_rate"] = (config["learning_rate"], "str")
    v["m2_measured_utc"] = (baseline.measured_at_utc.iloc[0][:16].replace("T", " "), "str")
    published = _read(root, "baseline/published_baseline.csv")
    cell_level = published[published.protocol == "cell-level comparison"].set_index("metric")
    for metric, key in short.items():
        if metric in cell_level.index:
            v[f"pub_cell_{key}"] = (cell_level.at[metric, "published_value"], "num4" if metric == "auc" else "pct1")

    # ---------------------------------------------------------------- M4 primary
    verdict = json.loads((root / "results" / "m4" / "primary_verdict.json").read_text())
    per_patient = _read(root, "m4/per_patient_metrics.csv")
    fold_metrics = _read(root, "m4/fold_metrics.csv")
    v["verdict"] = (verdict["verdict"], "str")
    v["verdict_lower"] = (verdict["verdict"].lower(), "str")
    v["verdict_exact_threshold"] = (verdict["verdict_under_exact_threshold"], "str")
    v["n_negative_folds"] = (verdict["n_negative"], "int")
    v["n_positive_folds"] = (verdict["n_positive"], "int")
    v["n_folds"] = (verdict["n_folds"], "int")
    v["mean_diff_pp"] = (verdict["mean_difference_pp"], "spp2")
    v["mean_diff_abs_pp"] = (abs(verdict["mean_difference_pp"]), "pp2")
    v["mean_diff_pp_3"] = (verdict["mean_difference_pp"], "num3")
    v["threshold_pp"] = (verdict["threshold_as_written_pp"], "pp2")
    v["threshold_exact_pp"] = (verdict["threshold_exact_half_m2_sd_pp"], "num3")
    v["shortfall_pp"] = (verdict["threshold_as_written_pp"] - abs(verdict["mean_difference_pp"]), "pp2")
    band = verdict["pre_registration"]["predicted_mean_difference_pp"]
    v["pred_low_pp"] = (band[0], "spp2")
    v["pred_high_pp"] = (band[1], "spp2")
    v["within_band"] = ("inside" if verdict["mean_within_predicted_range"] else "outside", "str")
    v["t_ci"] = ((verdict["t_interval_95_pp"]["low"], verdict["t_interval_95_pp"]["high"]), "ci_pp")
    v["boot_ci"] = ((verdict["bootstrap_95_pp_exploratory_a4"]["ci_low_pp"], verdict["bootstrap_95_pp_exploratory_a4"]["ci_high_pp"]), "ci_pp")
    v["boot_resamples"] = (verdict["bootstrap_95_pp_exploratory_a4"]["n_resamples"], "int")
    v["boot_seed"] = (verdict["bootstrap_95_pp_exploratory_a4"]["seed"], "int")
    v["min_wilcoxon_p"] = (verdict["significance_testing"]["min_two_sided_exact_wilcoxon_p"], "num4")
    v["min_wilcoxon_p_one_sided"] = (verdict["significance_testing"]["min_two_sided_exact_wilcoxon_p"] / 2, "num4")
    audit = json.loads((root / "results" / "baseline" / "dataset_audit.json").read_text())
    v["map_entries_par"] = (audit["official_mapping_entries"]["Parasitized"], "int")
    v["map_entries_uninf"] = (audit["official_mapping_entries"]["Uninfected"], "int")
    v["reuse_max_abs"] = (f"{verdict['reuse_assertions']['pooled_metrics_equal_fold_results']['max_abs_difference']:.1e}", "str")
    v["n_rows"] = (verdict["reuse_assertions"]["row_count"], "int")
    v["n_ids"] = (per_patient.patient_id.nunique(), "int")
    v["n_ids_pos"] = (int(per_patient.sensitivity_defined.astype(str).eq("True").sum()), "int")
    v["n_ids_negonly"] = (int(per_patient.sensitivity_defined.astype(str).eq("False").sum()), "int")
    pos = per_patient[per_patient.n_positive > 0].n_positive
    v["npos_min"], v["npos_median"], v["npos_max"] = (pos.min(), "int"), (pos.median(), "int"), (pos.max(), "int")
    v["nneg_min"], v["nneg_max"] = (per_patient.n_negative.min(), "int"), (per_patient.n_negative.max(), "int")
    v["nneg_sd"] = (per_patient.n_negative.std(ddof=1), "num2")
    v["npos_sd"] = (pos.std(ddof=1), "num2")
    hardest = per_patient.loc[per_patient.sensitivity.idxmin()]
    v["id_sens_min"] = (hardest.sensitivity, "pct1")
    v["id_sens_min_id"] = (hardest.patient_id, "str")
    v["id_sens_min_npos"] = (hardest.n_positive, "int")
    v["ids_per_fold"] = (" / ".join(str(n) for n in fold_metrics.n_ids_total), "str")
    v["pos_ids_per_fold"] = (" / ".join(str(n) for n in fold_metrics.n_ids_sensitivity), "str")
    v["negonly_ids_per_fold"] = (" / ".join(str(n) for n in fold_metrics.n_ids_sensitivity_undefined), "str")

    a4 = _read(root, "m4/ablations/a4_bootstrap.csv")
    a4["fold"] = a4.fold.astype(str)
    rows = []
    for row in verdict["folds"]:
        fold = int(row["fold"])
        v[f"f{fold}_pooled"] = (row["pooled"], "pct2")
        v[f"f{fold}_macro"] = (row["macro"], "pct2")
        v[f"f{fold}_diff"] = (row["difference_pp"], "spp2")
        v[f"f{fold}_ci"] = ((row["ci_low_pp"], row["ci_high_pp"]), "ci_pp")
        v[f"f{fold}_ids"] = (row["n_ids_eligible"], "int")
        rows.append([str(fold), row["n_ids_eligible"], 100 * row["pooled"], 100 * row["macro"], row["difference_pp"], (row["ci_low_pp"], row["ci_high_pp"])])
    boot_mean = a4[(a4.metric == "sensitivity") & (a4.fold == "mean")].iloc[0]
    rows.append(["Mean", sum(r[1] for r in rows), sum(r[2] for r in rows) / 5, sum(r[3] for r in rows) / 5, verdict["mean_difference_pp"], (boot_mean.ci_low_pp, boot_mean.ci_high_pp)])
    t["primary"] = Table(
        [("Fold", "str"), ("IDs", "int"), ("Pooled (%)", "num2"), ("Macro (%)", "num2"), ("\u0394 (pp)", "snum2"), ("95% CI (pp)", "ci2")],
        rows,
        "lrrrrr",
    )
    v["boot_share_below_zero"] = (boot_mean.share_resamples_below_zero, "pct1")
    worst_fold = max(verdict["folds"], key=lambda r: r["difference_pp"])
    v["positive_fold"] = (int(worst_fold["fold"]), "int")
    v["positive_fold_diff"] = (worst_fold["difference_pp"], "spp2")
    ranked = per_patient[per_patient.n_positive > 0].sort_values(["fn", "patient_id"], ascending=[False, True]).head(10)
    v["fn_top10_in_posfold"] = (int((ranked.fold == int(worst_fold["fold"])).sum()), "int")

    # ---------------------------------------------------------------- M4 secondary heterogeneity
    het = _read(root, "m4/secondary_heterogeneity.csv")
    v["id_sens_sd_min"] = (100 * het.id_sensitivity_sd.min(), "pp1")
    v["id_sens_sd_max"] = (100 * het.id_sensitivity_sd.max(), "pp1")
    v["id_acc_sd_min"] = (100 * het.id_accuracy_sd.min(), "pp1")
    v["id_acc_sd_max"] = (100 * het.id_accuracy_sd.max(), "pp1")
    v["folds_sens_sd_gt_acc_sd"] = (int((het.id_sensitivity_sd > het.id_accuracy_sd).sum()), "int")
    v["id_fnr_max_max"] = (het.id_fnr_max.max(), "pct1")
    v["id_fnr_iqr_min"] = (100 * het.id_fnr_iqr.min(), "pp1")
    v["id_fnr_iqr_max"] = (100 * het.id_fnr_iqr.max(), "pp1")
    t["heterogeneity"] = Table(
        [("Fold", "str"), ("IDs", "int"), ("No Parasitized cells", "int"), ("SD sens.", "num3"), ("IQR FNR", "num3"), ("Min-max FNR", "str"), ("SD accuracy", "num3")],
        [
            [str(r.fold), r.n_ids_total, r.n_ids_no_positive_cells, r.id_sensitivity_sd, r.id_fnr_iqr, f"{r.id_fnr_min:.3f}-{r.id_fnr_max:.3f}", r.id_accuracy_sd]
            for r in het.itertuples()
        ],
        "lrrrrrr",
    )

    # ---------------------------------------------------------------- M4 ablations
    a1 = _read(root, "m4/ablations/a1_weighting.csv")
    v["a1_max_abs"] = (f"{a1.weighted_minus_pooled.abs().max():.1e}", "str")
    a2 = _read(root, "m4/ablations/a2_summary.csv").set_index("min_positive_cells")
    for k in a2.index:
        v[f"a2_k{k}_mean"] = (a2.at[k, "mean_pp"], "spp2")
        v[f"a2_k{k}_mean_n"] = (a2.at[k, "mean_pp"], "snum2")
        v[f"a2_k{k}_kept"] = (a2.at[k, "ids_kept"], "int")
        v[f"a2_k{k}_excluded"] = (a2.at[k, "ids_excluded"], "int")
        v[f"a2_k{k}_neg"] = (a2.at[k, "n_negative"], "int")
        v[f"a2_k{k}_cells_kept"] = (a2.at[k, "share_positive_cells_kept"], "pct1")
    a3 = _read(root, "m4/ablations/a3_leave_one_id_out.csv")
    a3s = _read(root, "m4/ablations/a3_summary.csv")
    flips = a3[a3.verdict_changes.astype(str) == "True"]
    v["a3_deletions"] = (len(a3), "int")
    v["a3_flips"] = (len(flips), "int")
    v["a3_flip_ids"] = (", ".join(f"{r.removed_patient_id} (fold {r.fold})" for r in flips.itertuples()), "str")
    v["a3_flip_verdicts"] = (", ".join(sorted(set(flips.verdict_if_removed))) or "none", "str")
    v["a3_max_change"] = (a3.change_pp.abs().max(), "pp2")
    v["a3_mean_min"] = (a3.mean_difference_pp_if_removed.min(), "spp2")
    v["a3_mean_max"] = (a3.mean_difference_pp_if_removed.max(), "spp2")
    v["a3_diff_min"] = (a3s.min_difference_pp_without.min(), "spp2")
    v["a3_diff_max"] = (a3s.max_difference_pp_without.max(), "spp2")
    top_change = a3.loc[a3.change_pp.abs().idxmax()]
    v["a3_top_id"] = (top_change.removed_patient_id, "str")
    v["a3_top_fold"] = (int(top_change.fold), "int")
    v["a3_top_npos"] = (int(top_change.removed_n_positive), "int")
    v["a3_top_sens"] = (top_change.removed_sensitivity, "pct1")
    v["a3_top_diff_without"] = (top_change.difference_pp_without, "spp2")
    v["a3_top_mean_if_removed"] = (top_change.mean_difference_pp_if_removed, "spp2")
    v["a3_top_verdict_if_removed"] = (top_change.verdict_if_removed, "str")
    for row in flips.itertuples():
        key = f"a3_flip_f{row.fold}"
        v[f"{key}_id"] = (row.removed_patient_id, "str")
        v[f"{key}_mean"] = (row.mean_difference_pp_if_removed, "spp2")
    a5 = _read(root, "m4/ablations/a5_secondary_metrics.csv")
    a5["fold"] = a5.fold.astype(str)
    for metric, key in (("specificity", "spec"), ("accuracy", "acc")):
        mean_row = a5[(a5.metric == metric) & (a5.fold == "mean")].iloc[0]
        per_fold = a5[(a5.metric == metric) & (a5.fold != "mean")]
        v[f"a5_{key}_mean"] = (mean_row.difference_pp, "spp2")
        v[f"a5_{key}_ci"] = ((mean_row.ci_low_pp, mean_row.ci_high_pp), "ci_pp")
        v[f"a5_{key}_maxabs"] = (per_fold.difference_pp.abs().max(), "pp2")
        v[f"a5_{key}_neg"] = (int((per_fold.difference_pp < 0).sum()), "int")
    t["ablations"] = Table(
        [("Ablation (exploratory)", "str"), ("Setting", "str"), ("IDs", "str"), ("Mean \u0394 (pp)", "snum2"), ("Folds < 0", "str"), ("Note", "str")],
        [
            ["Primary (M3 rule)", "macro, >= 1 Parasitized cell", fmt(a2.at[1, "ids_kept"], "int"), verdict["mean_difference_pp"], f"{verdict['n_negative']}/5", f"verdict {verdict['verdict']}"],
            ["A1 weighting", "per-ID, weighted by cells", fmt(a2.at[1, "ids_kept"], "int"), float("nan"), "-", f"identical to pooled in all folds (max abs. difference {a1.weighted_minus_pooled.abs().max():.1e})"],
            ["A2 eligibility", ">= 10 Parasitized cells", fmt(a2.at[10, "ids_kept"], "int"), a2.at[10, "mean_pp"], f"{int(a2.at[10, 'n_negative'])}/5", f"{fmt(a2.at[10, 'share_positive_cells_kept'], 'pct1')} of positive cells kept"],
            ["A2 eligibility", ">= 25 Parasitized cells", fmt(a2.at[25, "ids_kept"], "int"), a2.at[25, "mean_pp"], f"{int(a2.at[25, 'n_negative'])}/5", f"{fmt(a2.at[25, 'share_positive_cells_kept'], 'pct1')} of positive cells kept"],
            ["A3 leave-one-ID-out", f"{len(a3)} single-ID deletions", fmt(a2.at[1, "ids_kept"] - 1, "int") + " remain", float("nan"), "-", f"mean range {fmt(a3.mean_difference_pp_if_removed.min(), 'num2')} to {fmt(a3.mean_difference_pp_if_removed.max(), 'num2')}; {len(flips)} change the verdict"],
            ["A4 cluster bootstrap", f"{verdict['bootstrap_95_pp_exploratory_a4']['n_resamples']:,} resamples, seed {verdict['bootstrap_95_pp_exploratory_a4']['seed']}", fmt(a2.at[1, "ids_kept"], "int"), verdict["mean_difference_pp"], "-", f"95% CI {fmt((boot_mean.ci_low_pp, boot_mean.ci_high_pp), 'ci2')}"],
            ["A5 specificity", "macro over IDs with Uninfected cells", fmt(v["n_ids"][0], "int"), a5[(a5.metric == "specificity") & (a5.fold == "mean")].difference_pp.iloc[0], f"{v['a5_spec_neg'][0]}/5", f"95% CI {fmt(v['a5_spec_ci'][0], 'ci2')}"],
            ["A5 accuracy", "macro over all IDs", fmt(v["n_ids"][0], "int"), a5[(a5.metric == "accuracy") & (a5.fold == "mean")].difference_pp.iloc[0], f"{v['a5_acc_neg'][0]}/5", f"95% CI {fmt(v['a5_acc_ci'][0], 'ci2')}"],
        ],
        "lllrrl",
    )

    if (root / "results" / "m5" / "concentration_summary.csv").exists():
        _collect_m5(root, v, t, int(worst_fold["fold"]))
    return v, t


def _collect_m5(root: Path, v: dict[str, tuple[object, str]], t: dict[str, Table], positive_fold: int) -> None:
    """M5 values and tables (prediction level, then image level)."""
    conc = _read(root, "m5/concentration_summary.csv").set_index("error_type")
    tables = _read(root, "m5/error_concentration.csv")
    for kind in ("FN", "FP"):
        k = kind.lower()
        v[f"{k}_total"] = (conc.at[kind, "total_errors"], "int")
        v[f"{k}_ids_at_risk"] = (conc.at[kind, "ids_at_risk"], "int")
        v[f"{k}_ids_any"] = (conc.at[kind, "ids_with_any_error"], "int")
        v[f"{k}_top1_share"] = (conc.at[kind, "top1_share"], "pct1")
        v[f"{k}_top5_share"] = (conc.at[kind, "top5_share"], "pct1")
        v[f"{k}_top10_share"] = (conc.at[kind, "top10_share"], "pct1")
        v[f"{k}_ids_50"] = (conc.at[kind, "ids_for_50pct"], "int")
        v[f"{k}_ids_80"] = (conc.at[kind, "ids_for_80pct"], "int")
        top = tables[tables.error_type == kind].head(10)
        v[f"{k}_top1_id"] = (top.patient_id.iloc[0], "str")
        v[f"{k}_top1_count"] = (top.errors.iloc[0], "int")
        v[f"{k}_top1_cells"] = (top.cells_at_risk.iloc[0], "int")
        v[f"{k}_top1_rate"] = (top.error_rate.iloc[0], "pct1")
        v[f"{k}_top1_fold"] = (top.fold.iloc[0], "int")
        t[f"top10_{k}"] = Table(
            [("Rank", "int"), ("Patient-ID", "str"), ("Fold", "int"), ("Cells at risk", "int"), (f"{kind}", "int"), ("Rate", "pct1"), ("Share of all", "pct1"), ("Cumulative", "pct1")],
            [[r.rank, r.patient_id, r.fold, r.cells_at_risk, r.errors, r.error_rate, r.share_of_errors, r.cumulative_share_of_errors] for r in top.itertuples()],
            "rlrrrrrr",
        )
    by_fold = _read(root, "m5/errors_by_fold.csv")
    t["errors_by_fold"] = Table(
        [("Fold", "int"), ("FN", "int"), ("FP", "int"), ("Pooled FNR", "pct1"), ("Pooled FPR", "pct1"), ("Top FN Patient-ID", "str"), ("Its share of fold FN", "pct1")],
        [[r.fold, r.false_negatives, r.false_positives, r.pooled_fnr, r.pooled_fpr, r.top_fn_patient_id, r.top_fn_share_of_fold] for r in by_fold.itertuples()],
        "rrrrrlr",
    )
    f2 = by_fold.set_index("fold").loc[positive_fold]
    v["posfold_fn"] = (f2.false_negatives, "int")
    v["posfold_top_fn_id"] = (f2.top_fn_patient_id, "str")
    v["posfold_top_fn_count"] = (f2.top_fn_count, "int")
    v["posfold_top_fn_share"] = (f2.top_fn_share_of_fold, "pct1")
    v["posfold_top_fn_npos"] = (f2.top_fn_n_positive, "int")
    v["max_fold_fn"] = (by_fold.false_negatives.max(), "int")
    v["min_fold_fn"] = (by_fold.false_negatives.min(), "int")
    vs_cells = _read(root, "m5/errors_vs_cells.csv")
    t["errors_vs_cells"] = Table(
        [("Parasitized cells per ID", "str"), ("IDs", "int"), ("Cells", "int"), ("FN", "int"), ("Share of all FN", "pct1"), ("Pooled FNR", "pct1"), ("Mean per-ID FNR", "pct1"), ("Max per-ID FNR", "pct1")],
        [[r.cells_bin, r.n_ids, r.parasitized_cells, r.false_negatives, r.share_of_all_fn, r.pooled_fnr, r.mean_id_fnr, r.max_id_fnr] for r in vs_cells.itertuples()],
        "lrrrrrrr",
    )
    big = vs_cells[vs_cells.cells_bin.isin(["100-299", "300+"])]
    v["fn_share_big_ids"] = (big.false_negatives.sum() / vs_cells.false_negatives.sum(), "pct1")
    v["n_big_ids"] = (big.n_ids.sum(), "int")
    small = vs_cells[vs_cells.cells_bin == "1-9"].iloc[0]
    v["small_ids"] = (small.n_ids, "int")
    v["small_ids_fn_share"] = (small.share_of_all_fn, "pct1")
    rho = _read(root, "m5/errors_vs_cells_spearman.csv").set_index("error_type")
    v["rho_fn"] = (rho.at["FN", "spearman_rho"], "num2")
    v["rho_fp"] = (rho.at["FP", "spearman_rho"], "num2")
    conf = _read(root, "m5/confident_errors_summary.csv").set_index("error_type")
    for kind in ("FN", "FP"):
        k = kind.lower()
        v[f"conf_{k}"] = (conf.at[kind, "confident_errors"], "int")
        v[f"conf_{k}_share"] = (conf.at[kind, "share_of_errors"], "pct1")
        v[f"conf_{k}_ids"] = (conf.at[kind, "n_patient_ids"], "int")
        v[f"conf_{k}_top_id"] = (conf.at[kind, "top_patient_id"], "str")
        v[f"conf_{k}_top_count"] = (conf.at[kind, "top_patient_id_count"], "int")
        v[f"conf_{k}_top_share"] = (conf.at[kind, "top_patient_id_share"], "pct1")
    cal = _read(root, "m5/calibration_summary.csv")
    cal["fold"] = cal.fold.astype(str)
    overall = cal[cal.fold == "all"].iloc[0]
    per_fold = cal[cal.fold != "all"]
    v["brier"] = (overall.brier, "num4")
    v["ece"] = (overall.ece, "num4")
    worst_brier = per_fold.loc[per_fold.brier.idxmax()]
    v["brier_worst_fold"] = (int(worst_brier.fold), "int")
    v["brier_worst"] = (worst_brier.brier, "num4")
    v["brier_best"] = (per_fold.brier.min(), "num4")
    bins = _read(root, "m5/calibration_bins.csv")
    v["cal_max_gap"] = (bins.abs_gap.max(), "num3")
    v["cal_extreme_share"] = ((bins.n_cells.iloc[0] + bins.n_cells.iloc[-1]) / bins.n_cells.sum(), "pct1")
    drivers = _read(root, "m5/sensitivity_sd_drivers.csv")
    largest = drivers[drivers.largest_sd_fold.astype(str) == "True"].iloc[0]
    v["sd_fold"] = (int(largest.fold), "int")
    v["sd_value"] = (largest.id_sensitivity_sd, "num3")
    v["sd_driver"] = (largest.driver_patient_id, "str")
    v["sd_without"] = (largest.sd_without_driver, "num3")
    v["sd_reduction_share"] = (largest.sd_reduction_share, "pct1")
    v["sd_driver_sens"] = (largest.driver_sensitivity, "pct1")
    v["sd_driver_npos"] = (int(largest.driver_n_positive), "int")
    v["sd_driver_fn_share"] = (largest.driver_share_of_fold_fn, "pct1")
    second = drivers.sort_values("id_sensitivity_sd", ascending=False).iloc[1]
    v["sd_second_fold"] = (int(second.fold), "int")
    v["sd_second_value"] = (second.id_sensitivity_sd, "num3")
    v["sd_reduction_share_max"] = (drivers.sd_reduction_share.max(), "pct1")
    t["sd_drivers"] = Table(
        [("Fold", "int"), ("SD per-ID sens.", "num3"), ("Most influential ID", "str"), ("Its sens.", "pct1"), ("Its cells", "int"), ("SD without it", "num3"), ("SD reduction", "pct1")],
        [[r.fold, r.id_sensitivity_sd, r.driver_patient_id, r.driver_sensitivity, r.driver_n_positive, r.sd_without_driver, r.sd_reduction_share] for r in drivers.itertuples()],
        "rrlrrrr",
    )

    # ---------------------------------------------------------------- M5 image level
    verification = json.loads((root / "results" / "m5" / "dataset_verification.json").read_text())
    v["dataset_verified"] = ("PASS" if verification["passed"] else "FAIL", "str")
    v["images_verified"] = (verification["images"]["verified"], "int")
    v["archive_sha_short"] = (verification["files"]["archive"]["sha256"][:12], "str")
    counts_path = root / "results" / "m5" / "image_review_counts.csv"
    if counts_path.exists():
        counts = _read(root, "m5/image_review_counts.csv").set_index("group")
        names = {
            "top_false_negative": ("Top FN (lowest p)", "tfn"),
            "top_false_positive": ("Top FP (highest p)", "tfp"),
            "random_true_positive": ("Random TP", "rtp"),
            "random_true_negative": ("Random TN", "rtn"),
        }
        rows = []
        for group, (label, key) in names.items():
            row = counts.loc[group]
            for column in ("n_cells", "n_patient_ids", "inclusion_yes", "inclusion_no", "inclusion_unclear", "pale_or_atypical_stain", "blur_or_low_contrast", "segmentation_artefact", "possible_label_noise"):
                v[f"rev_{key}_{column}"] = (row[column], "int")
            rows.append([label, row.n_cells, row.n_patient_ids, row.inclusion_yes, row.inclusion_no, row.inclusion_unclear, row.pale_or_atypical_stain, row.blur_or_low_contrast, row.segmentation_artefact, row.possible_label_noise])
        t["image_review"] = Table(
            [("Group (blind review)", "str"), ("Cells", "int"), ("IDs", "int"), ("Inclusion yes", "int"), ("No", "int"), ("Unclear", "int"), ("Grey/blue or atypical stain", "int"), ("Blur", "int"), ("Segmentation artefact", "int"), ("Possible label noise", "int")],
            rows,
            "lrrrrrrrrr",
        )
        v["rev_total"] = (int(counts.n_cells.sum()), "int")
    worst = _read(root, "m5/worst_patient_ids.csv")
    v["worst_ids"] = (", ".join(f"{r.patient_id} (fold {r.fold}, sensitivity {fmt(r.sensitivity, 'pct1')}, {r.n_positive} cells)" for r in worst.itertuples()), "str")


def _cell(cell: object, kind: str, target: str) -> str:
    if _is_nan(cell):
        return "" if target == "md" else "--"
    if kind == "cell":  # the cell carries its own (value, kind)
        cell, kind = cell
    return fmt(cell, kind, target)


def table_markdown(table: Table) -> str:
    header = "| " + " | ".join(name for name, _ in table.columns) + " |"
    rule = "| " + " | ".join("---:" if a == "r" else ":---:" if a == "c" else "---" for a in table.align) + " |"
    body = ["| " + " | ".join(_cell(cell, kind, "md") for cell, (_, kind) in zip(row, table.columns)) + " |" for row in table.rows]
    return "\n".join([header, rule, *body])


def table_latex(table: Table) -> str:
    header = " & ".join(r"\textbf{" + tex_escape(name) + "}" for name, _ in table.columns) + r" \\"
    body = [" & ".join(_cell(cell, kind, "tex") for cell, (_, kind) in zip(row, table.columns)) + r" \\" for row in table.rows]
    return "\n".join([r"\begin{tabular}{" + table.align + "}", r"\toprule", header, r"\midrule", *body, r"\bottomrule", r"\end{tabular}"]) + "\n"


def _is_nan(cell: object) -> bool:
    return isinstance(cell, float) and cell != cell
