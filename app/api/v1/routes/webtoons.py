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
    webtoon_dto = await service.create_webtoon(
        title=request.title,
        description=request.description,
        art_style=request.art_style,
    )
    return WebtoonResponse.from_dto(webtoon_dto)


@router.get("/{webtoon_id}", response_model=WebtoonResponse)
async def get_webtoon(
    webtoon_id: UUID, 
    include_html: bool = Query(False, description="Include HTML content for rendering"),
    service: WebtoonService = Depends(get_webtoon_service)
):
    """Get a webtoon by ID"""
    webtoon_dto = await service.get_webtoon(webtoon_id)
    if not webtoon_dto:
        from app.api.exception_handlers import NotFoundException
        raise NotFoundException("Webtoon not found")

    # Create the response
    response = WebtoonResponse.from_dto(webtoon_dto)
    
    # Add HTML content if requested
    if include_html:
        html_content = await service.get_webtoon_html_content(webtoon_id)
        if not html_content:
            from app.api.exception_handlers import BadRequestException
            raise BadRequestException("Failed to generate HTML content")
        response.html_content = html_content
        
    return response


@router.get("/", response_model=WebtoonListResponse)
async def list_webtoons(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    service: WebtoonService = Depends(get_webtoon_service),
):
    """List webtoons with optional search"""
    if keyword:
        webtoons = await service.search_webtoons(keyword)
    else:
        # Get all webtoons (in production, add pagination)
        webtoons = await service.get_all_webtoons()

    return WebtoonListResponse(
        webtoons=[WebtoonResponse.from_dto(w) for w in webtoons],
        total=len(webtoons),
    )


@router.post("/{webtoon_id}/characters", response_model=WebtoonResponse)
async def add_character(
    webtoon_id: UUID,
    request: CharacterCreateRequest,
    service: WebtoonService = Depends(get_webtoon_service),
):
    """Add a character to a webtoon"""
    # Convert the Pydantic model to a dictionary
    appearance_dict = request.appearance.model_dump()
    
    # Call the refactored service method with individual parameters
    webtoon_dto = await service.add_character(
        webtoon_id=webtoon_id,
        name=request.name,
        description=request.description,
        appearance_data=appearance_dict,
        personality_traits=request.personality_traits,
        role=request.role
    )
    
    if not webtoon_dto:
        from app.api.exception_handlers import NotFoundException
        raise NotFoundException("Webtoon not found")
    
    # Return a consistent response model
    return WebtoonResponse.from_dto(webtoon_dto)


@router.post("/{webtoon_id}/panels", response_model=WebtoonResponse)
async def add_panel(
    webtoon_id: UUID,
    request: PanelCreateRequest,
    service: WebtoonService = Depends(get_webtoon_service),
):
    """Add a panel to a webtoon"""
    # Call the refactored service method with individual parameters
    webtoon_dto = await service.add_panel(
        webtoon_id=webtoon_id,
        scene_description=request.scene_description,
        character_names=request.character_names,
        panel_size=request.panel_size
    )
    
    if not webtoon_dto:
        from app.api.exception_handlers import NotFoundException
        raise NotFoundException("Webtoon not found")
    
    # Return a consistent response model
    return WebtoonResponse.from_dto(webtoon_dto)


@router.patch("/{webtoon_id}/publish", response_model=WebtoonResponse)
async def publish_webtoon(
    webtoon_id: UUID, service: WebtoonService = Depends(get_webtoon_service)
):
    """Publish a webtoon"""
    success = await service.publish_webtoon(webtoon_id)
    if not success:
        from app.api.exception_handlers import NotFoundException
        raise NotFoundException("Webtoon not found")
    
    # Get the updated webtoon to return a consistent response
    webtoon_dto = await service.get_webtoon(webtoon_id)
    return WebtoonResponse.from_dto(webtoon_dto)
