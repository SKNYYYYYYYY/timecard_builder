from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from crop import crop_schedule
from shift_detector import parse_schedule
from helpers import *

app = FastAPI(title="Timecard Generator")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/")
def health():
	return {"status": "ok"}


@app.post("/parse")
async def parse_image(files: List[UploadFile] = File(...)):
	results = []
	parsed_schedules = []

	if len(files) != 2:
		raise HTTPException(
			status_code=400,
			detail={
				"message": "Please upload exactly two schedule images.",
				"stage": "validation"
			}
		)

	for file in files:
		try:
			content = await file.read()
			cropped_image = crop_schedule(
				content,
				x_offset=-10
			)

			result = parse_schedule(cropped_image)
			parsed_schedules.append(result)

			start, end = get_date_range(result)

			results.append({
				"filename": file.filename,
				"success": True,
				"data": result,
				"range": {
					"start": start,
					"end": end
				}
			})
			
		except Exception as e:
			results.append({
				"filename": file.filename,
				"success": False,
				"error": {
					"message": str(e),
					"stage": "parse_schedule"
				}
			})

	if not any(r["success"] for r in results):
		raise HTTPException(
			status_code=400,
			detail={
				"message": "All images failed to process",
				"results": results,
				"stage": "parse_schedule"
			}
		)

	if len(parsed_schedules) >= 2:
		month1 = get_month(parsed_schedules[0])
		month2 = get_month(parsed_schedules[1])

		if month1 != month2:
			raise HTTPException(
				status_code=400,
				detail={
					"message": "Both images must belong to the same month.",
					"stage": "validation"
				}
			)

	merged = parsed_schedules[0]
	for s in parsed_schedules[1:]:
		merged = merge_schedules(merged, s)

	merged = sort_schedule(merged)

	return {
		"success": True,
		"results": results,
		"data": merged
	}

if __name__ == "__main__":
	import uvicorn

	uvicorn.run(
		"app:app",
		host="0.0.0.0",
		port=8000,
		reload=True
	)