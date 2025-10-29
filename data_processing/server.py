from fastapi import FastAPI
from fastapi.responses import JSONResponse
from crawler import collect_complaints

app = FastAPI()

@app.post("/run-main")
def run_main():
    try:
        data = collect_complaints("santander", complaint_number=6, wait_seconds=10)
        return JSONResponse({"status": "success", "data": data})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
