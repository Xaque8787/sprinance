from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from app.database import init_db, get_db
from app.models import User, Position, TipEntryRequirement
from app.auth.jwt_handler import get_current_user_from_cookie
from app.routes import auth, admin, employees, daily_balance, positions, tip_requirements, reports, financial_items
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
app.include_router(reports.router)
app.include_router(financial_items.router)

def initialize_predefined_data():
    # No longer creating hardcoded positions and tip requirements
    # Users will create these manually via the UI
    pass

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
