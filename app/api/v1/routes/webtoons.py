# app/api/v1/routes/webtoons.py
"""
Webtoon management API routes
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.application.services.webtoon_service import WebtoonService
from app.dependencies import get_webtoon_service
from app.schemas.webtoon_schemas import (
    CharacterCreateRequest,
    PanelCreateRequest,
    WebtoonCreateRequest,
    WebtoonListResponse,
    WebtoonResponse,
)

router = APIRouter()


@router.post("/", response_model=WebtoonResponse)
async def create_webtoon(
    request: WebtoonCreateRequest,
    service: WebtoonService = Depends(get_webtoon_service),
):
    """Create a new webtoon"""
    try:
        webtoon_dto = await service.create_webtoon(
            title=request.title,
            description=request.description,
            art_style=request.art_style.value,
        )
        return WebtoonResponse.from_dto(webtoon_dto)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webtoon_id}", response_model=WebtoonResponse)
async def get_webtoon(
    webtoon_id: UUID, service: WebtoonService = Depends(get_webtoon_service)
):
    """Get a webtoon by ID"""
    webtoon_dto = await service.get_webtoon(webtoon_id)
    if not webtoon_dto:
        raise HTTPException(status_code=404, detail="Webtoon not found")

    return WebtoonResponse.from_dto(webtoon_dto)


@router.get("/", response_model=WebtoonListResponse)
async def list_webtoons(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    service: WebtoonService = Depends(get_webtoon_service),
):
    """List webtoons with optional search"""
    try:
        if keyword:
            webtoons = await service.search_webtoons(keyword)
        else:
            # Get all webtoons (in production, add pagination)
            webtoons = await service.get_all_webtoons()

        return WebtoonListResponse(
            webtoons=[WebtoonResponse.from_dto(w) for w in webtoons],
            total=len(webtoons),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{webtoon_id}/characters")
async def add_character(
    webtoon_id: UUID,
    request: CharacterCreateRequest,
    service: WebtoonService = Depends(get_webtoon_service),
):
    """Add a character to a webtoon"""
    from app.domain.entities.character import Character, CharacterAppearance

    # Convert the Pydantic model to a dictionary using model_dump() (Pydantic v2)
    appearance_dict = request.appearance.model_dump()

    character = Character(
        name=request.name,
        description=request.description,
        appearance=CharacterAppearance(**appearance_dict),
        personality_traits=request.personality_traits,
        role=request.role,
    )

    webtoon_dto = await service.add_character(webtoon_id, character)
    if not webtoon_dto:
        raise HTTPException(status_code=404, detail="Webtoon not found")

    return JSONResponse({"message": "Character added successfully"})


@router.post("/{webtoon_id}/panels")
async def add_panel(
    webtoon_id: UUID,
    request: PanelCreateRequest,
    service: WebtoonService = Depends(get_webtoon_service),
):
    """Add a panel to a webtoon"""
    from app.domain.entities.panel import Panel
    from app.domain.entities.scene import Scene
    from app.domain.value_objects.dimensions import PanelDimensions, PanelSize

    scene = Scene(
        description=request.scene_description,
        character_names=request.character_names,
    )

    panel = Panel(
        scene=scene,
        dimensions=PanelDimensions.from_size(PanelSize(request.panel_size)),
    )

    webtoon_dto = await service.add_panel(webtoon_id, panel)
    if not webtoon_dto:
        raise HTTPException(status_code=404, detail="Webtoon not found")

    return JSONResponse({"message": "Panel added successfully"})


@router.patch("/{webtoon_id}/publish")
async def publish_webtoon(
    webtoon_id: UUID, service: WebtoonService = Depends(get_webtoon_service)
):
    """Publish a webtoon"""
    success = await service.publish_webtoon(webtoon_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webtoon not found")

    return JSONResponse({"message": "Webtoon published successfully"})
