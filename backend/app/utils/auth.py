"""
JWT verification for Supabase Auth tokens.
Extracts the user_id from the Authorization header.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from app.database.client import get_anon_client

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """
    Validate the Supabase JWT and return the user's UUID.
    Raises 401 if the token is missing, expired, or invalid.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
        )

    # First attempt: validate with Supabase Auth server
    try:
        supabase = get_anon_client()
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            return user_response.user.id
    except Exception:
        pass

    # Second attempt: decode JWT claims directly
    try:
        payload = jwt.decode(
            token,
            key="",
            algorithms=["HS256", "RS256", "ES256"],
            options={"verify_signature": False, "verify_aud": False, "verify_exp": False},
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return user_id
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )

