from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    LeadershipEmployeeCreate,
    LeadershipEmployeeRead,
    LeadershipEmployeeUpdate,
    LeadershipRecordCreate,
    LeadershipRecordRead,
    LeadershipTokenResponse,
    LoginRequest,
)
from ..security import (
    clear_session_cookie,
    create_leadership_access_token,
    get_current_leadership,
    set_session_cookie,
    verify_leadership_credentials,
)
from ..services.leadership_service import LeadershipService

router = APIRouter(prefix="/leadership", tags=["leadership"])


def get_leadership_service(db: Session = Depends(get_db)) -> LeadershipService:
    return LeadershipService(db)


@router.post("/login", response_model=LeadershipTokenResponse)
def leadership_login(payload: LoginRequest, response: Response) -> LeadershipTokenResponse:
    if not verify_leadership_credentials(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario ou senha invalidos")
    token = create_leadership_access_token()
    set_session_cookie(response, token, leadership=True)
    return LeadershipTokenResponse(access_token=token)


@router.post("/logout")
def leadership_logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response, leadership=True)
    return {"status": "ok"}


@router.get("/me")
def leadership_me(username: str = Depends(get_current_leadership)) -> dict[str, str]:
    return {"username": username, "area": "leadership"}


@router.get("/employees", response_model=list[LeadershipEmployeeRead])
def list_employees(
    _: str = Depends(get_current_leadership),
    service: LeadershipService = Depends(get_leadership_service),
) -> list[LeadershipEmployeeRead]:
    return service.list_employees()


@router.post("/employees", response_model=LeadershipEmployeeRead)
def create_employee(
    payload: LeadershipEmployeeCreate,
    _: str = Depends(get_current_leadership),
    service: LeadershipService = Depends(get_leadership_service),
) -> LeadershipEmployeeRead:
    return service.create_employee(payload)


@router.patch("/employees/{employee_id}", response_model=LeadershipEmployeeRead)
def update_employee(
    employee_id: int,
    payload: LeadershipEmployeeUpdate,
    _: str = Depends(get_current_leadership),
    service: LeadershipService = Depends(get_leadership_service),
) -> LeadershipEmployeeRead:
    return service.update_employee(employee_id, payload)


@router.get("/records", response_model=list[LeadershipRecordRead])
def list_records(
    _: str = Depends(get_current_leadership),
    service: LeadershipService = Depends(get_leadership_service),
) -> list[LeadershipRecordRead]:
    return service.list_records()


@router.get("/employees/{employee_id}/records", response_model=list[LeadershipRecordRead])
def list_employee_records(
    employee_id: int,
    _: str = Depends(get_current_leadership),
    service: LeadershipService = Depends(get_leadership_service),
) -> list[LeadershipRecordRead]:
    return service.list_records(employee_id=employee_id)


@router.post("/employees/{employee_id}/records", response_model=LeadershipRecordRead)
def create_employee_record(
    employee_id: int,
    payload: LeadershipRecordCreate,
    username: str = Depends(get_current_leadership),
    service: LeadershipService = Depends(get_leadership_service),
) -> LeadershipRecordRead:
    return service.create_record(employee_id, payload, created_by=username)
