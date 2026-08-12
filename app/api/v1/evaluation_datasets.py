from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.evaluation import EvaluationDataset, EvaluationCase
from app.evaluation.datasets import dataset_registry
from app.evaluation.cases import case_registry

router = APIRouter(prefix="/evaluation-datasets", tags=["Evaluation Datasets & Cases"])

@router.post("", response_model=EvaluationDataset)
async def create_evaluation_dataset(dataset: EvaluationDataset):
    """
    Register a new evaluation dataset in the registry.
    """
    return dataset_registry.register_dataset(dataset)

@router.get("", response_model=List[EvaluationDataset])
async def list_evaluation_datasets():
    """
    List all active evaluation benchmark datasets.
    """
    return dataset_registry.list_datasets()

@router.get("/{dataset_id}", response_model=EvaluationDataset)
async def get_evaluation_dataset(dataset_id: str):
    """
    Get metadata for a specific evaluation dataset.
    """
    dataset = dataset_registry.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return dataset

@router.get("/{dataset_id}/cases", response_model=List[EvaluationCase])
async def list_cases_for_dataset(dataset_id: str):
    """
    List all evaluation cases in a dataset.
    """
    dataset = dataset_registry.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return case_registry.list_cases_for_dataset(dataset_id)

@router.post("/{dataset_id}/cases", response_model=EvaluationCase)
async def add_case_to_dataset(dataset_id: str, case: EvaluationCase):
    """
    Add a new evaluation case to a dataset.
    """
    dataset = dataset_registry.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    case.dataset_id = dataset_id
    registered = case_registry.register_case(case)
    dataset.total_cases = len(case_registry.list_cases_for_dataset(dataset_id))
    return registered
