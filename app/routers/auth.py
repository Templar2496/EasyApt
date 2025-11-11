from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from argon2 import PasswordHasher

from app.db import SessionLocal
from app.models.user import User
from app.core.audit import write_audit

router = APIRouter()
ph = PasswordHasher()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return request.app.state.templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=email).first():
        write_audit(db, "auth.register.fail.exists", request, actor=email, details={"reason":"exists"})
        db.commit()
        return RedirectResponse("/auth/register?err=exists", status_code=303)
    u = User(email=email, pw_hash=ph.hash(password))
    db.add(u)
    write_audit(db, "auth.register.success", request, actor=email)
    db.commit()
    return RedirectResponse("/auth/login?ok=registered", status_code=303)

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return request.app.state.templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=email).first()
    if not u:
        write_audit(db, "auth.login.fail", request, actor=email, details={"reason":"no_user"})
        db.commit()
        return RedirectResponse("/auth/login?err=invalid", status_code=303)
    try:
        ph.verify(u.pw_hash, password)
    except Exception:
        write_audit(db, "auth.login.fail", request, actor=email, details={"reason":"bad_password"})
        db.commit()
        return RedirectResponse("/auth/login?err=invalid", status_code=303)
    write_audit(db, "auth.login.success", request, actor=email)
    db.commit()
    return RedirectResponse("/portal", status_code=303)
