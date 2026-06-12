# Timecard Generator

Upload two monthly shift images and get an editable timecard broken down by shift type and day.

---

## What it does

- Accepts two schedule images (PNG or JPG)
- Parses and merges them into a single timecard
- Displays hours split into **Shift Allowance**, **Overtime 1.5**, and **Overtime 2.0**
- Lets you copy by click, edit, add rows, and undo/redo changes

---

## Stack

- **Frontend** — React
- **Backend** — FastAPI (Python)

---

## Running locally

### Backend

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd ui
npm install
npm run dev
```

---

## API

### `POST /parse`

Upload exactly two schedule images.

**Request** — `multipart/form-data`

| Field   | Type   | Description          |
|---------|--------|----------------------|
| `files` | images | Two schedule images  |

**Response**

```json
{
  "success": true,
  "results": [
    { "filename": "img1.png", "success": true, "data": {}, "range": { "start": "Feb 1, 2026", "end": "Feb 15, 2026" } },
    { "filename": "img2.png", "success": true, "data": {}, "range": { "start": "Feb 16, 2026", "end": "Feb 28, 2026" } }
  ],
  "data": {
    "Feb 1, 2026": {
      "is_off": false,
      "is_weekend": false,
      "normal": [{ "start": "08:00", "stop": "17:00", "comment": "" }],
      "overtime": []
    }
  }
}
```

**Errors**

| Status | Reason |
|--------|--------|
| `400`  | Not exactly two files uploaded |
| `400`  | Both images failed to parse |
| `400`  | Images are from different months |
| `500`  | Unexpected server error |

---

## Notes

- Both images must be from the **same month**
- If one image fails, you can still proceed with the successfully parsed one
- Overtime entries with `is_weekend: true` count as **Overtime 2.0**; others as **Overtime 1.5**