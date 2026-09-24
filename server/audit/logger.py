"""
ISO 9001 Compliance Audit Logger
Team 6 - AI Deployment, API Server & Client UX

Provides an append-only JSON Lines writer for full inspection traceability.
"""

import os
import json
import hashlib
import threading
from datetime import datetime, timezone

class AuditLogger:
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.dirname(__file__)
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "audit.jsonl")
        self._lock = threading.Lock()

    def write_record(self, image_bytes: bytes, hi_results: dict, alignment_quality: float,
                     processing_ms: float, board_serial: str = "AUTO-SERIAL-001",
                     system_version: str = "v1.0-frozen") -> dict:
        """
        Appends an immutable audit record to audit.jsonl.
        Returns the created record dict.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        image_sha256 = hashlib.sha256(image_bytes).hexdigest()
        record_id = f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')[:21]}"

        # Compute exact defect breakdown per record
        missing_cnt = 0
        tombstone_cnt = 0
        height_cnt = 0
        tilt_cnt = 0

        cat_defects = {
            "ICs": {"missing": 0, "rework": 0},
            "Capacitors": {"missing": 0, "rework": 0},
            "Resistors": {"missing": 0, "rework": 0},
            "Regulators": {"missing": 0, "rework": 0}
        }

        comps = hi_results.get("components", [])
        for c in comps:
            cid = c.get("id", "")
            if cid.startswith("C"):
                cat = "Capacitors"
            elif cid.startswith("VR"):
                cat = "Regulators"
            elif cid.startswith("R"):
                cat = "Resistors"
            elif cid.startswith("U"):
                cat = "ICs"
            else:
                cat = "ICs"

            if cat not in cat_defects:
                cat_defects[cat] = {"missing": 0, "rework": 0}

            if c.get("is_missing"):
                missing_cnt += 1
                cat_defects[cat]["missing"] += 1
            elif c.get("tombstone_flag"):
                tombstone_cnt += 1
                cat_defects[cat]["rework"] += 1
            elif c.get("tilt_flag"):
                tilt_cnt += 1
                cat_defects[cat]["rework"] += 1
            elif c.get("height_flag"):
                height_cnt += 1
                cat_defects[cat]["rework"] += 1

        record = {
            "record_id": record_id,
            "board_serial": board_serial,
            "timestamp_utc": timestamp,
            "image_sha256": image_sha256,
            "alignment_quality": round(float(alignment_quality), 4),
            "health_index": float(hi_results["health_index"]),
            "verdict": hi_results["verdict"],
            "total_components": hi_results["total_components"],
            "defective_components": hi_results["defective_components"],
            "defect_breakdown": {
                "missing": missing_cnt,
                "tombstone": tombstone_cnt,
                "height": height_cnt,
                "tilt": tilt_cnt
            },
            "category_defects": cat_defects,
            "processing_time_ms": round(float(processing_ms), 2),
            "system_version": system_version
        }

        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

        return record

    def get_summary_stats(self) -> dict:
        """Reads audit.jsonl and computes session statistics."""
        with self._lock:
            if not os.path.exists(self.log_file):
                return {
                    "boards_inspected": 0,
                    "pass_count": 0,
                    "rework_count": 0,
                    "fail_count": 0,
                    "session_fpy": 0.0,
                    "dpmo": 0.0,
                    "avg_processing_ms": 0.0
                }

            inspected = 0
            passes = 0
            reworks = 0
            fails = 0
            total_ms = 0.0
            total_defects = 0
            total_opportunities = 0

            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    inspected += 1
                    v = data.get("verdict", "FAIL")
                    if v == "PASS":
                        passes += 1
                    elif v == "REWORK":
                        reworks += 1
                    else:
                        fails += 1

                    total_ms += data.get("processing_time_ms", 0.0)
                    total_defects += data.get("defective_components", 0)
                    total_opportunities += data.get("total_components", 10)

        fpy = passes / float(max(1, inspected))
        avg_ms = total_ms / float(max(1, inspected))
        dpmo = (total_defects / float(max(1, total_opportunities))) * 1e6

        return {
            "boards_inspected": inspected,
            "pass_count": passes,
            "rework_count": reworks,
            "fail_count": fails,
            "session_fpy": round(fpy, 4),
            "dpmo": round(dpmo, 2),
            "avg_processing_ms": round(avg_ms, 2)
        }
