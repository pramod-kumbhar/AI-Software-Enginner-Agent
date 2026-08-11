from fastapi import APIRouter, HTTPException
from typing import List
from app.modules.string.schemas import stringCreate, stringResponse
from app.modules.string.service import string_service

router = APIRouter(prefix="/string", tags=["string"])

@router.post("", response_model=stringResponse, status_code=201)
def create_record(payload: stringCreate):
    record = string_service.create(payload)
    return record

@router.get("", response_model=List[stringResponse])
def list_records():
    return string_service.list_all()

@router.get("/{record_id}", response_model=stringResponse)
def get_record(record_id: str):
    record = string_service.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record
