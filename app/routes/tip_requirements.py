from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, TipEntryRequirement
from app.auth.jwt_handler import get_current_user
from app.utils.slugify import create_slug, ensure_unique_slug

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/tip-requirements/new")
async def create_tip_requirement(
    request: Request,
    name: str = Form(...),
    field_name: str = Form(...),
    display_order: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slug = ensure_unique_slug(db, TipEntryRequirement, create_slug(name))

    new_requirement = TipEntryRequirement(
        name=name,
        slug=slug,
        field_name=field_name,
        display_order=display_order
    )

    db.add(new_requirement)
    db.commit()

    return RedirectResponse(url="/positions", status_code=302)

@router.post("/tip-requirements/{slug}/update")
async def update_tip_requirement(
    slug: str,
    request: Request,
    name: str = Form(...),
    field_name: str = Form(...),
    display_order: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requirement = db.query(TipEntryRequirement).filter(TipEntryRequirement.slug == slug).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Tip requirement not found")

    if requirement.name != name:
        requirement.name = name
        requirement.slug = ensure_unique_slug(db, TipEntryRequirement, create_slug(name), exclude_id=requirement.id)

    requirement.field_name = field_name
    requirement.display_order = display_order

    db.commit()

    return RedirectResponse(url="/positions", status_code=302)

@router.post("/tip-requirements/{slug}/delete")
async def delete_tip_requirement(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requirement = db.query(TipEntryRequirement).filter(TipEntryRequirement.slug == slug).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Tip requirement not found")

    db.delete(requirement)
    db.commit()
    return RedirectResponse(url="/positions", status_code=302)
