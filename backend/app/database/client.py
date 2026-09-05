from supabase import create_client, Client, ClientOptions
from app.config import settings

# Service-role client — server-side only, bypasses RLS for AI-written data
# NEVER expose this client or its key to the frontend
_service_client: Client | None = None

# Anon client — for unauthenticated operations (e.g. auth verification)
_anon_client: Client | None = None


def get_service_client() -> Client:
    global _service_client
    if _service_client is None:
        _service_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _service_client


def get_anon_client() -> Client:
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
    return _anon_client


def get_user_client(token: str) -> Client:
    """
    Create a Supabase client scoped to the authenticated user's JWT.
    Attaches Authorization: Bearer <user_jwt> so Postgres RLS policies
    (such as user_id = auth.uid()) evaluate correctly with role 'authenticated'.
    """
    options = ClientOptions(headers={"Authorization": f"Bearer {token}"})
    client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=options,
    )
    client.postgrest.auth(token)
    return client
