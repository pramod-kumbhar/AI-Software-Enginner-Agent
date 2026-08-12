import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from app.tools.github.handlers import GitHubToolHandlers
from app.services.storage import storage_service

router = APIRouter(prefix="/github", tags=["GitHub Integration"])

class CreatePRRequest(BaseModel):
    title: str
    body: str
    head_branch: str
    base_branch: str = "main"
    approval_confirmed: bool = True
    reviewer_name: str = "Engineering_Lead"

@router.get("/{owner}/{repo}")
async def get_repository_info(owner: str, repo: str):
    """Retrieves repository metadata from GitHub REST API."""
    try:
        return await GitHubToolHandlers.get_repository(owner=owner, repo=repo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{owner}/{repo}/pull-requests")
async def create_pull_request_route(owner: str, repo: str, payload: CreatePRRequest):
    """
    Creates a Pull Request on GitHub following explicit human approval.
    """
    if not payload.approval_confirmed:
        raise HTTPException(status_code=403, detail="Pull request creation requires explicit human approval.")
        
    try:
        res = await GitHubToolHandlers.create_pull_request(
            title=payload.title,
            body=payload.body,
            head_branch=payload.head_branch,
            base_branch=payload.base_branch,
            owner=owner,
            repo=repo
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{owner}/{repo}/pull-requests/{pull_number}")
async def get_pull_request_route(owner: str, repo: str, pull_number: int):
    """Retrieves a specific Pull Request by number."""
    try:
        return await GitHubToolHandlers.get_pull_request(pull_number=pull_number, owner=owner, repo=repo)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/search/repositories")
async def search_repositories_route(query: str, language: str = "python", limit: int = 5):
    """Search public open-source repositories on GitHub."""
    try:
        return await GitHubToolHandlers.search_public_repositories(query=query, language=language, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/code")
async def search_code_route(query: str, language: str = "python", limit: int = 5):
    """Search public code snippets on GitHub."""
    try:
        return await GitHubToolHandlers.search_code_snippets(query=query, language=language, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/public-file")
async def get_public_file_route(owner: str, repo: str, path: str, ref: str = "main"):
    """Fetch raw source code from any public GitHub repository."""
    try:
        return await GitHubToolHandlers.fetch_public_file_content(owner=owner, repo=repo, file_path=path, ref=ref)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
