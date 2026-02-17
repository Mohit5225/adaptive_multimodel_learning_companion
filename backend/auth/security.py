import os
import logging
from fastapi import Request, HTTPException
from dotenv import load_dotenv
from clerk_backend_api import Clerk, AuthenticateRequestOptions
from auth.clerk_adaptor import clerk_user_to_session_dict

load_dotenv()

# Setup Logger
logger = logging.getLogger("auth")
logging.basicConfig(level=logging.INFO)

# 1. Load Keys
secret = os.environ.get("CLERK_SECRET_KEY")
jwt_key = os.environ.get("JWT_KEY") # You MUST have this in .env

if not secret or not jwt_key:
    raise RuntimeError("CLERK_SECRET_KEY and JWT_KEY must be set in .env")

# 2. Initialize SDK
clerk = Clerk(bearer_auth=secret)

# 3. The Dependency
async def get_current_user(request: Request):
    logger.info("🔐 Starting authentication attempt...")

    try:
        # A. Use SDK to Validate Token
        # The SDK uses the JWT_KEY to verify the signature of the header
        options = AuthenticateRequestOptions(jwt_key=jwt_key)
        request_state = clerk.authenticate_request(request, options)

        if not request_state.is_signed_in:
            logger.warning("⚠️ Not signed in.")
            raise HTTPException(status_code=401, detail="Not signed in")

        # B. Get User ID from Token
        if not request_state.payload:
            logger.error("❌ No payload in token.")
            raise HTTPException(status_code=401, detail="Invalid token: No payload.")
        
        user_id = request_state.payload.get("sub")
        if not user_id:
            logger.error("❌ No 'sub' in token.")
            raise HTTPException(status_code=401, detail="Invalid token: User ID missing.")

        logger.info(f"✅ Token validated for clerk_user_id='{user_id}'.")

        # C. The "Heavy" Call - Fetch User Data from Clerk API
        # (This is what you did in your old code)
        clerk_user = clerk.users.get(user_id=user_id)

        # D. Convert to Dict
        session_dict = clerk_user_to_session_dict(clerk_user)
        
        return session_dict

    except Exception as e:
        logger.error(f"❌ Authentication failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")