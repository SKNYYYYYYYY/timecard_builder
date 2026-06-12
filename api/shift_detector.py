import cv2
import numpy as np
import pytesseract
from datetime import datetime
import re


def x_to_time_raw(x, timeline_width, total_hours=24):
    hour_float = (x / timeline_width) * total_hours
    hour = int(hour_float)
    minute = int(round((hour_float - hour) * 60))
    if minute == 60:
        hour += 1
        minute = 0
    return f"{hour % 24:02d}:{minute:02d}"


def snap_hour(time_str):
    h, m = map(int, time_str.split(':'))
    if m >= 30:
        h += 1
    return f"{h % 24:02d}:00"


def snap_floor(time_str):
    h, _ = map(int, time_str.split(':'))
    return f"{h:02d}:00"


def time_to_min(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m


def merge_segments(segs, gap):
    if not segs:
        return []
    groups = []
    cs, ce = segs[0]
    for s, e in segs[1:]:
        if s - ce <= gap:
            ce = max(ce, e)
        else:
            groups.append((cs, ce))
            cs, ce = s, e
    groups.append((cs, ce))
    return groups


def merge_segments_no_red(segs, gap, red_col_set):
    if not segs:
        return []
    groups = []
    cs, ce = segs[0]
    for s, e in segs[1:]:
        gap_has_red = any(x in red_col_set for x in range(ce, s + 1))
        if (s - ce) <= gap and not gap_has_red:
            ce = max(ce, e)
        else:
            groups.append((cs, ce))
            cs, ce = s, e
    groups.append((cs, ce))
    return groups

def add_overtime_comments(schedule):
	for date, day in schedule.items():

		is_weekend = day.get("is_weekend", False)

		for ot in day.get("overtime", []):
			ot["comment"] = (
				"overtime weekend"
				if is_weekend
				else "overtime weekday"
			)

	return schedule


def transform_for_frontend(raw_data):
	result = {}

	for date, day in raw_data.items():

		# Remove OCR quotes and extra spaces
		date = re.sub(r"[‘’']", "", date).strip()

		# Normalize spaces around comma
		date = re.sub(r"\s*,\s*", ", ", date)

		transformed = {
			"is_off": day.get("is_off", False),
			"is_weekend": day.get("is_weekend", False)
		}

		# --------------------------
		# Normal shifts
		# --------------------------
		normal = day.get("normal")

		transformed["normal"] = []

		if (
			isinstance(normal, (list, tuple))
			and len(normal) == 2
			and isinstance(normal[0], str)
		):
			normal = [normal]

		for shift in normal or []:
			if (
				isinstance(shift, (list, tuple))
				and len(shift) == 2
			):
				transformed["normal"].append({
					"start": shift[0],
					"stop": shift[1],
					"comment": ""
				})

		# --------------------------
		# Overtime shifts
		# --------------------------
		overtime = day.get("overtime", [])

		transformed["overtime"] = []

		if (
			isinstance(overtime, (list, tuple))
			and len(overtime) == 2
			and isinstance(overtime[0], str)
		):
			overtime = [overtime]

		for ot in overtime or []:
			if (
				isinstance(ot, (list, tuple))
				and len(ot) == 2
			):
				transformed["overtime"].append({
					"start": ot[0],
					"stop": ot[1],
					"comment": ""
				})

		result[date] = transformed

	return result

def parse_schedule(image_bytes):
    if not image_bytes:
        raise ValueError("Empty image")

    if len(image_bytes) > 10 * 1024 * 1024:
        raise ValueError("Image too large")
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    h_img, w_img = img.shape[:2]

    DATE_COL_WIDTH  = 175
    HEADER_HEIGHT   = 50
    TIME_START_X    = DATE_COL_WIDTH
    TIME_END_X      = w_img
    timeline_width  = TIME_END_X - TIME_START_X
    HOUR_PX         = timeline_width / 24.0

    BLUE_MERGE_GAP  = int(HOUR_PX * 1.1)
    GREEN_MERGE_GAP = int(HOUR_PX * 0.5)
    MIDNIGHT_SNAP_PX = int(HOUR_PX * 0.7)
    try:
      FULL_ROW_PX      = timeline_width * 0.4
      
      def contour_segs(mask_2d, min_w=30):
          cnts, _ = cv2.findContours(mask_2d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
          segs = [(x, x + bw) for c in cnts for x, y, bw, bh in [cv2.boundingRect(c)] if bw >= min_w]
          segs.sort()
          return segs

      # ── Row boundary detection ──────────────────────────────────────────────
      gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
      row_strength = np.mean(gray, axis=1)
      raw_edges = []
      for y in range(HEADER_HEIGHT, h_img - 1):
          if abs(int(row_strength[y]) - int(row_strength[y + 1])) > 8:
              raw_edges.append(y)
      merged_e = []
      for y in raw_edges:
          if not merged_e or y - merged_e[-1] > 15:
              merged_e.append(y)
      rows = [
          (merged_e[i], merged_e[i + 1])
          for i in range(len(merged_e) - 1)
          if merged_e[i + 1] - merged_e[i] > 25
      ]

      # ── Color masks ─────────────────────────────────────────────────────────
      hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

      blue_mask  = cv2.inRange(hsv, np.array([90,  80,  50]), np.array([140, 255, 255]))
      green_mask = cv2.inRange(hsv, np.array([35,  40,  40]), np.array([ 90, 255, 255]))

      red_lo   = cv2.inRange(hsv, np.array([  0, 80, 80]), np.array([ 10, 255, 255]))
      red_hi   = cv2.inRange(hsv, np.array([160, 80, 80]), np.array([180, 255, 255]))
      red_mask = cv2.bitwise_or(red_lo, red_hi)

      # FIX Apr 10: exclude dark, brown, and grey pixels (POF bar variants)
      dark_mask  = cv2.inRange(hsv, np.array([  0,  0,   0]), np.array([180, 255,  80]))
      brown_mask = cv2.inRange(hsv, np.array([  5, 20,  60]), np.array([ 25, 120, 140]))
      grey_mask  = cv2.inRange(hsv, np.array([  0,  0,  60]), np.array([180,  40, 160]))

      blue_mask = cv2.bitwise_and(blue_mask, cv2.bitwise_not(dark_mask))
      blue_mask = cv2.bitwise_and(blue_mask, cv2.bitwise_not(brown_mask))
      blue_mask = cv2.bitwise_and(blue_mask, cv2.bitwise_not(grey_mask))
      blue_mask = cv2.bitwise_and(blue_mask, cv2.bitwise_not(red_mask))

      # ── Time helpers ────────────────────────────────────────────────────────
      def to_start(px):
          return snap_floor(x_to_time_raw(px, timeline_width))

      def to_end(px):
          if (timeline_width - px) <= MIDNIGHT_SNAP_PX:
              return "00:00"
          return snap_hour(x_to_time_raw(px, timeline_width))

      def seg_to_time(s, e):
          return (to_start(s), to_end(e))

      # ── Core derive logic ───────────────────────────────────────────────────
      def derive_normal_and_ot(blue_grps, green_grps):

          def fully_in_green(bs, be):
              return any(gs <= bs and be <= ge for gs, ge in green_grps)

          clean_blue = [(s, e) for s, e in blue_grps
                        if (e - s) > 5 and not fully_in_green(s, e)]

          def clip_right(bs, be):
              clipped = be
              for gs, ge in green_grps:
                  if bs <= gs <= be:
                      clipped = min(clipped, gs)
              return (bs, clipped)

          clipped_blue = [clip_right(s, e) for s, e in clean_blue]
          clipped_blue = [(s, e) for s, e in clipped_blue if e - s > 5]

          def gap_has_green(ce, ns):
              for gs, ge in green_grps:
                  if ce <= gs <= ns or ce <= ge <= ns:
                      return True
              return False

          if len(clipped_blue) > 1:
              remerged = []
              cs, ce = clipped_blue[0]
              for ns, ne in clipped_blue[1:]:
                  if (ns - ce) <= int(HOUR_PX * 1.1) and not gap_has_green(ce, ns):
                      ce = ne
                  else:
                      remerged.append((cs, ce))
                      cs, ce = ns, ne
              remerged.append((cs, ce))
              clipped_blue = remerged

          if not clipped_blue:
              normal_val = None
          elif len(clipped_blue) == 1:
              normal_val = seg_to_time(*clipped_blue[0])
          else:
              normal_val = [seg_to_time(s, e) for s, e in clipped_blue]

          ot_times = [seg_to_time(s, e) for s, e in green_grps]

          if not ot_times:
              ot_val = []
          elif len(ot_times) == 1:
              is_pre = False
              if isinstance(normal_val, tuple):
                  normal_start_min = time_to_min(normal_val[0])
              elif isinstance(normal_val, list) and normal_val:
                  normal_start_min = time_to_min(normal_val[0][0])
              else:
                  normal_start_min = None

              if normal_start_min is not None:
                  is_pre = time_to_min(ot_times[0][0]) < normal_start_min
              ot_val = ot_times[0] if is_pre else ot_times
          else:
              ot_val = ot_times

          return normal_val, ot_val

      # ── Main row loop ────────────────────────────────────────────────────────
      result = {}

      for top, bottom in rows:

          date_text = pytesseract.image_to_string(
              img[top:bottom, 0:DATE_COL_WIDTH], config="--psm 7"
          ).strip()
          if not date_text:
              continue

          # Green analysis for this row
          rg_all = green_mask[top:bottom, TIME_START_X:TIME_END_X]
          gcnts_all, _ = cv2.findContours(rg_all, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
          max_green_w = max((cv2.boundingRect(c)[2] for c in gcnts_all), default=0)
          is_full_row_off = max_green_w > FULL_ROW_PX

          # FIX Apr 6/7: column-coverage test catches thin full-row green bands
          # that are too thin in height to produce a wide contour bounding box.
          # If >50% of timeline columns contain any green pixel → day-off band present.
          green_col_coverage = np.mean(np.any(rg_all > 0, axis=0))
          if green_col_coverage > 0.5:
              is_full_row_off = True

          row_text = pytesseract.image_to_string(
              img[top:bottom, :], config="--psm 6"
          ).strip().lower()
          is_text_off = any(kw in row_text for kw in ("day off", "annual leave", "public holiday"))

          is_off_row = is_full_row_off or is_text_off

          # Blue segments
          rb       = blue_mask[top:bottom, TIME_START_X:TIME_END_X]
          rr       = red_mask[top:bottom, TIME_START_X:TIME_END_X]
          red_cols = set(np.where(np.any(rr > 0, axis=0))[0].tolist())

          raw_blue  = contour_segs(rb, min_w=30)
          blue_grps = merge_segments_no_red(raw_blue, BLUE_MERGE_GAP, red_cols)

          # Green OT segments (exclude full-row bands)
          raw_green = [
              (x, x + bw)
              for c in gcnts_all
              for x, y, bw, bh in [cv2.boundingRect(c)]
              if 30 <= bw <= FULL_ROW_PX
          ]
          raw_green.sort()
          green_grps = merge_segments_no_red(raw_green, GREEN_MERGE_GAP, red_cols)

          # ── Routing ─────────────────────────────────────────────────────────

          if is_off_row and not blue_grps and not green_grps:
              result[date_text] = {"is_off": True}
              continue

          if is_off_row and not blue_grps and green_grps:
              ot = [seg_to_time(s, e) for s, e in green_grps]
              result[date_text] = {"is_off": True, "normal": None, "overtime": ot}
              continue

          if is_off_row and blue_grps:
              normal_val, ot_val = derive_normal_and_ot(blue_grps, green_grps)
              result[date_text] = {"is_off": True, "normal": normal_val, "overtime": ot_val}
              continue

          if not blue_grps and not green_grps:
              result[date_text] = {"is_off": True}
              continue

          # Green only, no blue (May 21 pattern) → normal=None
          if not blue_grps and green_grps:
              ot_times = [seg_to_time(s, e) for s, e in green_grps]
              result[date_text] = {"is_off": False, "normal": None, "overtime": ot_times}
              continue

          normal_val, ot_val = derive_normal_and_ot(blue_grps, green_grps)
          result[date_text] = {"is_off": False, "normal": normal_val, "overtime": ot_val}

          # weekend classification
          for date_text, data in result.items():

              match = re.search(r'([A-Za-z]{3}\s+\d{1,2},\s*\d{4})', date_text)
              clean_date = match.group(1) if match else None

              if not clean_date:
                  data["is_weekend"] = None
                  continue

              date_obj = None
              for fmt in ("%b %d,%Y", "%b %d, %Y"):
                  try:
                      date_obj = datetime.strptime(clean_date, fmt)
                      break
                  except ValueError:
                      pass

              data["is_weekend"] = date_obj.weekday() >= 5 if date_obj else None
      transformed_result = transform_for_frontend(result)
      transformed_result = add_overtime_comments(transformed_result)
      return transformed_result
    except Exception as e:
      raise