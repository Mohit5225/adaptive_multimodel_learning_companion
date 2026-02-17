from typing import Dict, Any
# Note: In version 4.2.0, ensure this import is correct. 
# Sometimes it is straight from clerk_backend_api
from clerk_backend_api.models import User as ClerkUser

def clerk_user_to_session_dict(clerk_user: ClerkUser) -> Dict[str, Any]:
    # Extracting the primary email safely
    primary_email = None
    if clerk_user.email_addresses:
        # We look for the one marked as primary, or just take the first one
        primary_email = clerk_user.email_addresses[0].email_address

    return {
        "sub": clerk_user.id,
        "first_name": clerk_user.first_name,
        "last_name": clerk_user.last_name,
        "primary_email_address": {
            "email_address": primary_email
        },
    }