from datetime import datetime

def get_month(schedule):
	first_date = next(iter(schedule.keys()))
	return datetime.strptime(
		first_date.replace("'", "").replace("‘", "").replace("’", "").strip(),
		"%b %d, %Y"
	).strftime("%Y-%m")


def merge_schedules(schedule1, schedule2):
	merged = dict(schedule1)

	for date, day in schedule2.items():

		if date not in merged:
			merged[date] = day
			continue

		existing = merged[date]

		# Prefer non-off days
		if existing.get("is_off", False) and not day.get("is_off", False):
			merged[date] = day
			continue

		# Prefer entries containing overtime
		if (
			len(day.get("overtime", []))
			> len(existing.get("overtime", []))
		):
			merged[date] = day
			continue

		# Prefer entries with more normal shifts
		if (
			len(day.get("normal", []))
			> len(existing.get("normal", []))
		):
			merged[date] = day

	return merged


def sort_schedule(schedule):
	return dict(
		sorted(
			schedule.items(),
			key=lambda x: datetime.strptime(
				x[0].replace("'", "").replace("‘", "").replace("’", "").strip(),
				"%b %d, %Y"
			)
		)
	)

def get_date_range(schedule):
	dates = list(schedule.keys())

	start = min(dates, key=lambda d: datetime.strptime(
		d.replace("'", "").replace("‘", "").replace("’", "").strip(),
		"%b %d, %Y"
	))

	end = max(dates, key=lambda d: datetime.strptime(
		d.replace("'", "").replace("‘", "").replace("’", "").strip(),
		"%b %d, %Y"
	))

	return start, end