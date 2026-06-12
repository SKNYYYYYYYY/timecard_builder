const API_URL = "http://localhost:8000";
export async function uploadSchedule(files) {
	const formData = new FormData();

	files.forEach(file => {
		formData.append("files", file);
	});

	const response = await fetch(`${API_URL}/parse`, {
		method: "POST",
		body: formData,
	});

	const data = await response.json();

	if (!response.ok) {
		throw new Error(
			data?.detail?.message || "Upload failed"
		);
	}

	return data;
}