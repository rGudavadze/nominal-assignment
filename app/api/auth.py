from fastapi import Request, HTTPException, Depends, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse

from intuitlib.enums import Scopes

from services.auth import AuthService
from utils.helpers import get_auth_service

router = APIRouter(prefix='', tags=['Accounts'])


@router.get("/login")
async def login(
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)):
    """Initiate OAuth login flow"""
    scopes = [Scopes.ACCOUNTING]
    auth_url = auth_service.auth_client.get_authorization_url(scopes)
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
):
    """Handle OAuth callback"""
    auth_client = auth_service.auth_client
    code = request.query_params.get("code")
    realm_id = request.query_params.get("realmId")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed or denied")

    auth_client.get_bearer_token(code, realm_id=realm_id)

    auth_service.save_token(
        access_token=auth_client.access_token,
        refresh_token=auth_client.refresh_token,
        realm_id=realm_id,
        expires_in=3600
    )

    return JSONResponse({
        "message": "Authentication successful",
        "realm_id": realm_id,
        "access_token": auth_client.access_token
    })
