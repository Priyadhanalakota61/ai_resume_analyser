from flask import Blueprint, render_template, request

from app.scoring import calculate_match_score

from app.database import (
    DatabaseConfigurationError,
    DatabaseSaveError,
    ensure_database_ready,
    save_analysis,
)
from app.services.gemini_analyzer import (
    GeminiAnalysisError,
    GeminiConfigurationError,
    analyze_resume,
)
from app.services.pdf_extractor import PdfExtractionError, extract_resume_text

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return render_template("index.html")

    resume_file = request.files.get("resume_pdf")
    job_description = request.form.get("job_description", "").strip()
    consent = request.form.get("gemini_data_consent")

    if not resume_file or not resume_file.filename:
        return render_template("index.html", error="Choose a resume PDF.")
    if not resume_file.filename.lower().endswith(".pdf"):
        return render_template("index.html", error="Upload a file with a .pdf extension.")
    if not job_description:
        return render_template("index.html", error="Enter the job description.")
    if consent != "yes":
        return render_template(
            "index.html",
            error="Confirm that the resume is synthetic or anonymized before analysis.",
        )

    try:
        resume_text = extract_resume_text(resume_file.read())
    except PdfExtractionError as exc:
        return render_template("index.html", error=str(exc))

    try:
        ensure_database_ready()
    except (DatabaseConfigurationError, DatabaseSaveError) as exc:
        return render_template(
            "index.html",
            error=f"{exc} No text was sent to Gemini.",
        )

    try:
        insights = analyze_resume(resume_text, job_description)
    except GeminiConfigurationError as exc:
        return render_template("index.html", error=str(exc))
    except GeminiAnalysisError as exc:
        return render_template("index.html", error=str(exc))

    result = insights.model_dump(mode="json")
    result["job_match_score"] = calculate_match_score(result["requirements"])

    try:
        record_id = save_analysis(resume_text, result)
    except (DatabaseConfigurationError, DatabaseSaveError) as exc:
        return render_template(
            "index.html",
            error=f"{exc} Gemini returned an analysis, but it was not saved.",
        )

    return render_template(
        "results.html",
        result=result,
        record_id=record_id,
    )
