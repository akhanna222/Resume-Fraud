from dotenv import load_dotenv
load_dotenv()  # must run before any module reads os.getenv

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from detectors import run_all

app = FastAPI(title="Resume Fraud Detector — Stage 1")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html") as f:
        return f.read()


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    jd: str = Form(...),
    email: str = Form(""),
):
    pdf_bytes = await resume.read()
    return await run_all(pdf_bytes, jd, email)
