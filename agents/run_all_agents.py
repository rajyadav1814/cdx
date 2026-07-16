"""
CDX — Commercial Signal Intelligence Engine
Pipeline Orchestrator — runs all 4 agents in sequence.

Agents run strictly in order: 1 → 2 → 3 → 4.
Each agent's output CSV is verified before the next agent starts.
Individual agent failures are logged but do not halt the pipeline.

When DATABASE_URL is configured the orchestrator shares a single run_id
across all four agents so their results are queryable as one unit.
"""

import sys
import os
import json
import traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

# ─── DB helpers (optional) ───────────────────────────────────────────────────────
try:
    from db.readers import get_latest_run_id
    _DB_ENABLED = True
except Exception:
    _DB_ENABLED = False

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')



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

    # run_id is created by agent1 in the DB; extract it after agent1 completes
    shared_run_id: str | None = None

    for num in (1, 2, 3, 4):
        print(f"\n  ▶  {labels[num]}")
        print("  " + "─" * 48)

        # Check if previous agent succeeded
        if num > 1 and agent_status.get(num - 1) != "ok":
            msg = f"Prerequisite agent {num-1} did not succeed."
            print(f"  ✗ SKIPPED — {msg}")
            agent_status[num] = "skipped"
            agent_errors[num] = msg
            continue

        try:
            if num == 1:
                results = runners[num]()
            else:
                results = runners[num](shared_run_id)
                
            agent_results[num] = results if results else []

            if not agent_results[num]:
                raise ValueError(f"Agent returned no results")

            agent_status[num] = "ok"
            print(f"\n  ✓  {labels[num]} complete — {len(agent_results[num])} artists")

            # After agent1 completes, capture the run_id it created in the DB
            if num == 1 and _DB_ENABLED and shared_run_id is None:
                try:
                    shared_run_id = get_latest_run_id()
                    if shared_run_id:
                        print(f"  [DB] shared run_id: {shared_run_id}")
                except Exception as _e:
                    print(f"  [DB] could not fetch run_id: {_e}")

        except Exception as e:
            tb = traceback.format_exc()
            agent_status[num] = "failed"
            agent_errors[num]  = str(e)
            agent_results[num] = []
            print(f"\n  ✗  {labels[num]} FAILED: {e}")
            print(tb)

    # ── Summary ───────────────────────────────
    run_ts = datetime.now(timezone.utc).isoformat(timespec='seconds')
    
    # We no longer generate a local pipeline_summary.json 
    # since the backend API provides it via db.readers.read_pipeline_summary()
    # But we can still read it from DB here to print the final output
    try:
        from db.readers import read_pipeline_summary
        summary = read_pipeline_summary()
    except Exception:
        summary = {
            "run_timestamp": run_ts,
            "artists_processed": len(agent_results.get(1, [])),
            "agent1": {"status": agent_status.get(1, "ok")},
            "agent2": {"status": agent_status.get(2, "ok")},
            "agent3": {"status": agent_status.get(3, "ok")},
            "agent4": {"status": agent_status.get(4, "ok")},
        }

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
