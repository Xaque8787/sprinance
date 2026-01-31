from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import User, CheckPayee, EFTCardNumber, EFTPayee, DailyBalanceCheck, DailyBalanceEFT, ScheduledCheck, ScheduledEFT
from app.auth.jwt_handler import get_current_user, get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class CheckPayeeCreate(BaseModel):
    name: str

class EFTCardNumberCreate(BaseModel):
    number: str

class EFTPayeeCreate(BaseModel):
    name: str

class ScheduledCheckCreate(BaseModel):
    check_number: str = None
    payable_to: str
    default_total: float = 0.0
    days_of_week: List[str] = []
    memo: str = None
    is_active: bool = True

class ScheduledEFTCreate(BaseModel):
    card_number: str = None
    payable_to: str
    default_total: float = 0.0
    days_of_week: List[str] = []
    memo: str = None
    is_active: bool = True

@router.get("/api/checks-efts/check-payees")
async def get_check_payees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payees = db.query(CheckPayee).order_by(CheckPayee.name).all()
    return [{"id": p.id, "name": p.name} for p in payees]

@router.post("/api/checks-efts/check-payees")
async def create_check_payee(
    payee: CheckPayeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    name = payee.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Payee name cannot be empty")

    existing = db.query(CheckPayee).filter(CheckPayee.name == name).first()
    if existing:
        return {"id": existing.id, "name": existing.name}

    new_payee = CheckPayee(name=name)
    db.add(new_payee)
    db.commit()
    db.refresh(new_payee)

    return {"id": new_payee.id, "name": new_payee.name}

@router.put("/api/checks-efts/check-payees/{payee_id}")
async def update_check_payee(
    payee_id: int,
    payee: CheckPayeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing = db.query(CheckPayee).filter(CheckPayee.id == payee_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Payee not found")

    name = payee.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Payee name cannot be empty")

    name_exists = db.query(CheckPayee).filter(
        CheckPayee.name == name,
        CheckPayee.id != payee_id
    ).first()
    if name_exists:
        raise HTTPException(status_code=400, detail="Payee name already exists")

    existing.name = name
    db.commit()
    db.refresh(existing)

    return {"id": existing.id, "name": existing.name}

@router.delete("/api/checks-efts/check-payees/{payee_id}")
async def delete_check_payee(
    payee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payee = db.query(CheckPayee).filter(CheckPayee.id == payee_id).first()
    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    db.delete(payee)
    db.commit()

    return {"success": True}

@router.get("/api/checks-efts/eft-card-numbers")
async def get_eft_card_numbers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    cards = db.query(EFTCardNumber).order_by(EFTCardNumber.number).all()
    return [{"id": c.id, "number": c.number} for c in cards]

@router.post("/api/checks-efts/eft-card-numbers")
async def create_eft_card_number(
    card: EFTCardNumberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    number = card.number.strip()
    if not number:
        raise HTTPException(status_code=400, detail="Card number cannot be empty")

    existing = db.query(EFTCardNumber).filter(EFTCardNumber.number == number).first()
    if existing:
        return {"id": existing.id, "number": existing.number}

    new_card = EFTCardNumber(number=number)
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return {"id": new_card.id, "number": new_card.number}

@router.put("/api/checks-efts/eft-card-numbers/{card_id}")
async def update_eft_card_number(
    card_id: int,
    card: EFTCardNumberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing = db.query(EFTCardNumber).filter(EFTCardNumber.id == card_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Card number not found")

    number = card.number.strip()
    if not number:
        raise HTTPException(status_code=400, detail="Card number cannot be empty")

    number_exists = db.query(EFTCardNumber).filter(
        EFTCardNumber.number == number,
        EFTCardNumber.id != card_id
    ).first()
    if number_exists:
        raise HTTPException(status_code=400, detail="Card number already exists")

    existing.number = number
    db.commit()
    db.refresh(existing)

    return {"id": existing.id, "number": existing.number}

@router.delete("/api/checks-efts/eft-card-numbers/{card_id}")
async def delete_eft_card_number(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    card = db.query(EFTCardNumber).filter(EFTCardNumber.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card number not found")

    db.delete(card)
    db.commit()

    return {"success": True}

@router.get("/api/checks-efts/eft-payees")
async def get_eft_payees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payees = db.query(EFTPayee).order_by(EFTPayee.name).all()
    return [{"id": p.id, "name": p.name} for p in payees]

@router.post("/api/checks-efts/eft-payees")
async def create_eft_payee(
    payee: EFTPayeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    name = payee.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Payee name cannot be empty")

    existing = db.query(EFTPayee).filter(EFTPayee.name == name).first()
    if existing:
        return {"id": existing.id, "name": existing.name}

    new_payee = EFTPayee(name=name)
    db.add(new_payee)
    db.commit()
    db.refresh(new_payee)

    return {"id": new_payee.id, "name": new_payee.name}

@router.put("/api/checks-efts/eft-payees/{payee_id}")
async def update_eft_payee(
    payee_id: int,
    payee: EFTPayeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing = db.query(EFTPayee).filter(EFTPayee.id == payee_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Payee not found")

    name = payee.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Payee name cannot be empty")

    name_exists = db.query(EFTPayee).filter(
        EFTPayee.name == name,
        EFTPayee.id != payee_id
    ).first()
    if name_exists:
        raise HTTPException(status_code=400, detail="Payee name already exists")

    existing.name = name
    db.commit()
    db.refresh(existing)

    return {"id": existing.id, "name": existing.name}

@router.delete("/api/checks-efts/eft-payees/{payee_id}")
async def delete_eft_payee(
    payee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payee = db.query(EFTPayee).filter(EFTPayee.id == payee_id).first()
    if not payee:
        raise HTTPException(status_code=404, detail="Payee not found")

    db.delete(payee)
    db.commit()

    return {"success": True}

@router.get("/checks-efts/manage", response_class=HTMLResponse)
async def manage_checks_efts_page(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "checks_efts/manage.html",
        {
            "request": request,
            "current_user": user
        }
    )

@router.get("/api/scheduled-checks")
async def get_scheduled_checks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    checks = db.query(ScheduledCheck).order_by(ScheduledCheck.payable_to).all()
    return [{
        "id": c.id,
        "check_number": c.check_number,
        "payable_to": c.payable_to,
        "default_total": c.default_total,
        "days_of_week": c.days_of_week if c.days_of_week else [],
        "memo": c.memo,
        "is_active": c.is_active
    } for c in checks]

@router.post("/api/scheduled-checks")
async def create_scheduled_check(
    check: ScheduledCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payable_to = check.payable_to.strip()
    if not payable_to:
        raise HTTPException(status_code=400, detail="Payable To cannot be empty")

    new_check = ScheduledCheck(
        check_number=check.check_number,
        payable_to=payable_to,
        default_total=check.default_total,
        days_of_week=check.days_of_week,
        memo=check.memo,
        is_active=check.is_active
    )
    db.add(new_check)
    db.commit()
    db.refresh(new_check)

    return {
        "id": new_check.id,
        "check_number": new_check.check_number,
        "payable_to": new_check.payable_to,
        "default_total": new_check.default_total,
        "days_of_week": new_check.days_of_week if new_check.days_of_week else [],
        "memo": new_check.memo,
        "is_active": new_check.is_active
    }

@router.put("/api/scheduled-checks/{check_id}")
async def update_scheduled_check(
    check_id: int,
    check: ScheduledCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing = db.query(ScheduledCheck).filter(ScheduledCheck.id == check_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled check not found")

    payable_to = check.payable_to.strip()
    if not payable_to:
        raise HTTPException(status_code=400, detail="Payable To cannot be empty")

    existing.check_number = check.check_number
    existing.payable_to = payable_to
    existing.default_total = check.default_total
    existing.days_of_week = check.days_of_week
    existing.memo = check.memo
    existing.is_active = check.is_active

    db.commit()
    db.refresh(existing)

    return {
        "id": existing.id,
        "check_number": existing.check_number,
        "payable_to": existing.payable_to,
        "default_total": existing.default_total,
        "days_of_week": existing.days_of_week if existing.days_of_week else [],
        "memo": existing.memo,
        "is_active": existing.is_active
    }

@router.delete("/api/scheduled-checks/{check_id}")
async def delete_scheduled_check(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    check = db.query(ScheduledCheck).filter(ScheduledCheck.id == check_id).first()
    if not check:
        raise HTTPException(status_code=404, detail="Scheduled check not found")

    db.delete(check)
    db.commit()

    return {"success": True}

@router.get("/api/scheduled-efts")
async def get_scheduled_efts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    efts = db.query(ScheduledEFT).order_by(ScheduledEFT.payable_to).all()
    return [{
        "id": e.id,
        "card_number": e.card_number,
        "payable_to": e.payable_to,
        "default_total": e.default_total,
        "days_of_week": e.days_of_week if e.days_of_week else [],
        "memo": e.memo,
        "is_active": e.is_active
    } for e in efts]

@router.post("/api/scheduled-efts")
async def create_scheduled_eft(
    eft: ScheduledEFTCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payable_to = eft.payable_to.strip()
    if not payable_to:
        raise HTTPException(status_code=400, detail="Payable To cannot be empty")

    new_eft = ScheduledEFT(
        card_number=eft.card_number,
        payable_to=payable_to,
        default_total=eft.default_total,
        days_of_week=eft.days_of_week,
        memo=eft.memo,
        is_active=eft.is_active
    )
    db.add(new_eft)
    db.commit()
    db.refresh(new_eft)

    return {
        "id": new_eft.id,
        "card_number": new_eft.card_number,
        "payable_to": new_eft.payable_to,
        "default_total": new_eft.default_total,
        "days_of_week": new_eft.days_of_week if new_eft.days_of_week else [],
        "memo": new_eft.memo,
        "is_active": new_eft.is_active
    }

@router.put("/api/scheduled-efts/{eft_id}")
async def update_scheduled_eft(
    eft_id: int,
    eft: ScheduledEFTCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing = db.query(ScheduledEFT).filter(ScheduledEFT.id == eft_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled EFT not found")

    payable_to = eft.payable_to.strip()
    if not payable_to:
        raise HTTPException(status_code=400, detail="Payable To cannot be empty")

    existing.card_number = eft.card_number
    existing.payable_to = payable_to
    existing.default_total = eft.default_total
    existing.days_of_week = eft.days_of_week
    existing.memo = eft.memo
    existing.is_active = eft.is_active

    db.commit()
    db.refresh(existing)

    return {
        "id": existing.id,
        "card_number": existing.card_number,
        "payable_to": existing.payable_to,
        "default_total": existing.default_total,
        "days_of_week": existing.days_of_week if existing.days_of_week else [],
        "memo": existing.memo,
        "is_active": existing.is_active
    }

@router.delete("/api/scheduled-efts/{eft_id}")
async def delete_scheduled_eft(
    eft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    eft = db.query(ScheduledEFT).filter(ScheduledEFT.id == eft_id).first()
    if not eft:
        raise HTTPException(status_code=404, detail="Scheduled EFT not found")

    db.delete(eft)
    db.commit()

    return {"success": True}

@router.get("/api/scheduled-checks-for-day")
async def get_scheduled_checks_for_day(
    day_of_week: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    checks = db.query(ScheduledCheck).filter(ScheduledCheck.is_active == True).all()
    matching_checks = []

    for check in checks:
        days = check.days_of_week if check.days_of_week else []
        if day_of_week in days:
            matching_checks.append({
                "check_number": check.check_number,
                "payable_to": check.payable_to,
                "total": check.default_total,
                "memo": check.memo
            })

    return matching_checks

@router.get("/api/scheduled-efts-for-day")
async def get_scheduled_efts_for_day(
    day_of_week: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    efts = db.query(ScheduledEFT).filter(ScheduledEFT.is_active == True).all()
    matching_efts = []

    for eft in efts:
        days = eft.days_of_week if eft.days_of_week else []
        if day_of_week in days:
            matching_efts.append({
                "card_number": eft.card_number,
                "payable_to": eft.payable_to,
                "total": eft.default_total,
                "memo": eft.memo
            })

    return matching_efts
