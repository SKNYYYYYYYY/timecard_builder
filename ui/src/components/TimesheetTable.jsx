import { useState, useCallback, useRef, useEffect } from "react";
import TimesheetRow from "./TimesheetRow";
import "../styles/timesheet.css";

function toMinutes(time) {
	if (!time) return 0;
	const [h, m] = time.split(":").map(Number);
	return h * 60 + m;
}

function getDurationHours(entry) {
	if (!entry?.start || !entry?.stop) return 0;
	let start = toMinutes(entry.start);
	let stop = toMinutes(entry.stop);
	if (stop < start) stop += 24 * 60;
	return (stop - start) / 60;
}

const INITIAL_STATE = { overrides: {}, extraRows: { normal: 0, ot15: 0, ot20: 0 } };

export default function TimesheetTable({ data, goBack }) {
	// ── History ──────────────────────────────────────────
	const [history, setHistory] = useState([INITIAL_STATE]);
	const [cursor, setCursor] = useState(0);

	const current = history[cursor];
	const { overrides, extraRows } = current;

	const canUndo = cursor > 0;
	const canRedo = cursor < history.length - 1;

	const commit = useCallback((next) => {
		setHistory((prev) => [...prev.slice(0, cursor + 1), next]);
		setCursor((c) => c + 1);
	}, [cursor]);

	const undo = useCallback(() => { if (canUndo) setCursor((c) => c - 1); }, [canUndo]);
	const redo = useCallback(() => { if (canRedo) setCursor((c) => c + 1); }, [canRedo]);

	useEffect(() => {
		const handler = (e) => {
			if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) { e.preventDefault(); undo(); }
			if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) { e.preventDefault(); redo(); }
		};
		window.addEventListener("keydown", handler);
		return () => window.removeEventListener("keydown", handler);
	}, [undo, redo]);

	// ── Entry change ─────────────────────────────────────
	const handleEntryChange = useCallback((day, title, newEntry) => {
		const key = `${day.date}-${title}`;
		commit({
			overrides: { ...overrides, [key]: newEntry },
			extraRows,
		});
	}, [overrides, extraRows, commit]);

	// ── Override lookup (passed to rows) ─────────────────
	const getOverride = useCallback((day, title) => {
		const key = `${day.date}-${title}`;
		return overrides[key] ?? null;
	}, [overrides]);

	// ── Add row picker ────────────────────────────────────
	const [pickerOpen, setPickerOpen] = useState(false);
	const pickerRef = useRef(null);

	useEffect(() => {
		const handler = (e) => {
			if (pickerRef.current && !pickerRef.current.contains(e.target)) setPickerOpen(false);
		};
		document.addEventListener("mousedown", handler);
		return () => document.removeEventListener("mousedown", handler);
	}, []);

	const addRow = (type) => {
		commit({ overrides, extraRows: { ...extraRows, [type]: extraRows[type] + 1 } });
		setPickerOpen(false);
	};

	// ── Row counts ────────────────────────────────────────
	const maxNormal = Math.max(1, ...data.map((d) => d.normal?.length || 0)) + extraRows.normal;
	const maxOT15 = Math.max(1, ...data.map((d) => d.overtime.filter((ot) => !ot.is_weekend).length)) + extraRows.ot15;
	const maxOT20 = Math.max(1, ...data.map((d) => d.overtime.filter((ot) => ot.is_weekend).length)) + extraRows.ot20;

	// ── Column totals ─────────────────────────────────────
	const columnTotals = data.map((day) => {
		let total = 0;
		Array.from({ length: maxNormal }).forEach((_, i) => {
			const orig = day.normal?.[i];
			const entry = overrides[`${day.date}-Shift Allowance`] ?? orig;
			total += getDurationHours(entry);
		});
		Array.from({ length: maxOT15 }).forEach((_, i) => {
			const orig = day.overtime.filter((ot) => !ot.is_weekend)[i];
			const entry = overrides[`${day.date}-Overtime 1.5`] ?? orig;
			total += getDurationHours(entry);
		});
		Array.from({ length: maxOT20 }).forEach((_, i) => {
			const orig = day.overtime.filter((ot) => ot.is_weekend)[i];
			const entry = overrides[`${day.date}-Overtime 2.0`] ?? orig;
			total += getDurationHours(entry);
		});
		return total;
	});

	const grandTotal = columnTotals.reduce((a, b) => a + b, 0);

	return (
    <div className="sheet-outer">
      {/* TOOLBAR */}
      <div className="history-toolbar">
        <button className="btn-back" onClick={goBack} title="Go back">
          ← Back
        </button>

        <div className="toolbar-divider" />

        <button className="btn-history" onClick={undo} disabled={!canUndo} title="Undo (Ctrl+Z)">
          ↩ Undo
        </button>
        <button className="btn-history" onClick={redo} disabled={!canRedo} title="Redo (Ctrl+Y)">
          ↪ Redo
        </button>
        <span className="history-label">
          {cursor} / {history.length - 1} changes
        </span>
      </div>
      <div className="table-wrapper">
        <table className="timesheet-table">
          <thead>
            <tr>
              <th>Hours Type</th>
              {data.map((day) => {
                const d = new Date(day.date);
                const weekday = d.toLocaleDateString("en-US", { weekday: "short" });
                return (
                  <th key={day.date}>
                    {day.date}<br />
                    <span className="weekday">{weekday}</span>
                  </th>
                );
              })}
              <th>Total</th>
            </tr>
          </thead>

          <tbody>
            {Array.from({ length: maxNormal }).map((_, index) => (
              <TimesheetRow
                key={`normal-${index}`}
                title="Shift Allowance"
                rowClass="shift-row"
                data={data}
                getEntry={(day) => day.normal?.[index]}
                getOverride={getOverride}
                onEntryChange={handleEntryChange}
              />
            ))}

            {Array.from({ length: maxOT15 }).map((_, index) => (
              <TimesheetRow
                key={`ot15-${index}`}
                title="Overtime 1.5"
                rowClass="ot15-row"
                data={data}
                getEntry={(day) => day.overtime.filter((ot) => !ot.is_weekend)[index]}
                getOverride={getOverride}
                onEntryChange={handleEntryChange}
              />
            ))}

            {Array.from({ length: maxOT20 }).map((_, index) => (
              <TimesheetRow
                key={`ot20-${index}`}
                title="Overtime 2.0"
                rowClass="ot20-row"
                data={data}
                getEntry={(day) => day.overtime.filter((ot) => ot.is_weekend)[index]}
                getOverride={getOverride}
                onEntryChange={handleEntryChange}
              />
            ))}

            {/* ADD ROW */}
            <tr className="add-row-tr">
              <td colSpan={data.length + 2}>
                <div className="add-row-container" ref={pickerRef}>
                  <button className="btn-add-row" onClick={() => setPickerOpen((o) => !o)}>
                    + Add Row
                  </button>
                  {pickerOpen && (
                    <div className="add-row-picker">
                      <button className="picker-option picker-option--shift" onClick={() => addRow("normal")}>Shift Allowance</button>
                      <button className="picker-option picker-option--ot15" onClick={() => addRow("ot15")}>Overtime 1.5</button>
                      <button className="picker-option picker-option--ot20" onClick={() => addRow("ot20")}>Overtime 2.0</button>
                    </div>
                  )}
                </div>
              </td>
            </tr>

            {/* TOTALS */}
            <tr className="grand-total-row">
              <td className="type-cell">Total Hours</td>
              {columnTotals.map((t, i) => (
                <td key={i} className="entry-cell"><strong>{t}hrs</strong></td>
              ))}
              <td className="row-total"><strong>{grandTotal}hrs</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
	);
}