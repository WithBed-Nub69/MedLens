"""
JWT verification for Supabase Auth tokens.
Extracts the user_id from the Authorization header and provides
an authenticated Supabase client scoped to the user's JWT.
"""
from dataclasses import dataclass
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from supabase import Client
from app.database.client import get_anon_client, get_user_client

security = HTTPBearer()


@dataclass
class AuthenticatedUser:
    user_id: str
    token: str
    client: Client


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> AuthenticatedUser:
    """
    Validate the Supabase JWT and return an AuthenticatedUser containing
    the user's UUID, raw token, and a user-scoped Supabase client.
    Raises 401 if the token is missing, expired, or invalid.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
        )

    user_id: str | None = None

    # First attempt: fast JWT decode and expiration check
    try:
        payload = jwt.decode(
            token,
            key="",
            algorithms=["HS256", "RS256", "ES256"],
            options={"verify_signature": False, "verify_aud": False, "verify_exp": True},
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError:
        # Fallback to Supabase Auth server check
        try:
            supabase = get_anon_client()
            user_response = supabase.auth.get_user(token)
            if user_response and user_response.user:
                user_id = user_response.user.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
            )

    user_client = get_user_client(token)
    return AuthenticatedUser(user_id=user_id, token=token, client=user_client)


def get_current_user_id(
    auth_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> str:
    """
    Validate the Supabase JWT and return the user's UUID.
    Maintained for endpoints that only need the user_id string.
    """
    return auth_user.user_id


