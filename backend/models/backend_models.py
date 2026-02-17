from pydantic import BaseModel, Field, EmailStr, BeforeValidator
from typing import Optional, Annotated
from datetime import datetime

 
PyObjectId = Annotated[str, BeforeValidator(str)]

class User(BaseModel):
 
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    clerk_id: str = Field(..., description="The ID from Clerk")
    email: EmailStr
    first_name: Optional[str] = None
    role: str = "student"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

 
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


# ═════════════════════════════════════════════════════════════════════════════
# CHATBOT CLASSIFIER MODELS
# ═════════════════════════════════════════════════════════════════════════════

class ClassificationResult(BaseModel):
    """
    Output from the Intelligent Router (Classifier).
    Captures what type of response the user is requesting.
    """
    category: str = Field(
        ..., 
        description="Route category: 'need_video_visualisation' or 'need_text_response'"
    )
    reason: str = Field(
        ...,
        description="Why this classification was chosen (keyword found or default reason)"
    )
    confidence: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1). Defaults to 1.0 for keyword-based classification"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "need_video_visualisation",
                "reason": "Found keyword 'visualize'",
                "confidence": 1.0
            }
        }
    }


class ChatMessage(BaseModel):
    """
    Single message in a chatbot conversation.
    Tracks user input, classification, and system response.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    chat_id: str = Field(..., description="Reference to parent Chat document")
    user_id: str = Field(..., description="Clerk ID of user")
    
    # User's original message
    user_message: str = Field(..., description="The user's input text")
    
    # Classification metadata
    classification: ClassificationResult = Field(
        ...,
        description="Classifier output for this message"
    )
    
    # System response (populated after routing logic)
    system_response: Optional[str] = Field(
        default=None,
        description="Generated response from chatbot (text or video URL reference)"
    )
    
    # Routing decision
    routed_to: str = Field(
        ...,
        description="Where this was routed: 'text_response' or 'video_generation'"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class Chat(BaseModel):
    """
    Conversation thread with user.
    Groups multiple chat messages into a single session.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    user_id: str = Field(..., description="Clerk ID of user")
    
    # Metadata
    title: Optional[str] = Field(
        default=None,
        description="Auto-generated or user-set title for conversation"
    )
    
    # Statistics
    total_messages: int = Field(default=0, description="Total messages in this chat")
    total_videos_generated: int = Field(default=0, description="Count of video generation requests")
    total_text_responses: int = Field(default=0, description="Count of text response requests")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    archived: bool = Field(default=False, description= "Soft delete flag")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }