# Vehicle Surveillance & ALPR Security Gateway — Full Project Context

> **For any new AI assistant:** This document is the complete technical reference for the `Vehicle_Surveillance` project. Read this first before writing any code.

---

## 1. Project Overview

**Name:** Vehicle Surveillance & ALPR (Automatic License Plate Recognition) Security Gateway  
**Purpose:** A campus security and parking management system using computer vision to automatically detect, read, and track Indian license plates from camera or video feeds.  
**Tech Stack:** Python, FastAPI, YOLOv8, PaddleOCR, OpenCV, SQLite  
**Primary Use Case:** Easwari Engineering College campus — tracking vehicle entries/exits, detecting threats (hotlisted/banned vehicles), and flagging low-confidence reads for human operator review.

---

## 2. Root Project Path

```
d:\downloads\Vehicle_Surveillance\Vehicle_Surveillance\
```

*(Note: There is a double-nested folder. The actual working directory is the inner `Vehicle_Surveillance`.)*

---

## 3. Complete File & Folder Structure

```
Vehicle_Surveillance/                        ← WORKING ROOT
│
├── main.py                                  ← ⭐ MAIN FastAPI server + full HTML/JS dashboard (647 lines)
├── requirements.txt                         ← Python dependencies (pinned versions)
├── data.yaml                                ← YOLOv8 dataset config (for training)
├── .env                                     ← Live secrets (git-ignored)
├── .env.example                             ← Template for .env
├── .gitignore                               ← Excludes .db, .pt, datasets, kaggle.json, venv
├── README.md                                ← Project overview + architecture diagram
├── kaggle.json                              ← Kaggle API key (git-ignored)
│
├── campus_alpr.db                           ← SQLite database (git-ignored, runtime artifact)
│
├── plate_detector.pt                        ← Custom-trained YOLOv8 model for Indian plates (6.2 MB)
├── yolov8n.pt                               ← Base YOLOv8 nano weights (6.5 MB, for training)
├── yolo26n.pt                               ← Alternative YOLO weights (5.5 MB)
│
├── api/
│   └── __init__.py                          ← Empty (reserved for future API router separation)
│
├── core/
│   └── __init__.py                          ← Empty (reserved for future core logic)
│
├── db/
│   ├── __init__.py
│   ├── db_manager.py                        ← SQLite CRUD: init_db(), log_event(), enforce_privacy_policy()
│   ├── clear_db.py                          ← Utility: wipe all vehicle_events records + reset ID counter
│   └── view_db.py                           ← Utility: print all DB records to terminal
│
├── services/
│   ├── __init__.py
│   └── vision/
│       ├── __init__.py
│       ├── ocr_engine.py                    ← ⭐ PaddleOCR engine: extract_explainable_ocr(), fix_common_ocr_errors()
│       ├── alpr_pipeline.py                 ← Single-image ALPR pipeline (YOLO → crop → OCR → log)
│       ├── alpr_live_web.py                 ← Live video pipeline (logs to SQLite directly via db_manager)
│       └── alpr_video_secure.py             ← ⭐ Live video pipeline (posts to FastAPI REST endpoint via HTTP)
│
├── tests/
│   └── test_ocr.py                          ← OCR explainability report generator (process_plate_for_review())
│
├── scripts/
│   ├── dataset_kaggle.py                    ← Downloads Indian plate dataset from Kaggle
│   ├── format_dataset.py                    ← Converts dataset annotations to YOLO format
│   ├── train_plate_detection.py             ← YOLOv8 fine-tuning script (50 epochs, GPU)
│   └── download_models.sh                   ← Shell script to pull YOLO weights
│
├── datasets/
│   └── indian_plates/                       ← Training data (git-ignored)
│       ├── train/images/
│       └── val/images/
│
├── indian_vehicle_dataset/                  ← Raw Kaggle download (git-ignored, ~178 MB zip)
│   ├── State-wise_OLX/
│   ├── google_images/
│   └── video_images/
│
├── models/                                  ← (Empty, reserved for model versioning)
├── runs/                                    ← YOLOv8 training output (git-ignored)
└── __pycache__/                             ← Python bytecode cache
```

---

## 4. Architecture & Data Flow

```
Camera / Video File
        │
        ▼
[YOLOv8 plate_detector.pt]           ← Detects license plate bounding box
        │ Cropped plate ROI
        ▼
[Image Enhancement]                  ← Resize 2.5x, grayscale, contrast/threshold
        │ Enhanced image
        ▼
[PaddleOCR Engine]                   ← Reads text, returns character-level confidence
        │
        ├── High Confidence (≥65%) + Valid Format ──► AUTO_PASS
        └── Low Confidence / Bad Format ──────────► NEEDS HUMAN REVIEW
        │
        ▼
[Indian Plate Format Fixer]           ← Context-aware O↔D, I↔1 substitutions
        │ Cleaned plate_text + character_map
        ▼
[FastAPI Backend (main.py)]
        │
        ├── Fuzzy match against open visits (≥75% SequenceMatcher ratio)
        │   ├── Match found → UPDATE: set out_time, duration = "EXITED"
        │   └── No match   → INSERT: new entry event
        │
        ├── Hotlist check → is plate in banned list? → THREAT DETECTED
        │
        └── SQLite (campus_alpr.db)
                │
                ▼
        [Web Dashboard UI]            ← Served as inline HTML/JS from main.py GET /
                │
                ├── Operator login (session token, 24h expiry)
                ├── Live polling every 3 seconds (GET /api/v1/dashboard/metrics)
                ├── Threat badges with pulsing red animation
                ├── Click status badge → open OCR Resolution Console modal
                │   ├── Shows plate image (Base64)
                │   ├── Shows per-character confidence bars
                │   └── Operator can correct + commit → PUT /api/v1/events/{id}/review
                └── Admin: Manage Hotlist (add/remove banned plates)
```

---

## 5. SQLite Database Schema (`campus_alpr.db`)

### Table: `vehicle_events`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `plate_text` | TEXT | Corrected/final plate number |
| `original_ocr_text` | TEXT | Raw OCR output before operator fix |
| `confidence` | REAL | Average OCR confidence (0.0–1.0) |
| `system_status` | TEXT | `AUTO_PASS`, `NEEDS HUMAN REVIEW`, `RESOLVED`, `EXITED`, `THREAT DETECTED` |
| `in_time` | DATETIME | Entry timestamp |
| `out_time` | DATETIME | Exit timestamp (NULL if still inside) |
| `duration` | TEXT | Human-readable e.g. `"0h 15m"` |
| `is_hotlisted` | BOOLEAN | 1 if vehicle is on banned list |
| `notes` | TEXT | Operator remarks or system notes |
| `plate_image_base64` | TEXT | Base64-encoded JPEG of the cropped plate |
| `character_map_json` | TEXT | JSON: `[{char, confidence}, ...]` per character |

### Table: `hotlist`
| Column | Type | Description |
|---|---|---|
| `plate_text` | TEXT PK | Banned plate number (uppercase, stripped) |
| `added_on` | DATETIME | When it was banned |

### Table: `users`
| Column | Type | Description |
|---|---|---|
| `username` | TEXT PK | Login username |
| `password_hash` | TEXT | SHA-256 hash of password |
| `role` | TEXT | `admin` or `operator` |

### Table: `sessions`
| Column | Type | Description |
|---|---|---|
| `token` | TEXT PK | 64-char hex session token |
| `username` | TEXT | Associated user |
| `expires_on` | DATETIME | Expiry (24h from login) |

---

## 6. REST API Endpoints (all in `main.py`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | None | Serves the full HTML/JS dashboard UI |
| `POST` | `/api/v1/auth/login` | None | Returns session_token, username, role |
| `GET` | `/api/v1/hotlist` | Bearer token (any user) | List all banned plates |
| `POST` | `/api/v1/hotlist` | Bearer token (admin only) | Add plate to hotlist |
| `DELETE` | `/api/v1/hotlist/{plate}` | Bearer token (admin only) | Remove plate from hotlist |
| `POST` | `/api/v1/events` | `access_token` header (machine key) | Log a new vehicle detection from the vision pipeline |
| `PUT` | `/api/v1/events/{event_id}/review` | Bearer token (any user) | Operator corrects a plate reading |
| `GET` | `/api/v1/dashboard/metrics` | Bearer token (any user) | Returns last 50 events for the dashboard table |

### Two Auth Systems
1. **Machine API Key** (header: `access_token`): Used by the vision pipeline scripts (`alpr_video_secure.py`) to POST events. Value from `.env: API_KEY` (default: `easwari_secure_secret_token_2026`).
2. **Session Token** (header: `Authorization: Bearer <token>`): Used by the human operator dashboard UI. Created at login, expires in 24h.

### RBAC Roles
- `admin`: Can add/remove hotlist entries, manage everything.
- `operator`: Can view dashboard, correct plate readings. Cannot touch hotlist.

---

## 7. Key Modules Deep Dive

### `main.py` (647 lines) — The Entire Backend
- **FastAPI app** named `"Security Gateway"`.
- **Lifespan** (`@asynccontextmanager`): On startup, creates all 4 DB tables, inserts default `admin`/`guard1` users, starts background TTL task.
- **`enforce_ttl_policy()`**: Async background loop that runs daily. Deletes non-hotlisted events older than 30 days, hotlisted events older than 3 years.
- **`log_vehicle_event()` — the core event logic:**
  - Accepts OCR payload from the vision pipeline.
  - Checks hotlist → flags THREAT if match.
  - Fuzzy-matches (≥75% similarity) against the last 20 open visits.
    - Match found with >15 second gap → marks exit, calculates duration.
    - No match → inserts new entry.
  - Anti-bounce guard: ignores re-submissions within 15 seconds.
- **Embedded HTML/JS Dashboard** (returned inline from `GET /`): Login view → Dashboard view with table + polling. Modal for OCR character breakdown. Modal for hotlist management.

### `services/vision/ocr_engine.py` (153 lines)
- **`fix_common_ocr_errors(plate_text)`**: Position-aware Indian plate format fixer.
  - Positions 0–1: Must be letters (state code). Converts digits → letters.
  - Positions 2–3: Must be digits (RTO code). Converts letters → digits. Skips if BH series.
  - Positions 4–(N-4): Must be letters (series). Converts `0→D`, `O→D`.
  - Last 4 positions: Must be digits. Converts letters → digits.
  - Edge case: strips leading garbage character if `plate[1:3]` is a valid state.
- **`extract_explainable_ocr(ocr_image, display_image=None)`**:
  - Runs PaddleOCR, sorts bounding boxes top-to-bottom.
  - Builds `character_map`: list of `{char, confidence, bbox}` per character.
  - Applies `fix_common_ocr_errors()`.
  - Validates against Indian plate regex (standard `AA00AA0000` or BH series).
  - **Two-tier soft-fail:** `AUTO_PASS` if strict format + conf ≥ 0.65, else `NEEDS HUMAN REVIEW`.
  - Returns Base64 JPEG of the *color* plate image for the UI, while feeding B&W to PaddleOCR.

### `services/vision/alpr_video_secure.py` (141 lines) — Primary Live Pipeline
- The **production-grade** video pipeline.
- Processes every 3rd frame (`process_every_n_frames = 3`).
- Image preprocessing: YOLO bbox → 2% padding → 2.5x resize → bilateral filter → adaptive threshold (B&W for OCR) + color copy (for UI).
- **Plate cache (12 second timeout):** Uses fuzzy matching (≥40% similarity) to suppress duplicate reads from the same vehicle still in frame.
- POSTs to `http://127.0.0.1:8000/api/v1/events` via a daemon thread (non-blocking).
- Shows annotated live feed window with `cv2.imshow`.

### `services/vision/alpr_live_web.py` (102 lines) — Earlier/Simpler Pipeline
- Processes every 10th frame.
- Uses `process_plate_for_review()` from `tests/test_ocr.py` (different OCR path vs `alpr_video_secure.py`).
- Exact-match cache (15 second timeout) — no fuzzy matching.
- Logs **directly to SQLite** via `db/db_manager.py:log_event()`, **bypassing** the FastAPI server.

### `services/vision/alpr_pipeline.py` (88 lines) — Single Image Mode
- Entry point for processing a single static image file.
- YOLO detection → crop → 2.5x enlarge → grayscale → contrast enhance → `process_plate_for_review()` → `log_event()`.
- Cleans up temp JPEG files after processing.

### `tests/test_ocr.py` (93 lines)
- Contains `process_plate_for_review(image_path)`: an older OCR pipeline that reads from file path.
- Returns an "explainability report" dict with `primary_plate`, `plate_segments`, `system_status`.
- Used by `alpr_pipeline.py` and `alpr_live_web.py`.
- Has hardcoded `IGNORE_TEXT = ["IND", "HONDA", "DRHARY46"]` to filter watermarks.
- Confidence threshold: `0.90` (stricter than `ocr_engine.py`'s 0.65).

### `db/db_manager.py` (72 lines)
- `init_db()`: Creates the `vehicle_events` table (simpler schema than `main.py`'s inline schema — this is the older version).
- `log_event(plate_text, confidence, system_status, is_hotlisted, human_override)`: Inserts events with 30-day or 1095-day retention.
- `enforce_privacy_policy()`: Manual TTL delete (the `main.py` version runs this automatically as a background task).

> ⚠️ **Schema Mismatch:** `db_manager.py` creates a simpler `vehicle_events` table (no `out_time`, `duration`, `plate_image_base64`, etc.). The `main.py` lifespan creates the full schema with `ALTER TABLE` auto-migrations. The `alpr_live_web.py` uses `db_manager.log_event()` so its records lack the stateful tracking fields.

---

## 8. Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | `easwari_secure_secret_token_2026` | Machine token for vision pipeline → FastAPI |
| `DEFAULT_ADMIN_PASSWORD` | `secure2026` | Admin user password (set once on DB init) |
| `DEFAULT_GUARD_PASSWORD` | `password123` | Guard/operator password (set once on DB init) |

---

## 9. Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.103.1 | Web framework + REST API |
| `uvicorn` | 0.23.2 | ASGI server to run FastAPI |
| `ultralytics` | 8.0.196 | YOLOv8 for plate detection |
| `paddleocr` | 2.7.0.3 | OCR engine for reading plate text |
| `opencv-python` | 4.8.0.76 | Image processing and video capture |
| `pydantic` | 2.3.0 | Data validation (FastAPI models) |
| `requests` | 2.31.0 | HTTP client (vision pipeline → FastAPI) |
| `kaggle` | 1.5.16 | Dataset download from Kaggle |
| `python-dotenv` | 1.0.0 | Load `.env` secrets |

---

## 10. How to Run the System

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set up `.env`
```bash
cp .env.example .env
# Edit .env with your API_KEY and passwords
```

### Step 3: Start the FastAPI backend
```bash
# From inside the Vehicle_Surveillance/ directory
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- Dashboard URL: `http://localhost:8000/`
- Admin login: `admin` / `secure2026`
- Guard login: `guard1` / `password123`

### Step 4: Run the Vision Pipeline (in a second terminal)
```bash
# For live webcam (production mode — posts to FastAPI):
python -m services.vision.alpr_video_secure

# For a video file:
# Edit alpr_video_secure.py main block: process_secure_video_stream("path/to/video.mp4")
python -m services.vision.alpr_video_secure

# For a single image test:
# Edit alpr_pipeline.py: run_alpr_pipeline("my_plate.jpg")
python -m services.vision.alpr_pipeline
```

---

## 11. ML Model Training (Optional)

```bash
# 1. Download dataset from Kaggle
python scripts/dataset_kaggle.py

# 2. Format dataset to YOLO annotation format
python scripts/format_dataset.py

# 3. Train the model (requires GPU, NVIDIA)
python scripts/train_plate_detection.py
# Output saved to runs/detect/custom_plate_model/weights/best.pt
# Rename to plate_detector.pt and place in root
```

**`data.yaml` config:**
- Dataset path: `D:/Vehicle_Surveillance/datasets/indian_plates`
- Single class: `license_plate` (class index 0)
- Training: 50 epochs, 640px image size, batch 16

---

## 12. Key Design Decisions & Important Gotchas

### ✅ Two OCR Paths
- `ocr_engine.py:extract_explainable_ocr()` → used by `alpr_video_secure.py`. Returns full JSON payload ready for the API. Uses adaptive threshold preprocessing.
- `tests/test_ocr.py:process_plate_for_review()` → used by `alpr_pipeline.py` and `alpr_live_web.py`. Older path, reads from file. Confidence threshold is stricter (0.90 vs 0.65).

### ✅ Two DB Write Paths
- `alpr_video_secure.py` → HTTP POST to FastAPI → `main.py` writes to DB (full schema, stateful tracking).
- `alpr_live_web.py` + `alpr_pipeline.py` → direct SQLite via `db_manager.log_event()` (simpler schema, no stateful in/out tracking).

### ✅ Fuzzy Matching for Entry/Exit
- Backend (`main.py`) uses `difflib.SequenceMatcher` with a **0.75 ratio** threshold to match an exiting vehicle to its entry record, even if OCR reads slightly differently.
- Vision pipeline (`alpr_video_secure.py`) uses the same at a **0.40 ratio** to suppress duplicates from the same vehicle still in frame.

### ✅ Anti-Bounce Guard
- The FastAPI `/api/v1/events` endpoint will return `{"status": "ignored_anti_bounce"}` if the same vehicle triggers again within **15 seconds**. This is intentionally low for testing.

### ✅ Indian Plate Format Rules (Standard)
```
[State Code (2 letters)] [RTO Code (2 digits)] [Series (1-3 letters)] [Number (1-4 digits)]
Example: TN09DH1234
BH Series: 23BH1234AA
```

### ⚠️ Schema Drift
- `db/db_manager.py`'s `init_db()` creates a minimal schema. The production schema lives in `main.py`'s lifespan function. If you run `db_manager.init_db()` first, then start the server, the `ALTER TABLE` migrations in `main.py` will add the missing columns automatically.

### ⚠️ `api/` and `core/` Directories
- Both contain only `__init__.py`. They are **empty placeholder packages**, reserved for future refactoring (separating routes and core logic from `main.py`).

### ⚠️ `models/` Directory
- Completely empty. The actual model weights live in the project root (`plate_detector.pt`, `yolov8n.pt`, `yolo26n.pt`).

### ⚠️ Hardcoded API URL in Vision Pipeline
- `alpr_video_secure.py` has `API_URL = "http://127.0.0.1:8000/api/v1/events"` hardcoded. To run against a remote server, change this manually.

---

## 13. Dashboard UI Features (Inline in `main.py`)

The entire frontend is a single HTML page returned by `GET /`. No separate frontend framework.

| Feature | Details |
|---|---|
| **Login screen** | Username/password form, localStorage session management |
| **Role-based UI** | Hotlist button only visible to `admin` role |
| **Vehicle Log Table** | Plate, Entry Time, Exit Time, Duration, Status, Notes |
| **Status badges** | Color-coded: green (AUTO_PASS), red dashed (NEEDS REVIEW), gray (EXITED), green italic (RESOLVED), pulsing red (THREAT DETECTED) |
| **Auto-refresh** | `setInterval(fetchTelemetry, 3000)` — polls every 3 seconds |
| **OCR Resolution Console** | Click any status badge → modal with: plate image, per-character confidence bars (green/yellow/red), editable plate field, notes, submit correction |
| **Hotlist Manager** | Admin-only modal: add/remove banned plates in real-time |
| **Session Management** | 24h tokens, stored in `localStorage`, auto-logout on 401 |

---

## 14. Files Excluded from Git (`.gitignore`)

- `.env` (secrets)
- `*.db` / `campus_alpr.db` (runtime data)
- `kaggle.json` (API key)
- `datasets/` (large training data)
- `indian_vehicle_dataset/` (raw downloads)
- `*.pt` / `*.onnx` (large model weights)
- `runs/` (training outputs)
- `temp_plate_*.jpg` (pipeline temp files)
- `__pycache__/`, `.vscode/`
