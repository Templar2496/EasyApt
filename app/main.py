from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import auth, appointments

app = FastAPI(title="Healthcare Scheduler")

@app.middleware("http")
async def add_client_info(request, call_next):
    # nothing to mutate right now; placeholder for future (e.g., request-id)
    response = await call_next(request)
    return response

# Jinja2 templates
templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates  # make available to routers

# Static (optional)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home"})

@app.get("/healthz")
def health():
    return {"ok": True}

@app.get("/portal", response_class=HTMLResponse)
def portal(request: Request):
    return templates.TemplateResponse("portal.html", {"request": request, "title": "Portal"})

# include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
