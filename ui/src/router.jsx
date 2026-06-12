import { BrowserRouter, Routes, Route } from "react-router-dom";

import UploadPage from "./pages/UploadPage";
import TimecardPage from "./pages/TimecardPage";

export default function App() {
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/" element={<UploadPage />} />
				<Route path="/timecard" element={<TimecardPage />} />
			</Routes>
		</BrowserRouter>
	);
}