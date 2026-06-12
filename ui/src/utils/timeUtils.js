export function toMinutes(time) {
	if (!time) return 0;

	const [h, m] = time.split(":").map(Number);
	return h * 60 + m;
}

export function getDurationHours(entry) {
	if (!entry?.start || !entry?.stop) return 0;

	let start = toMinutes(entry.start);
	let stop = toMinutes(entry.stop);

	if (stop < start) stop += 24 * 60;

	return (stop - start) / 60;
}