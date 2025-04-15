from fastapi import Request, HTTPException, Depends, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse

from intuitlib.enums import Scopes

from app.services.auth import AuthService
from app.schemas.auth import Token
from app.utils.helpers import get_token_service

router = APIRouter(prefix='/auth', tags=['Accounts'])


@router.get("/login")
async def login():
    """Initiate OAuth login flow"""
    token_service = get_token_service()
    scopes = [Scopes.ACCOUNTING]
    auth_url = token_service.auth_client.get_authorization_url(scopes)
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(
        request: Request,
        token_service: AuthService = Depends(get_token_service)
):
    """Handle OAuth callback"""
    auth_client = token_service.auth_client
    code = request.query_params.get("code")
    realm_id = request.query_params.get("realmId")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed or denied")

    try:
        auth_client.get_bearer_token(code, realm_id=realm_id)

        # Save token using our service
        token = token_service.save_token(
            access_token=auth_client.access_token,
            refresh_token=auth_client.refresh_token,
            realm_id=realm_id,
            expires_in=auth_client.token_expires_in
        )

        return JSONResponse({
            "message": "Authentication successful",
            "realm_id": realm_id,
            "token": Token.model_validate(token).model_dump()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
