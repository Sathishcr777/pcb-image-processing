"""
Health Index & IPC-A-610H Quality Engine
Team 5 - Model Optimization & Sub-Team A

Computes continuous PCB Health Index (HI), maps IPC-A-610H quality verdicts,
and calculates Defects Per Million Opportunities (DPMO).
"""

class HealthIndexCalculator:
    def __init__(self, pass_thresh=0.95, rework_thresh=0.80):
        self.pass_thresh = pass_thresh
        self.rework_thresh = rework_thresh

    def compute(self, components_config: list, results_2d: dict, results_depth: dict):
        """
        Computes continuous Health Index HI, IPC verdict, and detailed component breakdown.
        """
        total_weighted_score = 0.0
        total_weight = 0.0
        defective_count = 0
        component_details = []

        for comp in components_config:
            cid = comp["id"]
            name = comp["name"]
            weight = float(comp.get("weight", 1.0))

            res_2d = results_2d.get(cid, {"presence_score": 1.0, "is_missing": False, "ssim_score": 1.0})
            res_depth = results_depth.get(cid, {"height_penalty": 0.0, "height_flag": False, "tilt_flag": False, "tombstone_flag": False})

            is_missing = res_2d["is_missing"]
            p_i = 0.0 if is_missing else float(res_2d["presence_score"])
            h_i = float(res_depth["height_penalty"])

            tilt_flag = res_depth["tilt_flag"]
            tombstone_flag = res_depth["tombstone_flag"]
            height_flag = res_depth["height_flag"]

            is_defective = is_missing or height_flag or tilt_flag or tombstone_flag
            if is_defective:
                defective_count += 1

            # Component contribution = w_i * p_i * (1 - h_i)
            comp_score = weight * (0.0 if is_missing else p_i) * (1.0 - (0.0 if is_missing else h_i))
            total_weighted_score += comp_score
            total_weight += weight
            # 3D structural tombstone/tilt defects take priority over 2D missing flag because the component is present (tilted/tombstoned)
            if tombstone_flag:
                comp_status = "TOMBSTONE"
                is_missing = False
            elif tilt_flag:
                comp_status = "TILT"
                is_missing = False
            elif is_missing:
                comp_status = "MISSING"
            elif height_flag:
                comp_status = "HEIGHT_ANOMALY"
            else:
                comp_status = "PASS"

            component_details.append({
                "id": cid,
                "name": name,
                "weight": weight,
                "is_missing": is_missing,
                "ssim_score": round(res_2d["ssim_score"], 4),
                "height_penalty": round(h_i, 4),
                "height_flag": height_flag,
                "tilt_flag": tilt_flag,
                "tombstone_flag": tombstone_flag,
                "is_defective": is_defective,
                "status": comp_status,
                "bbox_px": comp["bbox_xywh"]
            })

        if total_weight > 0:
            hi = float(total_weighted_score / total_weight)
        else:
            hi = 0.0

        hi = round(float(max(0.0, min(1.0, hi))), 4)

        # Map IPC-A-610H Verdict
        if hi >= self.pass_thresh and defective_count == 0:
            verdict = "PASS"
        elif hi >= self.rework_thresh:
            verdict = "REWORK"
        else:
            verdict = "FAIL"

        return {
            "health_index": hi,
            "verdict": verdict,
            "total_components": len(components_config),
            "defective_components": defective_count,
            "components": component_details
        }

    @staticmethod
    def calculate_dpmo(defective_opportunities: int, total_inspected_boards: int, opp_per_board: int) -> float:
        """Computes Defects Per Million Opportunities (DPMO)."""
        total_opportunities = max(1, total_inspected_boards * opp_per_board)
        return float((defective_opportunities / total_opportunities) * 1e6)
