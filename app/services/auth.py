from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session
import requests

from intuitlib.client import AuthClient

from models.auth import Token
from config.settings import settings
from schemas.auth import TokenCreateSchema


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self._auth_client = None

    @property
    def auth_client(self) -> AuthClient:
        """Create and return an AuthClient instance"""
        if self._auth_client:
            return self._auth_client

        client = AuthClient(
            settings.CLIENT_ID,
            settings.CLIENT_SECRET,
            settings.REDIRECT_URI,
            settings.ENVIRONMENT,
            settings.STATE,
        )
        return client

    def save_token(self, access_token: str, refresh_token: str, realm_id: str, expires_in: int) -> Token:
        """Save or update token in the database"""
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token_data = TokenCreateSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            realm_id=realm_id,
            expires_at=expires_at,
            expires_in=expires_in
        )
        
        token = self.db.query(Token).first()
        if token:
            token.access_token = token_data.access_token
            token.refresh_token = token_data.refresh_token
            token.realm_id = token_data.realm_id
            token.expires_at = token_data.expires_at
        else:
            token = Token(
                access_token=token_data.access_token,
                refresh_token=token_data.refresh_token,
                realm_id=token_data.realm_id,
                expires_at=token_data.expires_at
            )
            self.db.add(token)
        
        self.db.commit()
        return token
    
    def get_valid_token(self) -> Token:
        """Get a valid token, refreshing if necessary"""
        token = self.db.query(Token).first()
        if not token:
            raise ValueError("No token found. Please authenticate first.")
        
        if datetime.utcnow() >= token.expires_at - timedelta(minutes=5):
            return self.refresh_token(token)
        
        return token

    def refresh_token(self, token: Token) -> Token:
        """Refresh the access token using the refresh token"""
        response = requests.post(
            settings.TOKEN_URL,
            data={
                'grant_type': 'refresh_token',
                'refresh_token': token.refresh_token,
                'client_id': settings.CLIENT_ID,
                'client_secret': settings.CLIENT_SECRET
            }
        )

        if response.status_code != 200:
            raise HTTPException(400, f"Failed to refresh token: {response.text}")

        data = response.json()
        return self.save_token(
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
            realm_id=token.realm_id,
            expires_in=data['expires_in']
        )
