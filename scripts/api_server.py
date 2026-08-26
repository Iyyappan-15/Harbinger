# ============================================================
# Harbinger — api_server.py
# FastAPI REST backend for query fragility sweeps and history.
#
# Run with:
#   uvicorn scripts.api_server:app --reload --port 8000
# ============================================================

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.db_config import (
    SELECTIVITY_LEVELS, RUNS_PER_STATE, REGRESSION_THRESHOLD,
    TARGET_TABLE, PREDICATE_VAL, TOTAL_ROWS
)
from scripts.data_state_manager import verify_state
from scripts.harbinger_engine import run_full_sweep

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("harbinger_api")

app = FastAPI(
    title="Harbinger API",
    description="Backend API server for PostgreSQL Query Fragility Analysis",
    version="1.0"
)

# CORS middleware for local React/Vite development on standard ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SweepRequest(BaseModel):
    threshold: Optional[float] = None
    levels: Optional[List[int]] = None
    runs: Optional[int] = None
    save: Optional[bool] = True

@app.get("/api/status")
def get_status():
    """Returns the database connection health and target table statistics."""
    try:
        counts = verify_state(verbose=False)
        total = sum(counts.values())
        pending = counts.get(PREDICATE_VAL, 0)
        selectivity_pct = round((pending / total) * 100.0, 2) if total > 0 else 0.0
        
        return {
            "status": "healthy",
            "database_connected": True,
            "target_table": TARGET_TABLE,
            "total_rows": total,
            "pending_rows": pending,
            "selectivity_pct": selectivity_pct,
            "distribution": counts
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e)
        }

@app.post("/api/run-sweep")
def post_run_sweep(req: SweepRequest):
    """Triggers the dual-threshold query sweep."""
    # Override settings dynamically
    threshold = req.threshold if req.threshold is not None else REGRESSION_THRESHOLD
    levels = sorted(req.levels) if req.levels is not None else sorted(SELECTIVITY_LEVELS)
    runs = req.runs if req.runs is not None else RUNS_PER_STATE

    import config.db_config as cfg
    original_levels = cfg.SELECTIVITY_LEVELS
    original_runs = cfg.RUNS_PER_STATE
    original_threshold = cfg.REGRESSION_THRESHOLD

    cfg.SELECTIVITY_LEVELS = levels
    cfg.RUNS_PER_STATE = runs
    cfg.REGRESSION_THRESHOLD = threshold

    try:
        logger.info(f"Starting sweep (threshold={threshold}, levels={levels}, runs={runs})")
        summary = run_full_sweep(regression_threshold=threshold, verbose=False)
        
        # Save results locally if requested
        if req.save:
            os.makedirs("results", exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_path = f"results/sweep_{ts}.json"
            
            # Save clean JSON results
            clean_summary = {k: v for k, v in summary.items() if k != 'results'}
            clean_summary['results'] = []
            for row in summary['results']:
                clean_row = {k: v for k, v in row.items()}
                clean_summary['results'].append(clean_row)
                
            clean_summary['generated_at'] = datetime.now().isoformat()
            with open(json_path, 'w') as f:
                json.dump(clean_summary, f, indent=2)
                
            summary["saved_file"] = json_path
            
        return summary
    except Exception as e:
        logger.error(f"Sweep execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Restore configuration values
        cfg.SELECTIVITY_LEVELS = original_levels
        cfg.RUNS_PER_STATE = original_runs
        cfg.REGRESSION_THRESHOLD = original_threshold

@app.get("/api/history")
def get_history():
    """Scans results/ directory and returns list of past execution summary metadata."""
    results_dir = "results"
    if not os.path.exists(results_dir):
        return []
        
    runs = []
    try:
        for fname in os.listdir(results_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(results_dir, fname)
                try:
                    with open(fpath, 'r') as f:
                        data = json.load(f)
                        runs.append({
                            "filename": fname,
                            "timestamp": data.get("generated_at", ""),
                            "target_table": data.get("target_table", ""),
                            "ft_runtime": data.get("ft_runtime"),
                            "ptt": data.get("ptt"),
                            "risk_classification": data.get("risk_classification", ""),
                            "baseline_median_ms": data.get("baseline_median_ms", 0.0)
                        })
                except Exception as ex:
                    logger.warning(f"Failed to read {fname}: {ex}")
                    
        # Sort by timestamp descending
        runs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{filename}")
def get_history_detail(filename: str):
    """Returns the full data of a specific historical run."""
    results_dir = "results"
    fpath = os.path.join(results_dir, filename)
    if not os.path.exists(fpath) or not filename.endswith(".json"):
        raise HTTPException(status_code=404, detail="Historical run file not found")
        
    try:
        with open(fpath, 'r') as f:
            data = json.load(f)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
