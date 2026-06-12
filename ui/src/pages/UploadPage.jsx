import { useState } from "react";
import { Calendar,  CheckCircle2, ImagePlus, Loader2, Wand2, ShieldAlert  } from "lucide-react";
import { uploadSchedule } from "../services/api";
import TimecardPage from "./TimecardPage";
import "../styles/UploadPage.css";

export default function UploadPage() {
	const [file1, setFile1] = useState(null);
	const [file2, setFile2] = useState(null);

	const [fileKey, setFileKey] = useState(0);

	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");

	const [results, setResults] = useState([]);
	const [timecard, setTimecard] = useState(null);

	const [showDecision, setShowDecision] = useState(false);
	const [showTimecard, setShowTimecard] = useState(false);

	const closeError = () => setError("");

	const bothSelected = file1 && file2;

	const handleUpload = async () => {
		if (!bothSelected || loading) return;

		setLoading(true);
		setError("");
		setShowDecision(false);
		setShowTimecard(false);

		try {
			const result = await uploadSchedule([file1, file2]);
 console.log("API result:", result);
			setResults(result.results || []);
			setTimecard(result.data || null);

			const hasSuccess = result.results?.some(r => r.success);
			const hasFailure = result.results?.some(r => !r.success);

			if (hasSuccess && hasFailure) {
				setShowDecision(true);
			} else if (hasSuccess) {
				setShowTimecard(true);
			} else {
				setError("Both images failed to process");
			}
		} catch (err) {
			setError(err?.message || "Something went wrong");
		} finally {
			setLoading(false);
		}
	};

	const truncate = (name, max = 22) =>
		name?.length > max ? name.slice(0, max - 1) + "…" : name;

	const resetUpload = () => {
		setFile1(null);
		setFile2(null);
		setResults([]);
		setTimecard(null);
		setShowDecision(false);
		setShowTimecard(false);
		setFileKey(k => k + 1);
	};

	// ✅ TIMECARD VIEW (FIXED)
	if (showTimecard && timecard) {
		return (
				<TimecardPage
					timecard={timecard}
					onBack={() => setShowTimecard(false)}
				/>
		);
	}

	return (
		<div className="upload-page">
			<div className="upload-card">

				{/* Header */}
				<div className="upload-header">
					<div className="upload-header-icon"><Calendar /></div>
					<div className="upload-header-text">
						<h1>Timecard Generator</h1>
            <p>Upload two screenshots of your monthly shift schedule to generate a timecard.</p>
					</div>
				</div>

				<hr className="upload-divider" />

				{/* Progress */}
				<div className="upload-pips">
					<div className={`upload-pip${file1 ? " active" : ""}`} />
					<div className={`upload-pip${file2 ? " active" : ""}`} />
				</div>

				{/* File inputs */}
				<div className="upload-slots">
					{[
						{ num: "01", file: file1, setFile: setFile1, label: "First image" },
						{ num: "02", file: file2, setFile: setFile2, label: "Second image" },
					].map(({ num, file, setFile, label }) => (
						<label key={num} className={`upload-slot${file ? " filled" : ""}`}>
							<input
								key={fileKey}
								type="file"
								accept="image/*"
								hidden
								onChange={(e) => setFile(e.target.files[0] || null)}
							/>

							<span className="upload-slot-num">{num}</span>
							<span className="upload-slot-icon">
							{file ? <CheckCircle2 size={20} /> : <ImagePlus size={20} />}
							</span>
							<span className="upload-slot-label">
								{file ? truncate(file.name) : label}
							</span>
						</label>
					))}
				</div>

				<p className="upload-hint">
					<span></span> PNG or JPG
				</p>

				{/* Upload button */}
				<button
					className="upload-btn"
					onClick={handleUpload}
					disabled={!bothSelected || loading}
				>
        {
          loading ? (
            <>
              <Loader2 className="animate-spin" size={16} />
              Processing…
            </>
          ) : bothSelected ? (
            <>
              <Wand2 size={16} />
              Upload
            </>
          ) : (
            <>
              <ShieldAlert size={16} />
                 Select both images to continue
            </>
          )
        }
				</button>

				{/* View timecard */}
        {timecard && (
            <button
                className="upload-nav-btn"
                onClick={() => setShowTimecard(true)}
            >
                ↗ View timecard
            </button>
        )}
			</div>

			{/* Error modal */}
			{error && (
				<div className="error-overlay" onClick={closeError}>
					<div className="error-modal" onClick={(e) => e.stopPropagation()}>
						<div className="error-icon-wrap">⚠️</div>
						<h2>Upload failed</h2>
						<p>{error}</p>
						<button onClick={closeError}>Dismiss</button>
					</div>
				</div>
			)}

			{/* Partial success */}
			{showDecision && (
				<div className="error-overlay" onClick={() => setShowDecision(false)}>
					<div className="error-modal" onClick={(e) => e.stopPropagation()}>
						<h2>Partial success</h2>
						<p>At least one image was processed successfully.</p>

						<div className="result-list">
							{results.map((r, i) => (
								<div key={i} className="result-item">
									<strong>{r.filename}</strong>
									{r.success ? (
										<span className="ok">✔ processed</span>
									) : (
										<span className="fail">❌ {r.error?.message || r.error}</span>
									)}
								</div>
							))}
						</div>

						<div className="modal-actions">
							<button onClick={() => setShowTimecard(true)}>
								Proceed
							</button>

							<button onClick={resetUpload}>
								Re-upload
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}