"""Authenticated, bounded, request-only physio dialogue proposal endpoint."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from schemas.dialogue import PhysioDialogueRequest, PhysioDialogueResponse
from services.grounded_dialogue_service import propose, unavailable

MAX_REQUEST_BYTES = 32_768


def create_evidence_router(*, authenticate, generate, provider_configured, limiter):
    router = APIRouter()

    @router.post('/api/physio/dialogue', response_model=PhysioDialogueResponse)
    @limiter.limit('10/minute')
    async def physio_dialogue(request: Request, device=Depends(authenticate)):
        # No subject/user lookup, no server memory, no records written.
        if request.query_params:
            return JSONResponse(status_code=422, content=unavailable('invalid_request').model_dump(mode='json'))
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > MAX_REQUEST_BYTES:
                return JSONResponse(status_code=413, content=unavailable('invalid_request').model_dump(mode='json'))
        try:
            body = PhysioDialogueRequest.model_validate_json(raw)
        except (ValidationError, ValueError):
            return JSONResponse(status_code=422, content=unavailable('invalid_request').model_dump(mode='json'))
        return await propose(body, generate=generate, provider_configured=provider_configured)

    return router
