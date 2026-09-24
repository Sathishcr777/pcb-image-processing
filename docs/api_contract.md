# REST API Contract Specifications

**Server Host (Laptop B Static IP):** `http://192.168.1.100:8000`  
**Protocol:** HTTP/1.1 REST JSON  
**Maintained By:** Teams 5 & 6  

---

## Endpoints

### 1. `GET /health`
Returns system status and model readiness.
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "system_version": "v1.0-frozen",
  "reference_loaded": true,
  "depth_model_loaded": true,
  "timestamp_utc": "2026-07-30T09:12:00Z"
}
```

---

### 2. `POST /set-reference`
Sets the golden reference image and generates the baseline depth map (`golden_depth.npy`).
- **Request:** `multipart/form-data` with `file: image/png`
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Golden reference set and depth map generated.",
  "alignment_features_extracted": 5000,
  "golden_shape": [720, 1280, 3]
}
```

---

### 3. `POST /inspect`
Inspects an incoming PCB image against the golden reference.
- **Request:** `multipart/form-data` with `file: image/png`
- **Response (200 OK):**
```json
{
  "record_id": "REC-20260730-001",
  "alignment_quality": 0.942,
  "health_index": 0.985,
  "verdict": "PASS",
  "total_components": 10,
  "defective_components": 0,
  "processing_time_ms": 342,
  "components": [
    {
      "id": "U1",
      "name": "Main Microcontroller",
      "is_missing": false,
      "ssim_score": 0.98,
      "height_penalty": 0.0,
      "tilt_flag": false,
      "tombstone_flag": false,
      "status": "PASS"
    }
  ],
  "overlay_image_b64": "<base64_png_string>"
}
```

---

### 4. `GET /metrics`
Returns aggregated session inspection statistics.
- **Response (200 OK):**
```json
{
  "boards_inspected": 31,
  "pass_count": 5,
  "rework_count": 6,
  "fail_count": 20,
  "session_fpy": 0.161,
  "dpmo": 83870.97,
  "avg_processing_ms": 385.4
}
```

---

## Edge Case HTTP Status Codes
- `HTTP 400 Bad Request`: Invalid image payload format (`invalid_image_type`).
- `HTTP 413 Payload Too Large`: Upload file exceeds 10 MB limit (`file_too_large`).
- `HTTP 422 Unprocessable Entity`: Alignment quality $< 0.40$ (`alignment_failed`).
- `HTTP 503 Service Unavailable`: Reference board not set prior to inspection (`reference_not_set`).
