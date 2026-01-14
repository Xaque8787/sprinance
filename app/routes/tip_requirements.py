from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, TipEntryRequirement
from app.auth.jwt_handler import get_current_user
from app.utils.slugify import create_slug, create_field_name, ensure_unique_slug
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/tip-requirements/new")
async def create_tip_requirement(
    request: Request,
    name: str = Form(...),
    display_order: int = Form(0),
    is_total: Optional[str] = Form(None),
    is_deduction: Optional[str] = Form(None),
    no_input: Optional[str] = Form(None),
    no_null_value: Optional[str] = Form(None),
    apply_to_revenue: Optional[str] = Form(None),
    revenue_type: Optional[str] = Form("addition"),
    apply_to_expense: Optional[str] = Form(None),
    expense_type: Optional[str] = Form("addition"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slug = ensure_unique_slug(db, TipEntryRequirement, create_slug(name))
    field_name = ensure_unique_slug(db, TipEntryRequirement, create_field_name(name), field='field_name')

    new_requirement = TipEntryRequirement(
        name=name,
        slug=slug,
        field_name=field_name,
        display_order=display_order,
        is_total=is_total == "true",
        is_deduction=is_deduction == "true",
        no_input=no_input == "true",
        no_null_value=no_null_value == "true",
        apply_to_revenue=apply_to_revenue == "true",
        revenue_is_deduction=revenue_type == "deduction",
        apply_to_expense=apply_to_expense == "true",
        expense_is_deduction=expense_type == "deduction"
    )

    db.add(new_requirement)
    db.commit()

    return RedirectResponse(url="/positions", status_code=302)

@router.get("/tip-requirements/{slug}/data")
async def get_tip_requirement_data(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requirement = db.query(TipEntryRequirement).filter(TipEntryRequirement.slug == slug).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Tip requirement not found")

    return JSONResponse({
        "name": requirement.name,
        "field_name": requirement.field_name,
        "display_order": requirement.display_order,
        "is_total": requirement.is_total,
        "is_deduction": requirement.is_deduction,
        "no_input": requirement.no_input,
        "no_null_value": requirement.no_null_value,
        "apply_to_revenue": requirement.apply_to_revenue,
        "revenue_is_deduction": requirement.revenue_is_deduction,
        "apply_to_expense": requirement.apply_to_expense,
        "expense_is_deduction": requirement.expense_is_deduction
    })

@router.post("/tip-requirements/{slug}/update")
async def update_tip_requirement(
    slug: str,
    request: Request,
    name: str = Form(...),
    display_order: int = Form(0),
    is_total: Optional[str] = Form(None),
    is_deduction: Optional[str] = Form(None),
    no_input: Optional[str] = Form(None),
    no_null_value: Optional[str] = Form(None),
    apply_to_revenue: Optional[str] = Form(None),
    revenue_type: Optional[str] = Form("addition"),
    apply_to_expense: Optional[str] = Form(None),
    expense_type: Optional[str] = Form("addition"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requirement = db.query(TipEntryRequirement).filter(TipEntryRequirement.slug == slug).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Tip requirement not found")

    if requirement.name != name:
        requirement.name = name
        requirement.slug = ensure_unique_slug(db, TipEntryRequirement, create_slug(name), exclude_id=requirement.id)
        requirement.field_name = ensure_unique_slug(db, TipEntryRequirement, create_field_name(name), field='field_name', exclude_id=requirement.id)

    requirement.display_order = display_order
    requirement.is_total = is_total == "true"
    requirement.is_deduction = is_deduction == "true"
    requirement.no_input = no_input == "true"
    requirement.no_null_value = no_null_value == "true"
    requirement.apply_to_revenue = apply_to_revenue == "true"
    requirement.revenue_is_deduction = revenue_type == "deduction"
    requirement.apply_to_expense = apply_to_expense == "true"
    requirement.expense_is_deduction = expense_type == "deduction"

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
