import io
import os
import shutil
import uuid
from datetime import datetime
from typing import Annotated, Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import services.grades as GradeService
import services.surveys as SurveyService
import services.user as UserService
from config import DBSessionDep, hash_helper
from models.surveys import Survey
from models.user import User
from schemas.user import (
    UserLoginCredentialsSchema,
    UserLoginResponseSchema,
    UserModSchema,
    UserPlusSchema,
    UserSchema,
    UserSignUpSchema,
)
from services.auth import (
    AdminAccessCheckDep,
    AuthJWTTokenPayload,
    AuthJWTTokenValidatorDep,
    construct_auth_jwt,
)

router = APIRouter()


@router.post("/", status_code=200, response_model=UserLoginResponseSchema)
async def create(
    db_session: DBSessionDep,
    auth_token_body: Annotated[AuthJWTTokenPayload, AdminAccessCheckDep],
    user_credentials: UserLoginCredentialsSchema = Body(...),
):
    existing_user: User | None = await UserService.get_user_by_username(
        db_session, user_credentials.username
    )

    if existing_user:
        password_valid: bool = hash_helper.verify(
            user_credentials.password, existing_user.password_hash
        )

        if password_valid:
            return construct_auth_jwt(existing_user)

        raise HTTPException(
            status_code=401, detail="Incorrect username or password"
        )

    raise HTTPException(
        status_code=401, detail="Incorrect username or password"
    )


@router.post(
    "/",
    status_code=201,
    response_model=UserSchema,
)
async def create_user(
    db_session: DBSessionDep,
    body: UserSignUpSchema = Body(...),
) -> User:
    """Creates User with specified details"""
    existing_user: User | None = await UserService.get_user_by_username(
        db_session, body.username
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User with the provided username already exists",
        )

    new_user = await UserService.create_user(db_session, body)
    return new_user


@router.get(
    "/current",
    status_code=200,
    response_model=UserPlusSchema,
    responses={401: {}},
)
async def get_current_user(
    auth_token_body: Annotated[AuthJWTTokenPayload, AuthJWTTokenValidatorDep],
    db_session: DBSessionDep,
):
    user: User | None = await UserService.get_user(
        db_session, auth_token_body["user_id"]
    )
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    return user


@router.get(
    "/all",
    status_code=200,
    response_model=Sequence[UserPlusSchema],
    responses={401: {}},
    dependencies=[AdminAccessCheckDep],
)
async def get_all_users(
    db_session: DBSessionDep,
):
    users = await UserService.get_users(db_session)
    return users


@router.get(
    "/{id}",
    status_code=200,
    response_model=UserPlusSchema,
    responses={401: {}},
)
async def get_user(
    id,
    db_session: DBSessionDep,
):
    user: User | None = await UserService.get_user(db_session, id)
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    return user


def cleanup_temp_report_directory(path: str):
    shutil.rmtree(path)


@router.get(
    "/{id}/report",
    status_code=200,
    # response_model=UserPlusSchema,
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
    interval_duration = (
        total_duration / 20
    )  # Each bin represents 5% of the total time

    # Create time bins (20 bins, each 5% of total time)
    time_bins = [started_at + i * interval_duration for i in range(21)]

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
        time_bins, bin_labels, rotation=45, ha="right", fontsize=8
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


@router.delete("/{id}", status_code=204, dependencies=[AdminAccessCheckDep])
async def delete_user(
    id,
    db_session: DBSessionDep,
):
    """Deletes User with database id"""
    user_to_delete: User | None = await UserService.get_user(db_session, id)

    if user_to_delete is None:
        raise HTTPException(
            status_code=400,
            detail="User does not exist",
        )

    await db_session.delete(user_to_delete)
    await db_session.commit()
    return


@router.put("/{id}", status_code=204)
async def modify_user(
    id,
    db_session: DBSessionDep,
    auth_token_body: Annotated[AuthJWTTokenPayload, AdminAccessCheckDep],
    config: UserModSchema,
):
    """Allows modification of user. Password can be changed only by the user."""
    user: User | None = await UserService.get_user(db_session, id)

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="User does not exist",
        )
    update_data = dict(config)

    if update_data["password"] is not None:
        if auth_token_body["user_id"] != id:
            await db_session.rollback()
            raise HTTPException(
                status_code=400,
                detail="Cannot change password of another user",
            )
        if len(update_data["password"]) < 8:
            await db_session.rollback()
            raise HTTPException(status_code=400, detail="Password too short")
        user.password = update_data["password"]

    if update_data["username"] is not None:
        check = await UserService.get_user_by_username(
            db_session, update_data["username"]
        )
        if check is not None and str(check.id) != id:
            await db_session.rollback()
            raise HTTPException(
                status_code=400,
                detail="User with this username already exists",
            )
        user.name = update_data["username"]

    if update_data["first_name"] is not None:
        user.first_name = update_data["first_name"]

    if update_data["last_name"] is not None:
        user.last_name = update_data["last_name"]

    if update_data["is_admin"] is not None:
        user.is_admin = update_data["is_admin"]

    await db_session.commit()
    return
