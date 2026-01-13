from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models import User, FinancialLineItemTemplate
from app.auth.jwt_handler import get_current_user

router = APIRouter()

class FinancialLineItemTemplateCreate(BaseModel):
    name: str
    category: str
    is_deduction: bool = False
    is_starting_till: bool = False

class FinancialLineItemTemplateUpdate(BaseModel):
    name: str
    is_deduction: bool = False
    is_starting_till: bool = False

@router.get("/api/financial-items/templates")
async def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    templates = db.query(FinancialLineItemTemplate).order_by(
        FinancialLineItemTemplate.category,
        FinancialLineItemTemplate.display_order
    ).all()

    revenue_items = [
        {"id": t.id, "name": t.name, "display_order": t.display_order, "is_default": t.is_default, "is_deduction": t.is_deduction, "is_starting_till": t.is_starting_till}
        for t in templates if t.category == "revenue"
    ]

    expense_items = [
        {"id": t.id, "name": t.name, "display_order": t.display_order, "is_default": t.is_default, "is_deduction": t.is_deduction, "is_starting_till": t.is_starting_till}
        for t in templates if t.category == "expense"
    ]

    return {"revenue": revenue_items, "expense": expense_items}

@router.post("/api/financial-items/templates")
async def create_template(
    template: FinancialLineItemTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    max_order = db.query(FinancialLineItemTemplate).filter(
        FinancialLineItemTemplate.category == template.category
    ).count()

    new_template = FinancialLineItemTemplate(
        name=template.name,
        category=template.category,
        display_order=max_order,
        is_default=False,
        is_deduction=template.is_deduction,
        is_starting_till=template.is_starting_till
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    return {
        "id": new_template.id,
        "name": new_template.name,
        "category": new_template.category,
        "display_order": new_template.display_order,
        "is_default": new_template.is_default,
        "is_deduction": new_template.is_deduction,
        "is_starting_till": new_template.is_starting_till
    }

@router.put("/api/financial-items/templates/{template_id}")
async def update_template(
    template_id: int,
    template: FinancialLineItemTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    db_template = db.query(FinancialLineItemTemplate).filter(
        FinancialLineItemTemplate.id == template_id
    ).first()

    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    db_template.name = template.name
    db_template.is_deduction = template.is_deduction
    db_template.is_starting_till = template.is_starting_till
    db.commit()

    return {"success": True}

@router.delete("/api/financial-items/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    db_template = db.query(FinancialLineItemTemplate).filter(
        FinancialLineItemTemplate.id == template_id
    ).first()

    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    db.delete(db_template)
    db.commit()

    return {"success": True}

@router.post("/api/financial-items/templates/reorder")
async def reorder_templates(
    items: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    for item in items:
        template = db.query(FinancialLineItemTemplate).filter(
            FinancialLineItemTemplate.id == item["id"]
        ).first()
        if template:
            template.display_order = item["display_order"]

    db.commit()
    return {"success": True}
