"""
Visualization & Overlay Renderer with Metrology Callouts
Team 6 - AI Deployment, API Server & Client UX

Draws:
1. Multi-shape defect markers (Missing, Height, Tombstone, Tilt, Pass)
2. Quantitative Metrology Overlays (Shift vectors Delta X, Delta Y, Rotation Delta Theta, Overhang %)
3. Continuous Health Index gradient bar & IPC-A-610 Class verdict badge
4. Bottom-Right Legend, Metrology Summary & Latency Tag
"""

import cv2
import numpy as np
import base64
from typing import Dict, List, Optional

class PCBVisualizer:
    def __init__(self):
        # Marker Colors (BGR format matching modern industrial UI)
        self.COLOR_MISSING = (68, 68, 239)      # Red #EF4444
        self.COLOR_TOMBSTONE = (11, 158, 245)   # Amber/Yellow #F59E0B
        self.COLOR_HEIGHT = (212, 182, 6)       # Cyan #06B6D4
        self.COLOR_TILT = (247, 85, 168)        # Magenta/Purple #A855F7
        self.COLOR_PASS = (129, 185, 16)        # Green #10B981
        self.COLOR_METRO_ARROW = (0, 255, 255)  # Yellow shift vector

    def draw_overlay(
        self,
        img: np.ndarray,
        hi_results: dict,
        metrology_results: Optional[List[dict]] = None,
        processing_ms: float = 0.0
    ) -> np.ndarray:
        """
        Draws visual defect markers and quantitative metrology vectors.
        """
        overlay = img.copy()
        h, w = overlay.shape[:2]

        hi = hi_results.get("health_index", 1.0)
        verdict = hi_results.get("verdict", "PASS")
        components = hi_results.get("components", [])
        metrology_dict = {m["component_id"]: m for m in (metrology_results or []) if "component_id" in m}

        # 1. Top Health Index Banner (Gradient Bar)
        banner_h = 45
        cv2.rectangle(overlay, (0, 0), (w, banner_h), (25, 25, 25), -1)

        # Draw HI Bar
        bar_w = int((w - 400) * hi)
        bar_color = (
            int(255 * (1 - hi)),
            int(200 * hi),
            40
        )
        cv2.rectangle(overlay, (200, 10), (200 + bar_w, banner_h - 10), bar_color, -1)
        cv2.rectangle(overlay, (200, 10), (w - 200, banner_h - 10), (150, 150, 150), 2)
        cv2.putText(overlay, f"HEALTH INDEX: {hi:.3f}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 2. IPC Verdict Badge (Top-Right)
        if verdict == "PASS":
            v_color = (0, 180, 0)
        elif verdict == "REWORK":
            v_color = (0, 140, 255)
        else:
            v_color = (0, 0, 220)

        cv2.rectangle(overlay, (w - 180, 5), (w - 10, banner_h - 5), v_color, -1)
        cv2.putText(overlay, verdict, (w - 160, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # 3. Component ROI Annotation Markers & Metrology Vectors
        for comp in components:
            cid = comp["id"]
            x, y, cw, ch = comp["bbox_px"]
            status = comp["status"]
            metro = metrology_dict.get(cid, {})

            cx, cy = x + cw // 2, y + ch // 2
            dx_px = metro.get("delta_x_px", 0.0)
            dy_px = metro.get("delta_y_px", 0.0)
            rot_deg = metro.get("rotation_deg", 0.0)
            overhang = metro.get("max_overhang_pct", 0.0)

            metro_label = f"[{cid}] rot:{rot_deg:+.1f}d ovh:{overhang:.0f}%"

            if status == "MISSING":
                # 🔴 Rounded circle enclosing missing part
                radius = int(max(cw, ch) / 1.4) + 6
                cv2.circle(overlay, (cx, cy), radius, self.COLOR_MISSING, 4)
                cv2.circle(overlay, (cx, cy), radius + 3, (255, 255, 255), 1)
                cv2.circle(overlay, (cx, cy), 6, self.COLOR_MISSING, -1)
                cv2.rectangle(overlay, (x, y), (x + cw, y + ch), self.COLOR_MISSING, 2)

                cv2.rectangle(overlay, (x - 5, y - 24), (x + len(cid)*14 + 75, y - 2), (0, 0, 180), -1)
                cv2.putText(overlay, f"{cid} MISSING", (x, y - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            elif status == "HEIGHT_ANOMALY":
                # 🔵 Upward triangle
                pts = np.array([[cx, cy - 18], [cx - 16, cy + 14], [cx + 16, cy + 14]], np.int32)
                cv2.fillPoly(overlay, [pts], self.COLOR_HEIGHT)
                cv2.polylines(overlay, [pts], True, (255, 255, 255), 2)
                cv2.rectangle(overlay, (x, y), (x + cw, y + ch), self.COLOR_HEIGHT, 2)

                cv2.rectangle(overlay, (x - 5, y - 24), (x + len(metro_label)*7 + 10, y - 2), (0, 100, 200), -1)
                cv2.putText(overlay, f"{metro_label} HEIGHT", (x, y - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)

            elif status == "TOMBSTONE":
                # 🟡 Diamond
                pts = np.array([[cx, cy - 16], [cx + 16, cy], [cx, cy + 16], [cx - 16, cy]], np.int32)
                cv2.fillPoly(overlay, [pts], self.COLOR_TOMBSTONE)
                cv2.polylines(overlay, [pts], True, (0, 0, 0), 2)
                cv2.rectangle(overlay, (x, y), (x + cw, y + ch), self.COLOR_TOMBSTONE, 2)

                cv2.rectangle(overlay, (x - 5, y - 24), (x + len(metro_label)*7 + 10, y - 2), (180, 180, 0), -1)
                cv2.putText(overlay, f"{metro_label} TOMBSTONE", (x, y - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1)

            elif status == "TILT":
                # 🟣 Rotated square
                pts = np.array([[cx - 12, cy - 12], [cx + 12, cy - 12], [cx + 12, cy + 12], [cx - 12, cy + 12]], np.int32)
                cv2.fillPoly(overlay, [pts], self.COLOR_TILT)
                cv2.polylines(overlay, [pts], True, (255, 255, 255), 2)
                cv2.rectangle(overlay, (x, y), (x + cw, y + ch), self.COLOR_TILT, 2)

                # Draw physical shift vector arrow if shifted
                if abs(dx_px) > 2 or abs(dy_px) > 2:
                    cv2.arrowedLine(overlay, (cx, cy), (int(cx + dx_px * 2), int(cy + dy_px * 2)), self.COLOR_METRO_ARROW, 2, tipLength=0.3)

                cv2.rectangle(overlay, (x - 5, y - 24), (x + len(metro_label)*7 + 10, y - 2), (140, 0, 140), -1)
                cv2.putText(overlay, f"{metro_label} TILT", (x, y - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)

            else:
                # 🟢 Checkmark
                cv2.circle(overlay, (cx, cy), 11, self.COLOR_PASS, -1)
                cv2.line(overlay, (cx - 5, cy), (cx - 1, cy + 5), (255, 255, 255), 2)
                cv2.line(overlay, (cx - 1, cy + 5), (cx + 6, cy - 4), (255, 255, 255), 2)
                cv2.rectangle(overlay, (x, y), (x + cw, y + ch), (60, 160, 60), 1)

                cv2.rectangle(overlay, (x, y + ch + 2), (x + len(cid)*9 + 8, y + ch + 18), (20, 20, 20), -1)
                cv2.putText(overlay, cid, (x + 2, y + ch + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)

        # 4. Legend (Bottom-Right)
        leg_w, leg_h = 245, 160
        leg_x = max(10, w - leg_w - 10)
        leg_y = max(10, h - leg_h - 10)
        cv2.rectangle(overlay, (leg_x, leg_y), (leg_x + leg_w, leg_y + leg_h), (30, 30, 30), -1)
        cv2.rectangle(overlay, (leg_x, leg_y), (leg_x + leg_w, leg_y + leg_h), (200, 200, 200), 1)
        cv2.putText(overlay, "IPC-A-610 METROLOGY", (leg_x + 10, leg_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        legends = [
            ("[Red Circle] Missing Component", self.COLOR_MISSING),
            ("[Cyan Triangle] Height Anomaly", self.COLOR_HEIGHT),
            ("[Yellow Diamond] Tombstone Defect", self.COLOR_TOMBSTONE),
            ("[Purple Square] Tilt / Skew Anomaly", self.COLOR_TILT),
            ("[Green Check] IPC-A-610 Pass", self.COLOR_PASS)
        ]
        for idx, (lbl, col) in enumerate(legends):
            ly = leg_y + 42 + idx * 22
            cv2.putText(overlay, lbl, (leg_x + 10, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.40, col, 1)

        # 5. Processing Time Tag (Bottom-Left)
        cv2.rectangle(overlay, (10, h - 35), (230, h - 10), (20, 20, 20), -1)
        cv2.putText(overlay, f"Inspection Latency: {processing_ms:.1f} ms", (18, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        return overlay

    def draw_depth_heatmap(self, img: np.ndarray, depth_map: np.ndarray) -> np.ndarray:
        """
        Renders a colorized 3D Depth Heatmap overlay (INFERNO colormap) blended with the base image.
        """
        if depth_map is None or depth_map.size == 0:
            return img.copy()

        h, w = img.shape[:2]
        resized_depth = cv2.resize(depth_map, (w, h))

        norm_depth = cv2.normalize(resized_depth, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        color_heatmap = cv2.applyColorMap(norm_depth, cv2.COLORMAP_INFERNO)

        blended = cv2.addWeighted(img, 0.4, color_heatmap, 0.6, 0)

        # Add 3D Depth Title Banner
        cv2.rectangle(blended, (0, 0), (w, 40), (15, 15, 15), -1)
        cv2.putText(blended, "3D SUBSTRATE-LEVELED DEPTH MAP (INFERNO)", (20, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        return blended

    def to_base64(self, img: np.ndarray) -> str:
        """Encodes BGR image to base64 PNG string."""
        _, buf = cv2.imencode(".png", img)
        return base64.b64encode(buf).decode("utf-8")
