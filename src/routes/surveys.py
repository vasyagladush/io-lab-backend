import io
import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Annotated, Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException
from fastapi.responses import FileResponse
from matplotlib.dates import date2num
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import services.grades as GradeService
import services.surveys as SurveyService
from config import DBSessionDep, hash_helper
from models.surveys import Survey
from schemas.surveys import SurveyPlusSchema, SurveySchema
from services.auth import (
    AdminAccessCheckDep,
    AuthJWTTokenPayload,
    AuthJWTTokenValidatorDep,
    construct_auth_jwt,
)

router = APIRouter()


@router.post("/", status_code=201, response_model=SurveyPlusSchema)
async def create_survey(
    db_session: DBSessionDep,
    auth_token_body: Annotated[AuthJWTTokenPayload, AdminAccessCheckDep],
    response_model=SurveyPlusSchema,
    body: SurveySchema = Body(...),
) -> Survey:

    new_survey = await SurveyService.create_survey(db_session, body)
    return new_survey


@router.get(
    "/current",
    status_code=200,
    response_model=Sequence[SurveyPlusSchema],
    dependencies=[AuthJWTTokenValidatorDep],
)
async def get_current_surveys(
    db_session: DBSessionDep,
):
    # Pobierz wszystkie ankiety, ustawiając pustą listę jako domyślną wartość
    all_surveys = await SurveyService.get_all_survey(db_session) or []

    # Filtruj ankiety, które są aktualnie otwarte
    now = datetime.now()
    current_surveys = [
        survey
        for survey in all_surveys
        if survey.start_at <= now <= survey.finishes_at
    ]

    return current_surveys


@router.get("/{id}", status_code=200, response_model=SurveyPlusSchema)
async def get_survey(
    db_session: DBSessionDep,
    id,
    auth_token_body: Annotated[AuthJWTTokenPayload, AdminAccessCheckDep],
) -> list:

    survey = await SurveyService.get_survey(db_session, id)
    return survey


@router.get("/", status_code=200, response_model=Sequence[SurveyPlusSchema])
async def get_all_surveys(
    db_session: DBSessionDep,
    auth_token_body: Annotated[AuthJWTTokenPayload, AdminAccessCheckDep],
) -> list:

    survey_list = await SurveyService.get_all_survey(db_session)
    return survey_list


def cleanup_temp_report_directory(path: str):
    shutil.rmtree(path)


@router.get(
    "/{id}/report",
    status_code=200,
    responses={401: {}},
)
async def get_report(
    id,
    db_session: DBSessionDep,
    auth_token_body: Annotated[AuthJWTTokenPayload, AdminAccessCheckDep],
    background_tasks: BackgroundTasks,
):
    survey: Survey | None = await SurveyService.get_survey(db_session, id)
    if not survey:
        raise HTTPException(status_code=404, detail="No survey found")

    grades_data = await GradeService.get_grades_by_survey(db_session, id)

    # Create a unique folder for storing temporary files
    report_id = uuid.uuid4()
    temp_dir = f"reports/{report_id}"
    os.makedirs(temp_dir, exist_ok=True)

    # File paths within the unique folder
    hist_filename = os.path.join(temp_dir, "histogram.png")
    pdf_path = os.path.join(temp_dir, "report.pdf")

    # Extract grades and created_at timestamps for analysis
    grades = [entry.grade for entry in grades_data]
    timestamps = [entry.created_at for entry in grades_data]

    # 1. Create a histogram

    # Parse start and end times for the survey
    started_at = survey.start_at
    closes_at = survey.finishes_at

    # Calculate total time span and 5% intervals
    total_duration = closes_at - started_at
    interval_duration = timedelta(seconds=total_duration.total_seconds() / 20)
    # Each bin represents 5% of the total time

    # Create time bins (20 bins, each 5% of total time)
    time_bins = [started_at + i * interval_duration for i in range(21)]
    time_bins_numeric = date2num(time_bins)

    # Extract vote timestamps for histogram calculation
    grade_times = [entry.created_at for entry in grades_data]

    # Count the number of votes in each time bin
    grade_counts = []
    for i in range(len(time_bins) - 1):
        start = time_bins[i]
        end = time_bins[i + 1]
        count = sum(start <= grade_time < end for grade_time in grade_times)
        grade_counts.append(count)

    # 1. Plot Histogram
    plt.figure(figsize=(10, 6))
    plt.bar(time_bins[:-1], grade_counts, width=interval_duration, align="edge", color="skyblue")  # type: ignore
    plt.xlabel("Time")
    plt.ylabel("Number of grades")
    plt.title("Distribution of grades over time")

    # Format x-axis as dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)

    # Display each bin's start time on the x-axis
    bin_labels = [bin_start.strftime("%H:%M") for bin_start in time_bins]
    plt.xticks(
        time_bins_numeric, bin_labels, rotation=45, ha="right", fontsize=8
    )  # type:ignore

    # Save the histogram image to the temporary folder
    plt.savefig(hist_filename, format="png")
    plt.close()

    # 2. Generate PDF report
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Title
    c.drawString(100, 750, f"Report: results for the '{survey.title}' survey")
    c.drawString(100, 730, f"Average grade {sum(grades)/len(grades)}")

    # Include histogram
    c.drawImage(
        hist_filename, 100, 420, width=400, height=300
    )  # Adjust position and size as needed

    # 3. Add summary of voting results (count of each grade)
    grade_counts = {grade: grades.count(grade) for grade in set(grades)}
    summary_y_position = 400
    c.drawString(100, summary_y_position, "Summary of grades:")
    for grade, count in grade_counts.items():
        summary_y_position -= 20
        c.drawString(120, summary_y_position, f"Grade {grade}: {count} votes")

    # 4. List each vote with timestamp and user_id
    list_y_position = summary_y_position - 40
    c.drawString(100, list_y_position, "Detailed list of grade:")
    for entry in grades_data:
        list_y_position -= 20
        c.drawString(
            120,
            list_y_position,
            f"User gave a grade of {entry.grade} on {entry.created_at}",
        )

    # Finalize and save the PDF
    c.showPage()
    c.save()

    # Schedule cleanup of the temporary folder after response is sent
    background_tasks.add_task(cleanup_temp_report_directory, temp_dir)

    return FileResponse(
        pdf_path, media_type="application/pdf", filename="report.pdf"
    )
