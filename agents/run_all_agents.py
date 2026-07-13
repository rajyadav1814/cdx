"""
CDX — Commercial Signal Intelligence Engine
Pipeline Orchestrator — runs all 4 agents in sequence.

Agents run strictly in order: 1 → 2 → 3 → 4.
Each agent's output CSV is verified before the next agent starts.
Individual agent failures are logged but do not halt the pipeline.
"""

import sys
import os
import json
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

AGENT_PREREQS = {
    1: None,
    2: os.path.join(DATA_DIR, 'agent1_output.csv'),
    3: os.path.join(DATA_DIR, 'agent2_output.csv'),
    4: os.path.join(DATA_DIR, 'agent3_output.csv'),
}
AGENT_OUTPUTS = {
    1: os.path.join(DATA_DIR, 'agent1_output.csv'),
    2: os.path.join(DATA_DIR, 'agent2_output.csv'),
    3: os.path.join(DATA_DIR, 'agent3_output.csv'),
    4: os.path.join(DATA_DIR, 'agent4_output.csv'),
}

SEP = "━" * 52


def run_pipeline():
    print(SEP)
    print("  CDX — CSIE Pipeline Starting")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(SEP)

    agent_results = {}   # agent_num → list[dict] returned by run_agent()
    agent_status  = {}   # agent_num → "ok" | "failed" | "skipped"
    agent_errors  = {}   # agent_num → error string

    # ── Import all agents up front ────────────────────────────────
    from agents.agent1_opportunity import run_agent as run1
    from agents.agent2_strategy    import run_agent as run2
    from agents.agent3_audience    import run_agent as run3
    from agents.agent4_roi         import run_agent as run4

    runners = {1: run1, 2: run2, 3: run3, 4: run4}
    labels  = {
        1: "Agent 1: Opportunity Discovery",
        2: "Agent 2: Strategy Synthesis",
        3: "Agent 3: Audience-Fit",
        4: "Agent 4: ROI Forecast",
    }

    for num in (1, 2, 3, 4):
        print(f"\n  ▶  {labels[num]}")
        print("  " + "─" * 48)

        # Check prerequisite CSV
        prereq = AGENT_PREREQS[num]
        if prereq and not os.path.exists(prereq):
            msg = f"Prerequisite missing: {os.path.basename(prereq)}"
            print(f"  ✗ SKIPPED — {msg}")
            agent_status[num] = "skipped"
            agent_errors[num] = msg
            continue

        try:
            results = runners[num]()
            agent_results[num] = results if results else []

            # Verify output was written
            out_path = AGENT_OUTPUTS[num]
            if not os.path.exists(out_path):
                raise FileNotFoundError(f"Output not created: {os.path.basename(out_path)}")

            agent_status[num] = "ok"
            print(f"\n  ✓  {labels[num]} complete — {len(agent_results[num])} artists")

        except Exception as e:
            tb = traceback.format_exc()
            agent_status[num] = "failed"
            agent_errors[num]  = str(e)
            agent_results[num] = []
            print(f"\n  ✗  {labels[num]} FAILED: {e}")
            print(tb)

    # ── Build pipeline_summary.json ───────────────────────────────
    run_ts = datetime.now(timezone.utc).isoformat(timespec='seconds')

    def _agent1_summary():
        path = AGENT_OUTPUTS[1]
        if not os.path.exists(path):
            return {"status": agent_status.get(1, "skipped")}
        df = pd.read_csv(path)
        counts = df['opportunity_class'].value_counts().to_dict()
        top = df.sort_values('momentum_score', ascending=False).iloc[0]['artist_name'] if len(df) else ""
        return {
            "status":               agent_status.get(1, "ok"),
            "high_opportunities":   int(counts.get('HIGH',   0)),
            "medium_opportunities": int(counts.get('MEDIUM', 0)),
            "watch_opportunities":  int(counts.get('WATCH',  0)),
            "top_artist":           top,
            **( {"error": agent_errors[1]} if 1 in agent_errors else {} ),
        }

    def _agent2_summary():
        path = AGENT_OUTPUTS[2]
        if not os.path.exists(path):
            return {"status": agent_status.get(2, "skipped")}
        df = pd.read_csv(path)
        cat_dist = df['best_brand_category'].value_counts().to_dict()
        channel  = df['recommended_channel'].mode().iloc[0] if len(df) else ""
        return {
            "status":                        agent_status.get(2, "ok"),
            "briefs_generated":              len(df),
            "best_brand_category_distribution": {k: int(v) for k, v in cat_dist.items()},
            "most_common_channel":           channel,
            **( {"error": agent_errors[2]} if 2 in agent_errors else {} ),
        }

    def _agent3_summary():
        path = AGENT_OUTPUTS[3]
        if not os.path.exists(path):
            return {"status": agent_status.get(3, "skipped")}
        df = pd.read_csv(path)
        total = len(df)
        conf_cts = df['data_confidence'].value_counts()
        return {
            "status":               agent_status.get(3, "ok"),
            "avg_reach":            int(df['total_reach'].mean()) if total else 0,
            "high_confidence_pct":  round(conf_cts.get('HIGH',   0) / total * 100, 1) if total else 0,
            "medium_confidence_pct":round(conf_cts.get('MEDIUM', 0) / total * 100, 1) if total else 0,
            "low_confidence_pct":   round(conf_cts.get('LOW',    0) / total * 100, 1) if total else 0,
            **( {"error": agent_errors[3]} if 3 in agent_errors else {} ),
        }

    def _agent4_summary():
        path = AGENT_OUTPUTS[4]
        if not os.path.exists(path):
            return {"status": agent_status.get(4, "skipped")}
        df = pd.read_csv(path)
        if len(df) == 0:
            return {"status": agent_status.get(4, "ok")}
        best = df.nlargest(1, 'base_roi').iloc[0]
        return {
            "status":                  agent_status.get(4, "ok"),
            "avg_base_roi":            round(float(df['base_roi'].mean()), 4),
            "highest_roi_artist":      best['artist_name'],
            "highest_roi_multiple":    round(float(best['base_roi']), 4),
            "total_projected_revenue": int(df['base_revenue'].sum()),
            **( {"error": agent_errors[4]} if 4 in agent_errors else {} ),
        }

    # Count total artists processed (from agent1 as the source)
    a1_path = AGENT_OUTPUTS[1]
    n_artists = len(pd.read_csv(a1_path)) if os.path.exists(a1_path) else 0

    summary = {
        "run_timestamp":      run_ts,
        "artists_processed":  n_artists,
        "agent1":             _agent1_summary(),
        "agent2":             _agent2_summary(),
        "agent3":             _agent3_summary(),
        "agent4":             _agent4_summary(),
    }

    summary_path = os.path.join(DATA_DIR, 'pipeline_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Written → {summary_path}")

    # ── Final console report ───────────────────────────────────────
    a1 = summary['agent1']
    a2 = summary['agent2']
    a3 = summary['agent3']
    a4 = summary['agent4']

    print("\n" + SEP)
    print("  CDX — CSIE Pipeline Complete")
    print(SEP)

    if a1.get('status') == 'ok':
        print(f"  Agent 1: {a1.get('high_opportunities',0)} high, "
              f"{a1.get('medium_opportunities',0)} medium opportunities. "
              f"Top: {a1.get('top_artist','—')}")
    else:
        print(f"  Agent 1: {a1.get('status','—').upper()} — {a1.get('error','')}")

    if a2.get('status') == 'ok':
        cat_dist = a2.get('best_brand_category_distribution', {})
        top_cat  = max(cat_dist, key=cat_dist.get) if cat_dist else '—'
        print(f"  Agent 2: {a2.get('briefs_generated',0)} briefs. "
              f"Most matched category: {top_cat}")
    else:
        print(f"  Agent 2: {a2.get('status','—').upper()} — {a2.get('error','')}")

    if a3.get('status') == 'ok':
        reach_m = a3.get('avg_reach', 0) / 1_000_000
        print(f"  Agent 3: avg reach {reach_m:.1f}M. "
              f"High confidence: {a3.get('high_confidence_pct',0)}%")
    else:
        print(f"  Agent 3: {a3.get('status','—').upper()} — {a3.get('error','')}")

    if a4.get('status') == 'ok':
        print(f"  Agent 4: avg base ROI {a4.get('avg_base_roi',0):.3f}x. "
              f"Best artist: {a4.get('highest_roi_artist','—')} "
              f"at {a4.get('highest_roi_multiple',0):.3f}x")
    else:
        print(f"  Agent 4: {a4.get('status','—').upper()} — {a4.get('error','')}")

    print(SEP)

    return summary


if __name__ == "__main__":
    run_pipeline()
