# PDF Upload & RAG Pipeline Flow

## Overview
When a user uploads a PDF through the PDF viewer, it now **automatically triggers the upload, extraction, and full RAG pipeline** without requiring a pre-existing chat.

## Complete Flow Diagram

```
User Uploads PDF
    ↓
✓ PDF displayed locally in viewer (instant feedback)
    ↓
Check: Is there an active chat?
    ├─ YES → Upload PDF to backend immediately
    └─ NO → Create new chat → Upload PDF to backend
    ↓
Backend Processing:
    ├─ Extract text (PyMuPDF)
    ├─ Chunk text (512 chars, 64 overlap)
    ├─ Generate Jina embeddings (dense vectors)
    ├─ Generate sparse BM25 vectors
    └─ Ingest into Qdrant with metadata
    ↓
Frontend Updates:
    ├─ Show "Indexing for AI context..." status
    ├─ Load indexed PDFs list
    └─ Set active chat to new PDF's chat
    ↓
Ready for RAG queries!
```

## Changes Made

### 1. Frontend: PDFSidebar.tsx
**Key Change**: Auto-create chat if none exists
- Added `createChat` import from API
- Added `onChatCreated` callback prop
- Enhanced `handleFileUpload` and `uploadToBackend` with:
  - Better error handling with logging
  - Auto-chat creation when no active chat exists
  - Callback to parent (`onChatCreated`) when new chat is created

**Before**: PDF upload only worked if a chat already existed  
**After**: Chat is automatically created for PDF upload if needed

### 2. Frontend: ChatLayout.tsx
**Key Change**: Pass chat creation callback to PDF sidebar
- Added `onChatCreated` callback prop
- Passes it to `<PDFSidebar>` component

### 3. Frontend: chats/page.tsx (main chat page)
**Key Change**: Handle new chats created by PDF uploads
- Added `handleChatCreatedFromPDF` function:
  ```typescript
  const handleChatCreatedFromPDF = (chatId: string) => {
    console.log(`[Chat] New chat created from PDF upload: ${chatId}`);
    setActiveChatId(chatId);
    loadChat(chatId);
    setSidebarRefresh((prev) => prev + 1);
  };
  ```
- Passes this to `ChatLayout` as `onChatCreated` prop

### 4. Backend: Already Complete
✅ PDF extraction (`Services/pdf_service.py`) - Working  
✅ Qdrant RAG service (`database/qdrant.py`) - Fully implemented  
✅ PDF router endpoints (`controller/pdf_router.py`) - Complete  

## User Experience

### Before This Fix
1. User opens PDF sidebar
2. User uploads PDF
3. PDF displays in viewer... then nothing happens
4. User has to manually create a chat before PDF gets indexed

### After This Fix
1. User opens PDF sidebar and uploads PDF
2. PDF displays **instantly** in viewer
3. If no chat exists → **Auto-creates a new chat**
4. Shows "Indexing for AI context..." loading state
5. Once indexed → **Indexed PDFs list appears** showing chunks
6. User can immediately ask questions with RAG context

## Visual Feedback

### Upload Status States
- **Uploading**: Shows cyan text "Indexing for AI context..." with spinner
- **Success**: PDF appears in "Indexed for AI" list with chunk count
- **Error**: Red error message explaining what went wrong
- **File List**: Shows all indexed PDFs with delete option

## Testing the Flow

### Test Case 1: Upload without active chat
1. Start chat application
2. Click "View PDF" button to open sidebar
3. Click "Upload PDF" and select a PDF
4. **Expected**: 
   - PDF loads in viewer instantly
   - "Indexing..." message appears
   - New chat auto-created
   - Sidebar shows new chat
   - PDF appears in "Indexed for AI" list

### Test Case 2: Upload with active chat
1. Create a chat first
2. Open PDF sidebar
3. Upload PDF
4. **Expected**: Same as above, but uses existing chat

### Test Case 3: RAG Query
1. After PDF is indexed
2. Send a message asking something about PDF content
3. **Expected**:
   - Classifier routes to TEXT_RESPONSE
   - Gemini searches PDFs for context
   - Response is grounded in PDF content

## Backend Pipeline Details

### Document Ingestion (QdrantRAGService.ingest_document)
1. **Text Chunking**: Splits into 512-char chunks with 64-char overlap
2. **Dense Vectors**: Jina Embeddings API (768 dimensions)
3. **Sparse Vectors**: BM25-style tokens (TF-IDF approximation)
4. **Metadata**: Stores filename, pdf_id, chat_id, user_id with each chunk
5. **Batch Upload**: Uploads to Qdrant in batches of 100

### Context Retrieval (Hybrid Search)
- **Query**: User question
- **Dense Search**: Semantic similarity search
- **Sparse Search**: Keyword/BM25 matching
- **Fusion**: Reciprocal Rank Fusion combines results
- **Filtering**: Only returns PDFs from current chat
- **Result**: Top-5 most relevant chunks with scores

## Error Handling

### Common Errors
- **"No PDF file selected"** → Only PDFs are accepted
- **"Failed to extract text"** → PDF might be scanned/image-only
- **"PDF appears to be empty"** → PDF has less than 50 extractable chars
- **"Failed to upload PDF"** → Network or server issue
- **"Failed to create chat"** → Database connectivity issue

### Logging
Both frontend and backend log detailed information:
- Frontend logs to browser console (`[PDF]` prefix)
- Backend logs to server stdout with emoji indicators

## Configuration

### File: `.env` (backend)
Required variables:
- `QDRANT_URL` - Qdrant Cloud URL
- `QDRANT_KEY` - Qdrant API key
- `JINA_API_KEY` - Jina embeddings API key
- `MONGO_URL` - MongoDB connection string

### Chunk Parameters (src/database/qdrant.py)
```python
CHUNK_SIZE = 512          # Characters per chunk
CHUNK_OVERLAP = 64        # Overlap between chunks
DENSE_VECTOR_SIZE = 768   # Jina embeddings dimensions
```

## Future Enhancements

1. **Multiple PDF Support**: Upload multiple PDFs to one chat
2. **PDF Highlighting**: Highlight source text from PDFs in responses
3. **Scanned PDFs**: Add OCR support for image-based PDFs
4. **Chunk Preview**: Show chunk content on hover in indexed list
5. **Search**: Search within indexed PDFs
6. **PDF Annotations**: Let users add notes to PDFs

---

**Status**: ✅ Complete and Ready for Testing
