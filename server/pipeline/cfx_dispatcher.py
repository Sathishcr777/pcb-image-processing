"""
Industry 4.0 IPC-CFX (Connected Factory Exchange) & MES Telemetry Dispatcher
Team 6 - Enterprise Factory Automation & Industry 4.0 Standards

Dispatches IPC-CFX-2591 standard JSON events for automated Pick-and-Place machine feedback.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

class CFXDispatcher:
    def __init__(self, line_id: str = "SMT-LINE-01", station_id: str = "AOI-OPTICAL-01"):
        self.line_id = line_id
        self.station_id = station_id
        self.event_history: List[Dict] = []
        self.max_history = 100

    def generate_inspection_event(
        self,
        board_serial: str,
        hi_results: Dict,
        metrology_results: List[Dict],
        processing_ms: float
    ) -> Dict:
        """
        Generates standard IPC-CFX Production.AssemblyInspectionCompleted payload.
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        defects = []
        drift_alerts = []

        for comp in hi_results.get("components", []):
            cid = comp["id"]
            status = comp.get("status", "PASS")
            
            # Find matching metrology data
            metro = next((m for m in metrology_results if m.get("component_id") == cid), {})
            
            if status != "PASS":
                defects.append({
                    "ComponentDesignator": cid,
                    "DefectCategory": status,
                    "IPCVerdict": metro.get("ipc_class_verdict", "DEFECT"),
                    "SeverityScore": round(float(1.0 - comp.get("presence_score", 1.0) * (1.0 - comp.get("height_penalty", 0.0))), 3),
                    "MeasuredOffset": {
                        "DeltaX_mm": metro.get("delta_x_mm", 0.0),
                        "DeltaY_mm": metro.get("delta_y_mm", 0.0),
                        "Rotation_deg": metro.get("rotation_deg", 0.0),
                        "Overhang_pct": metro.get("max_overhang_pct", 0.0)
                    }
                })

            # Check for proactive process drift (rotations > 2 deg or overhang > 15% even if passing)
            elif abs(metro.get("rotation_deg", 0.0)) > 2.0 or metro.get("max_overhang_pct", 0.0) > 15.0:
                drift_alerts.append({
                    "ComponentDesignator": cid,
                    "DriftType": "ROTATIONAL_DRIFT" if abs(metro.get("rotation_deg", 0.0)) > 2.0 else "PLACEMENT_OFFSET_DRIFT",
                    "DeltaTheta": metro.get("rotation_deg", 0.0),
                    "OverhangPct": metro.get("max_overhang_pct", 0.0),
                    "RecommendedAction": "RECALIBRATE_FEEDER_NOZZLE"
                })

        cfx_payload = {
            "CFXMessage": {
                "Header": {
                    "MessageId": event_id,
                    "MessageType": "CFX.Production.AssemblyInspectionCompleted",
                    "Timestamp": timestamp,
                    "Source": f"{self.line_id}.{self.station_id}",
                    "Version": "1.4"
                },
                "Body": {
                    "BoardSerialNumber": board_serial,
                    "InspectionResult": hi_results.get("verdict", "PASS"),
                    "HealthIndex": hi_results.get("health_index", 1.0),
                    "TotalOpportunities": hi_results.get("total_components", 12),
                    "DefectCount": len(defects),
                    "InspectionCycleTimeMs": round(processing_ms, 2),
                    "DefectList": defects,
                    "ProcessDriftWarnings": drift_alerts,
                    "MESDisposition": "ROUTE_TO_PACKAGING" if hi_results.get("verdict") == "PASS" else "ROUTE_TO_REWORK_STATION"
                }
            }
        }

        # Store in circular buffer
        self.event_history.append(cfx_payload)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        return cfx_payload

    def get_recent_events(self, limit: int = 15) -> List[Dict]:
        return list(reversed(self.event_history[-limit:]))
