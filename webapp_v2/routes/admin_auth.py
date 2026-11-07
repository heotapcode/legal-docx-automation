"""API đăng nhập quản trị (Mục 10.1). Tạo tài khoản bằng dòng lệnh: python -m tools.admin_user create <tên>."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

import config
from services import auth

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginRequest(BaseModel):
    username: str
    password: str


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response):
    auth.require_csrf(request)
    try:
        user = auth.authenticate(body.username, body.password, _client_ip(request))
    except auth.LoginLocked:
        raise HTTPException(status_code=429,
                            detail=f"Sai mật khẩu quá nhiều lần. Vui lòng thử lại sau {auth.LOCK_MINUTES} phút.")
    if not user:
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
    token = auth.create_session(user["id"], _client_ip(request))
    response.set_cookie(auth.COOKIE_NAME, token, max_age=config.ADMIN_SESSION_HOURS * 3600, httponly=True,
                        samesite="strict", secure=config.ADMIN_COOKIE_SECURE, path="/")
    return {"username": user["username"], "role": user["role"]}


@router.post("/logout")
def logout(request: Request, response: Response, user: dict = Depends(auth.require_admin)):
    auth.delete_session(request.cookies.get(auth.COOKIE_NAME))
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(auth.require_admin)):
    return {"username": user["username"], "role": user["role"]}
