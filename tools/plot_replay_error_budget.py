"""Optional matplotlib figures for the affine replay research pilot."""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    if report["report_kind"] != "babcs.affine-replay-error-budget-pilot.v1":
        raise ValueError("unsupported report kind")
    outputs = [args.output_directory / f"replay-error-budget.{suffix}" for suffix in ("svg", "png")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("figure output already exists")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({"svg.hashsalt": "babcs-replay-budget-v1", "font.size": 10})

    def select(case, interval=4, initial="0"):
        return next(r for r in report["rows"] if r["case"] == case and r["step"] == "1/20"
                    and r["anchor_interval"] == interval and r["initial_radius"] == initial
                    and r["refinement"] == 4 and not r["reference_only"])

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    for ax, name, label in ((axes[0, 0], "rc_decay", "RC decay"),
                             (axes[1, 0], "lc_neutral", "Neutral LC")):
        points = select(name)["points"]
        time = [float(Fraction(p["time"])) for p in points]
        ax.semilogy(time, [p["radius_float"] for p in points], color="#176b87", label="Total-error upper bound")
        ax.semilogy(time, [p["central_trajectory_error_diagnostic"] for p in points],
                    color="#bd5b24", label="Independent error diagnostic")
        anchors = [p for p in points if p["replay"]]
        ax.scatter([float(Fraction(p["time"])) for p in anchors],
                   [p["radius_float"] for p in anchors], s=20, color="#176b87")
        ax.set(title=f"{label}: error grows between replay anchors", xlabel="Dimensionless time",
               ylabel="State-norm error (log scale)")
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8, loc="lower left")

    ax = axes[0, 1]
    rows = [select("rc_decay", interval) for interval in (1, 4, 16)]
    ax.bar([0, 1, 2], [r["max_central_error_diagnostic"] for r in rows], color="#bd5b24", width=0.6)
    ax.set_yscale("log")
    ax.set_xticks([0, 1, 2], ["Every step", "Every 4 steps", "Every 16 steps"])
    ax.set(title="RC: longer windows do not save replay steps", ylabel="Peak accepted-state error (log scale)")
    for i, r in enumerate(rows):
        ax.text(i, r["max_central_error_diagnostic"] * 1.25, f'{r["replay_steps"]} replay steps',
                ha="center", fontsize=8)
    ax.set_ylim(1e-6, 0.04)
    ax.grid(axis="y", alpha=0.2)

    ax = axes[1, 1]
    anchors = [p for p in select("rc_decay", initial="1/1000")["points"] if p["replay"]]
    time = [float(Fraction(p["time"])) for p in anchors]
    inherited = [float(Fraction(p["inherited_anchor_radius"])) for p in anchors]
    fresh = [float(Fraction(p["fresh_replay_defect_radius"])) for p in anchors]
    ax.stackplot(time, inherited, fresh, labels=["Inherited anchor uncertainty", "Fresh window defect"],
                 colors=["#176b87", "#e5a04c"])
    ax.set(title="RC: replay retains inherited uncertainty", xlabel="Dimensionless time (replay endpoints)",
           ylabel="Total-error upper bound")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    fig.suptitle("Affine replay pilot — exact rational bounds, diagnostic trajectory errors", fontsize=14)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(outputs[0], metadata={"Date": None})
    fig.savefig(outputs[1], dpi=160)
    plt.close(fig)
    print("\n".join(map(str, outputs)))


if __name__ == "__main__":
    main()
