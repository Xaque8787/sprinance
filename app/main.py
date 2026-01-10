from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from app.database import init_db, get_db
from app.models import User, Position, TipEntryRequirement
from app.auth.jwt_handler import get_current_user_from_cookie
from app.routes import auth, admin, employees, daily_balance, positions, tip_requirements
from app.utils.slugify import create_slug

app = FastAPI(title="Internal Management System")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(employees.router)
app.include_router(daily_balance.router)
app.include_router(positions.router)
app.include_router(tip_requirements.router)

def initialize_predefined_data():
    db = next(get_db())

    predefined_requirements = [
        {"name": "Bank Card Sales", "field_name": "bank_card_sales"},
        {"name": "Bank Card Tips", "field_name": "bank_card_tips"},
        {"name": "Total Sales", "field_name": "total_sales"},
        {"name": "Cash Tips", "field_name": "cash_tips"},
        {"name": "Take-Home Tips", "field_name": "calculated_take_home"},
        {"name": "No Tips", "field_name": "no_tips"}
    ]

    requirements = {}
    for req_data in predefined_requirements:
        existing = db.query(TipEntryRequirement).filter(
            TipEntryRequirement.name == req_data["name"]
        ).first()

        if not existing:
            requirement = TipEntryRequirement(
                name=req_data["name"],
                slug=create_slug(req_data["name"]),
                field_name=req_data["field_name"]
            )
            db.add(requirement)
            db.flush()
            requirements[req_data["name"]] = requirement
        else:
            requirements[req_data["name"]] = existing

    predefined_positions = [
        {
            "name": "Waitstaff",
            "requirements": ["Bank Card Sales", "Bank Card Tips", "Total Sales", "Cash Tips", "Take-Home Tips"]
        },
        {
            "name": "Busser",
            "requirements": ["Cash Tips", "Take-Home Tips"]
        },
        {
            "name": "Host",
            "requirements": ["No Tips"]
        },
        {
            "name": "Cook",
            "requirements": ["No Tips"]
        }
    ]

    for pos_data in predefined_positions:
        existing = db.query(Position).filter(Position.name == pos_data["name"]).first()

        if not existing:
            position = Position(
                name=pos_data["name"],
                slug=create_slug(pos_data["name"])
            )

            position.tip_requirements = [
                requirements[req_name] for req_name in pos_data["requirements"]
            ]

            db.add(position)

    db.commit()

@app.on_event("startup")
def startup_event():
    init_db()
    initialize_predefined_data()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)

    if not user:
        return RedirectResponse(url="/login", status_code=302)

    today = date.today()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_of_week = days_of_week[today.weekday()]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_user": user,
            "current_date": today,
            "day_of_week": day_of_week
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5710)
