from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.database import get_db
from app.models import User, Position, TipEntryRequirement, EmployeePositionSchedule
from app.auth.jwt_handler import get_current_admin_user
from app.utils.slugify import create_slug, ensure_unique_slug

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/positions", response_class=HTMLResponse)
async def positions_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    positions = db.query(Position).all()
    tip_requirements = db.query(TipEntryRequirement).order_by(TipEntryRequirement.display_order).all()
    return templates.TemplateResponse(
        "positions/list.html",
        {
            "request": request,
            "positions": positions,
            "tip_requirements": tip_requirements,
            "current_user": current_user
        }
    )

@router.get("/positions/new", response_class=HTMLResponse)
async def new_position_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    tip_requirements = db.query(TipEntryRequirement).order_by(TipEntryRequirement.display_order).all()
    return templates.TemplateResponse(
        "positions/form.html",
        {
            "request": request,
            "position": None,
            "tip_requirements": tip_requirements,
            "current_user": current_user
        }
    )

@router.post("/positions/new")
async def create_position(
    request: Request,
    name: str = Form(...),
    tip_requirement_ids: List[int] = Form([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    slug = ensure_unique_slug(db, Position, create_slug(name))

    new_position = Position(
        name=name,
        slug=slug
    )

    db.add(new_position)
    db.flush()

    for req_id in tip_requirement_ids:
        db.execute(
            text("INSERT INTO position_tip_requirements (position_id, tip_requirement_id) VALUES (:position_id, :req_id)"),
            {"position_id": new_position.id, "req_id": req_id}
        )

    db.commit()

    return RedirectResponse(url="/positions", status_code=302)

@router.get("/positions/{slug}/edit", response_class=HTMLResponse)
async def edit_position_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    position = db.query(Position).filter(Position.slug == slug).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    tip_requirements = db.query(TipEntryRequirement).order_by(TipEntryRequirement.display_order).all()

    return templates.TemplateResponse(
        "positions/form.html",
        {
            "request": request,
            "position": position,
            "tip_requirements": tip_requirements,
            "current_user": current_user
        }
    )

@router.post("/positions/{slug}/edit")
async def update_position(
    slug: str,
    request: Request,
    name: str = Form(...),
    tip_requirement_ids: List[int] = Form([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    position = db.query(Position).filter(Position.slug == slug).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    position.name = name

    db.execute(
        text("DELETE FROM position_tip_requirements WHERE position_id = :position_id"),
        {"position_id": position.id}
    )

    for req_id in tip_requirement_ids:
        db.execute(
            text("INSERT INTO position_tip_requirements (position_id, tip_requirement_id) VALUES (:position_id, :req_id)"),
            {"position_id": position.id, "req_id": req_id}
        )

    db.commit()
    return RedirectResponse(url="/positions", status_code=302)

@router.post("/positions/{slug}/delete")
async def delete_position(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    position = db.query(Position).filter(Position.slug == slug).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    employee_count = db.query(EmployeePositionSchedule).filter(
        EmployeePositionSchedule.position_id == position.id
    ).count()

    if employee_count > 0:
        employee_word = "employee" if employee_count == 1 else "employees"
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete {position.name} - {employee_count} {employee_word} are scheduled for this position"
        )

    db.delete(position)
    db.commit()
    return RedirectResponse(url="/positions", status_code=302)
