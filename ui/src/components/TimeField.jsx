import { useState } from "react";

export default function TimeField({ label, value }) {
	const [copied, setCopied] = useState(false);

	const handleCopy = () => {
		if (!value) return;
		navigator.clipboard.writeText(value).then(() => {
			setCopied(true);
			setTimeout(() => setCopied(false), 1200);
		});
	};

	return (
		<div className="time-field">
			<span className="label">{label}</span>
			<span
				className={`time-value${value ? " copyable" : ""}`}
				onClick={handleCopy}
				title={value ? "Click to copy" : undefined}
			>
				{copied ? <span className="copied-flash">Copied!</span> : value}
			</span>
		</div>
	);
}