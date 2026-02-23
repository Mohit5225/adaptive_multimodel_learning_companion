# 🎓 Adaptive Multimodel Learning Companion

An intelligent, personalized learning platform that combines AI-powered chat, automated video generation, and PDF-based learning to create an adaptive educational experience. The system generates mathematical visualizations using Manim, provides multilingual support (English, Hindi, Marathi, Gujarati, Hinglish), and offers real-time conversational learning.

## ✨ Features

### 🎬 Automated Math Video Generation
- **AI-Powered Manim Code**: Automatically generates Manim Community Edition code for mathematical concepts
- **Text-to-Speech Integration**: Supports both Google Cloud TTS and Cartesia TTS for narration
- **Multilingual Support**: Generate videos in English, Hindi, Marathi, Gujarati, and Hinglish
- **Intelligent Visual Planning**: Creates lesson plans with synchronized narration and visuals
- **3Blue1Brown Style**: Professional mathematical animations similar to 3Blue1Brown videos

### 💬 AI Chat Assistant
- **Personalized Learning**: Adaptive responses based on student level and learning mode
- **Multiple Learning Modes**: 
  - Conceptual understanding
  - Problem-solving practice
  - Visual learning
  - Step-by-step guidance
- **Context-Aware**: Maintains conversation history for coherent interactions
- **RAG-Powered**: Integration with PDF documents for context-specific answers

### 📚 PDF Learning Integration
- **Upload & Analyze**: Upload PDF documents for AI-assisted learning
- **Vector Search**: Semantic search through PDF content using Qdrant
- **Smart Chunking**: Intelligent text extraction and processing
- **Context-Aware Responses**: Get answers based on uploaded course materials

### 🔐 User Management
- **Clerk Authentication**: Secure user authentication and authorization
- **User Profiles**: Personalized learning experiences
- **Project Management**: Track video generation projects and history

## 🏗️ Architecture

```
adaptive_multimodel_learning_companion/
├── backend/                    # FastAPI backend server
│   ├── Services/              # Core business logic
│   │   ├── orchestrator.py    # Video generation orchestrator
│   │   ├── cartesia_orchestrator.py  # Cartesia TTS integration
│   │   ├── gemini_chat_service.py    # AI chat service
│   │   ├── pdf_service.py     # PDF processing service
│   │   └── video_service.py   # Video assembly service
│   ├── auth/                  # Authentication & security
│   ├── controller/            # API route controllers
│   ├── database/              # MongoDB & Qdrant operations
│   ├── models/                # Data models
│   ├── prompts/               # AI prompt templates
│   ├── tts_service/           # Google TTS integration
│   ├── cartesia_tts_service/  # Cartesia TTS integration
│   ├── utils/                 # Utility functions
│   ├── main.py               # CLI entry point
│   └── server.py             # FastAPI server
│
└── frontend/                  # Next.js frontend
    ├── src/
    │   ├── app/              # Next.js app router
    │   ├── components/       # React components
    │   │   ├── chat/        # Chat interface components
    │   │   └── ui/          # Reusable UI components
    │   └── lib/             # Utility libraries
    ├── package.json
    └── tsconfig.json
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **MongoDB** (local or cloud instance)
- **Qdrant** (for vector search)
- **FFmpeg** (for video processing)
- **Manim Community Edition** (installed via pip)

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Install Python dependencies**:
```bash
pip install -r requirement.txt
```

3. **Set up environment variables**:
Create a `.env` file in the `backend` directory:
```env
# Database
MONGODB_URI=your_mongodb_connection_string

# Qdrant Vector DB
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key

# Authentication (Clerk)
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_WEBHOOK_SECRET=your_clerk_webhook_secret

# AI Services
GOOGLE_API_KEY=your_google_api_key

# TTS Services (choose one or both)
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json
CARTESIA_API_KEY=your_cartesia_api_key

# Server
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Run the backend server**:
```bash
# Production mode
python server.py

# Or with uvicorn for development
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
# or
bun install
```

3. **Set up environment variables**:
Create a `.env.local` file in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
```

4. **Run the development server**:
```bash
npm run dev
# or
bun dev
```

5. **Open your browser**:
Navigate to [http://localhost:3000](http://localhost:3000)

## 📖 Usage

### CLI - Generate Math Videos

Generate a mathematical visualization video from the command line:

```bash
cd backend
python main.py "visualize 3+2 addition"
python main.py "explain vector addition"
python main.py "show matrix transformation"
python main.py "demonstrate fractions 1/2 + 1/4"
```

Output: `final_video.mp4` with synchronized narration

### Web Interface

1. **Sign Up/Login**: Create an account using Clerk authentication
2. **Chat Interface**: Ask questions or request explanations
3. **Generate Videos**: Request video generation for mathematical concepts
4. **Upload PDFs**: Upload course materials for AI-assisted learning
5. **Track Projects**: Monitor video generation progress and access completed videos

## 🔌 API Endpoints

### Authentication
- `GET /` - Health check
- `GET /api/users/me` - Get current user profile
- `POST /api/webhooks/clerk` - Clerk webhook handler

### Video Generation
- `POST /api/generate` - Start video generation job
  ```json
  {
    "prompt": "visualize quadratic equations"
  }
  ```
- `GET /api/projects` - Get user's projects
- `GET /api/projects/{project_id}` - Get specific project status

### Chat
- `POST /api/chat` - Send chat message
- `GET /api/chats` - Get user's chat history
- `GET /api/chats/{chat_id}` - Get specific chat
- `DELETE /api/chats/{chat_id}` - Delete chat

### PDF Processing
- `POST /api/chats/{chat_id}/upload-pdf` - Upload PDF to chat
- `GET /api/chats/{chat_id}/pdfs` - List PDFs in chat
- `DELETE /api/chats/{chat_id}/pdfs/{pdf_id}` - Remove PDF

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance web framework
- **MongoDB**: Document database for user data and projects
- **Qdrant**: Vector database for semantic search
- **Google Gemini**: Large language model for AI responses
- **Manim Community Edition**: Mathematical animation engine
- **Google Cloud TTS / Cartesia TTS**: Text-to-speech services
- **FFmpeg**: Video processing
- **Clerk**: Authentication and user management

### Frontend
- **Next.js 16**: React framework with app router
- **React 19**: UI library
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Clerk**: Authentication UI components
- **Framer Motion**: Animation library
- **Vidstack**: Video player component

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Development Notes

### Manim Code Generation
- Uses Manim Community Edition v0.19.1
- Strict syntax compliance with ManimCE (not ManimGL)
- Supports multilingual text rendering
- Anti-overlap protocols for visual elements
- Synchronized with narration timing

### TTS Integration
- **Google TTS**: Traditional cloud-based TTS with SSML support
- **Cartesia TTS**: Modern WebSocket-based TTS for lower latency
- Automatic timestamp extraction for video synchronization

### Video Pipeline
1. Concept analysis and lesson planning
2. Beat generation (narrative segments)
3. Manim code generation
4. Audio narration generation with timestamps
5. Video rendering with Manim
6. Audio-video synchronization
7. Final assembly with FFmpeg

## 🐛 Troubleshooting

### Video Generation Issues
- Ensure FFmpeg is installed and in PATH
- Check Manim installation: `manim --version`
- Verify TTS API credentials are correct
- Check output directory permissions

### Database Connection
- Verify MongoDB connection string
- Ensure Qdrant instance is running
- Check network firewall settings

### Frontend Issues
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check API URL in environment variables

## 📄 License

This project is proprietary software. All rights reserved.

## 👥 Authors

- Mohit5225

## 🙏 Acknowledgments

- Manim Community Edition for mathematical visualization
- 3Blue1Brown for animation inspiration
- Google Gemini for AI capabilities
- Clerk for authentication services
- Cartesia for TTS services
