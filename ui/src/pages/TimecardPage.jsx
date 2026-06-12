import TimesheetTable from "../components/TimesheetTable";
import "../styles/TimecardPage.css";

export default function TimecardPage({ timecard, onBack }) {
	if (!timecard) {
		return (
			<div className="timecard-page">
				<p style={{ color: "#fff" }}>No timecard data available.</p>

				{onBack && (
					<button onClick={onBack}>
						← Back
					</button>
				)}
			</div>
		);
	}

	const data = Object.entries(timecard || {}).map(([date, day]) => ({
		date,
		...day,
		normal: Array.isArray(day?.normal) ? day.normal : [],
		overtime: Array.isArray(day?.overtime) ? day.overtime : [],
	}));

return (
    <div className="timecard-page">
        <div className="timecard-container">
            <TimesheetTable 
              data={data}
              goBack={onBack}
            />
        </div>
    </div>
);
}