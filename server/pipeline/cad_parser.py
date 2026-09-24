"""
SMT Pick-and-Place Centroid / CAD Parser
Advanced Industry Feature: Automated ROI Generation
Converts standard SMT .csv / .xy / .pos centroid files to pixel-based inspection ROIs.
"""

import csv
import json
import os
import numpy as np
from typing import List, Dict, Tuple, Optional

class CADParser:
    def __init__(self, pcb_width_mm: float = 100.0, pcb_height_mm: float = 80.0):
        self.pcb_width_mm = pcb_width_mm
        self.pcb_height_mm = pcb_height_mm
        
        # Standard SMT Package Footprint Dimensions in mm [width_mm, height_mm, default_weight]
        self.PACKAGE_SPECS = {
            "0201": {"w_mm": 0.6, "h_mm": 0.3, "weight": 1.0, "type": "Resistor", "depth": True, "tilt": True, "tomb": True},
            "0402": {"w_mm": 1.0, "h_mm": 0.5, "weight": 1.5, "type": "Capacitor", "depth": True, "tilt": True, "tomb": True},
            "0603": {"w_mm": 1.6, "h_mm": 0.8, "weight": 1.5, "type": "Capacitor", "depth": True, "tilt": True, "tomb": True},
            "0805": {"w_mm": 2.0, "h_mm": 1.25, "weight": 2.0, "type": "Capacitor", "depth": True, "tilt": True, "tomb": True},
            "1206": {"w_mm": 3.2, "h_mm": 1.6, "weight": 2.0, "type": "Resistor", "depth": True, "tilt": True, "tomb": True},
            "SOT-23": {"w_mm": 2.9, "h_mm": 1.3, "weight": 3.0, "type": "Transistor", "depth": True, "tilt": True, "tomb": False},
            "SOIC-8": {"w_mm": 4.9, "h_mm": 3.9, "weight": 3.5, "type": "IC", "depth": True, "tilt": True, "tomb": False},
            "QFP-64": {"w_mm": 10.0, "h_mm": 10.0, "weight": 5.0, "type": "IC", "depth": True, "tilt": True, "tomb": False},
            "QFP-100": {"w_mm": 14.0, "h_mm": 14.0, "weight": 5.0, "type": "IC", "depth": True, "tilt": True, "tomb": False},
            "USB-C": {"w_mm": 8.9, "h_mm": 7.3, "weight": 3.0, "type": "Connector", "depth": True, "tilt": False, "tomb": False},
            "HEADER": {"w_mm": 2.54, "h_mm": 25.4, "weight": 3.5, "type": "Header", "depth": True, "tilt": True, "tomb": False},
            "ELECTRO_CAP": {"w_mm": 6.3, "h_mm": 6.3, "weight": 2.5, "type": "Capacitor", "depth": True, "tilt": True, "tomb": True}
        }

    def parse_centroid_csv(self, file_content: str, image_shape: Tuple[int, int], origin_mode: str = "bottom_left") -> List[Dict]:
        """
        Parses a Pick-and-Place CSV string into normalized component dictionaries.
        Supports standard Altium, KiCad, Eagle, and generic SMT CSV formats:
        Designator, Package, Mid X, Mid Y, Rotation, Layer
        """
        img_h, img_w = image_shape[:2]
        lines = [line.strip() for line in file_content.strip().split("\n") if line.strip() and not line.startswith("#")]
        
        if not lines:
            return []

        reader = csv.reader(lines)
        header = [col.strip().lower() for col in next(reader)]

        # Map header columns carefully
        col_map = {}
        for i, col in enumerate(header):
            if any(k == col or k in col for k in ["mid x", "center-x", "posx", "pos_x", "x_mm", "x"]):
                if "id" not in col or col in ["mid x", "center-x"]:
                    col_map["x_mm"] = i
            elif any(k == col or k in col for k in ["mid y", "center-y", "posy", "pos_y", "y_mm", "y"]):
                col_map["y_mm"] = i
            elif any(k == col or k in col for k in ["designator", "refdes", "ref_des", "ref", "component", "id"]):
                if "x" not in col and "y" not in col:
                    col_map["id"] = i
            elif any(k == col or k in col for k in ["package", "footprint", "pkg"]):
                col_map["package"] = i
            elif any(k == col or k in col for k in ["rotation", "rot", "angle"]):
                col_map["rotation"] = i
            elif any(k == col or k in col for k in ["comment", "value", "val"]):
                col_map["value"] = i

        components = []
        scale_x = img_w / max(1.0, self.pcb_width_mm)
        scale_y = img_h / max(1.0, self.pcb_height_mm)

        for row in reader:
            if not row or len(row) < 3:
                continue

            cid = row[col_map.get("id", 0)].strip()
            pkg = row[col_map.get("package", 1)].strip().upper() if "package" in col_map and len(row) > col_map["package"] else "0603"
            
            try:
                x_mm = float(row[col_map.get("x_mm", 2)])
                y_mm = float(row[col_map.get("y_mm", 3)])
            except (ValueError, IndexError):
                continue

            rot_deg = float(row[col_map.get("rotation", 4)]) if "rotation" in col_map and len(row) > col_map["rotation"] else 0.0
            val_str = row[col_map["value"]].strip() if "value" in col_map and len(row) > col_map["value"] else pkg

            # Match or estimate package physical dimension
            spec = self._match_package_spec(pkg, cid)
            
            # Convert physical mm position to pixel coordinates
            pixel_cx = int(x_mm * scale_x)
            if origin_mode == "bottom_left":
                pixel_cy = int(img_h - (y_mm * scale_y))
            else:
                pixel_cy = int(y_mm * scale_y)

            # Convert package size to pixels with a safety pad margin (+25%)
            comp_w_px = max(16, int(spec["w_mm"] * scale_x * 1.25))
            comp_h_px = max(16, int(spec["h_mm"] * scale_y * 1.25))

            # Handle 90/270 degree rotation dimension swap
            if abs(rot_deg - 90.0) < 15 or abs(rot_deg - 270.0) < 15:
                comp_w_px, comp_h_px = comp_h_px, comp_w_px

            # Bounding box Top-Left [x, y, w, h]
            bbox_x = max(0, min(img_w - comp_w_px, pixel_cx - (comp_w_px // 2)))
            bbox_y = max(0, min(img_h - comp_h_px, pixel_cy - (comp_h_px // 2)))

            components.append({
                "id": cid,
                "name": f"{cid} ({val_str})",
                "type": spec["type"],
                "package": pkg,
                "bbox_xywh": [int(bbox_x), int(bbox_y), int(comp_w_px), int(comp_h_px)],
                "nominal_center_mm": [round(x_mm, 2), round(y_mm, 2)],
                "nominal_rotation_deg": round(rot_deg, 1),
                "weight": float(spec["weight"]),
                "depth_check": spec["depth"],
                "tilt_check": spec["tilt"],
                "tombstone_check": spec["tomb"]
            })

        return components

    def _match_package_spec(self, package_name: str, designator: str) -> Dict:
        pkg_upper = package_name.upper()
        for key, spec in self.PACKAGE_SPECS.items():
            if key in pkg_upper:
                return spec
        
        # Heuristic fallback based on designator prefix
        des_prefix = "".join([c for c in designator if c.isalpha()]).upper()
        if des_prefix in ["U", "IC"]:
            return {"w_mm": 6.0, "h_mm": 6.0, "weight": 4.0, "type": "IC", "depth": True, "tilt": True, "tomb": False}
        elif des_prefix in ["C"]:
            return {"w_mm": 1.6, "h_mm": 0.8, "weight": 2.0, "type": "Capacitor", "depth": True, "tilt": True, "tomb": True}
        elif des_prefix in ["R"]:
            return {"w_mm": 1.6, "h_mm": 0.8, "weight": 1.5, "type": "Resistor", "depth": True, "tilt": True, "tomb": True}
        elif des_prefix in ["J", "CONN"]:
            return {"w_mm": 10.0, "h_mm": 5.0, "weight": 3.0, "type": "Connector", "depth": True, "tilt": False, "tomb": False}
        elif des_prefix in ["D", "LED"]:
            return {"w_mm": 2.0, "h_mm": 1.25, "weight": 1.5, "type": "Diode", "depth": True, "tilt": True, "tomb": True}
        
        return {"w_mm": 2.0, "h_mm": 2.0, "weight": 1.5, "type": "Generic", "depth": True, "tilt": True, "tomb": False}
