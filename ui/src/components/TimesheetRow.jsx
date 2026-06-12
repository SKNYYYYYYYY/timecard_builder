import { useState } from "react";
import TimeField from "./TimeField";
import { getDurationHours } from "../utils/timeUtils";

export default function TimesheetRow({
	title,
	data,
	getEntry,
	rowClass,
	onEntryChange,
	getOverride,
}) {
	const [editingKey, setEditingKey] = useState(null);
	const [draft, setDraft] = useState({});

	const getEffectiveEntry = (day) => getOverride?.(day, title) ?? getEntry(day);

	const rowTotal = data.reduce((total, day) => {
		return total + getDurationHours(getEffectiveEntry(day));
	}, 0);

	const startEdit = (day) => {
		const entry = getEffectiveEntry(day);
		setDraft({
			start: entry?.start ?? "",
			stop: entry?.stop ?? "",
			comment: entry?.comment ?? "",
		});
		setEditingKey(`${day.date}-${title}`);
	};

	const commitEdit = (day) => {
		onEntryChange?.(day, title, { ...draft });
		setEditingKey(null);
	};

	const cancelEdit = () => setEditingKey(null);

	return (
		<tr className={rowClass}>
			<td className="type-cell">{title}</td>

			{data.map((day) => {
				const key = `${day.date}-${title}`;
				const entry = getEffectiveEntry(day);
				const hours = getDurationHours(entry);
				const isEditing = editingKey === key;

				return (
					<td key={key} className="entry-cell">
						<div className={`entry-block${isEditing ? " entry-block--editing" : ""}`}>
							{isEditing ? (
								<>
									<div className="edit-field">
										<label className="label">Start</label>
										<input
											type="time"
											value={draft.start}
											onChange={(e) => setDraft((d) => ({ ...d, start: e.target.value }))}
											className="edit-input"
										/>
									</div>
									<div className="edit-field">
										<label className="label">Stop</label>
										<input
											type="time"
											value={draft.stop}
											onChange={(e) => setDraft((d) => ({ ...d, stop: e.target.value }))}
											className="edit-input"
										/>
									</div>
									<div className="edit-field">
										<label className="label">Comments</label>
										<input
											type="text"
											value={draft.comment}
											onChange={(e) => setDraft((d) => ({ ...d, comment: e.target.value }))}
											className="edit-input edit-input--comment"
											placeholder="Add comment…"
										/>
									</div>
									<div className="edit-actions">
										<button className="btn-commit" onClick={() => commitEdit(day)}>
											✓ Commit
										</button>
										<button className="btn-cancel" onClick={cancelEdit}>
											✕
										</button>
									</div>
								</>
							) : (
								<>
									<TimeField label="Start" value={entry?.start ?? ""} />
									<TimeField label="Stop" value={entry?.stop ?? ""} />
									<TimeField label="Comments" value={entry?.comment ?? ""} />
									<div className="entry-footer">
										<div className="hours-small">{hours ? `${hours}hrs` : ""}</div>
										<button className="btn-edit" onClick={() => startEdit(day)} title="Edit this entry">
											✎ Edit
										</button>
									</div>
								</>
							)}
						</div>
					</td>
				);
			})}

			<td className="row-total">{rowTotal}hrs</td>
		</tr>
	);
}