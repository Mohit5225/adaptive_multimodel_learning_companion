/**
 * Client-side authenticated API call helper
 * Uses a token getter function set by the AuthProvider (Clerk useAuth hook)
 */

// ═══════════════════════════════════════════════════════════════════════════
// TOKEN MANAGEMENT — Set by React component using useAuth()
// ═══════════════════════════════════════════════════════════════════════════
let _getToken: (() => Promise<string | null>) | null = null;

/** Call this from your top-level component to inject the Clerk getToken function */
export function setAuthTokenGetter(fn: () => Promise<string | null>) {
  _getToken = fn;
}

export async function apiCall(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  let token: string | null = null;

  // Try injected getter first (from useAuth hook), fallback to window.Clerk
  if (_getToken) {
    token = await _getToken();
  } else {
    token = await (window as any).Clerk?.session?.getToken?.() ?? null;
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  } else {
    console.warn('[API] No auth token available — request may fail with 401');
  }

  const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`;
  
  console.log(`[API] 📤 Request: ${options.method || 'GET'} ${endpoint}`);
  console.log(`[API]   Token: ${token ? '✅ Present' : '❌ Missing'}`);
  if (options.body) {
    console.log(`[API]   Body: ${typeof options.body === 'string' ? options.body.substring(0, 100) : 'binary'}`);
  }

  const startTime = performance.now();
  const response = await fetch(url, {
    ...options,
    headers,
  });
  const duration = (performance.now() - startTime).toFixed(2);

  console.log(`[API] 📥 Response: ${response.status} ${response.statusText} (${duration}ms)`);
  
  return response;
}


// ═══════════════════════════════════════════════════════════════════════════
// CHAT API FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/** Types matching backend models */
export interface ChatMessage {
  id: string;
  chat_id: string;
  user_id: string;
  user_message: string;
  classification: {
    category: 'need_video_visualisation' | 'need_text_response';
    reason: string;
    confidence: number;
  };
  routed_to: 'text_response' | 'video_generation';
  system_response: string | null;
  video_url: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Chat {
  id: string;
  user_id: string;
  title: string;
  total_messages: number;
  total_videos_generated: number;
  total_text_responses: number;
  created_at: string;
  updated_at: string | null;
  archived: boolean;
}

export interface SendMessageResponse {
  message: ChatMessage;
  chat_id: string;
  is_new_chat: boolean;
  status: 'completed' | 'video_generating';
  project_id?: string;
}

export interface VideoStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  video_url: string | null;
  error: string | null;
}

export interface ModeInfo {
  key: string;
  label: string;
  description: string;
  icon: string;
}

/** Send a message to the chatbot */
export async function sendChatMessage(
  message: string,
  chatId?: string,
  mode?: string
): Promise<SendMessageResponse> {
  const res = await apiCall('/api/chat/send', {
    method: 'POST',
    body: JSON.stringify({
      message,
      chat_id: chatId || null,
      mode: mode || null,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to send message' }));
    throw new Error(err.detail || 'Failed to send message');
  }

  return res.json();
}

/** Create a new chat session */
export async function createChat(title?: string): Promise<Chat> {
  const res = await apiCall('/api/chat/create', {
    method: 'POST',
    body: JSON.stringify({ title: title || null }),
  });

  if (!res.ok) throw new Error('Failed to create chat');
  return res.json();
}

/** Get all chats for current user */
export async function listChats(): Promise<Chat[]> {
  const res = await apiCall('/api/chat/list');
  if (!res.ok) throw new Error('Failed to fetch chats');
  return res.json();
}

/** Get messages for a specific chat */
export async function getChatMessages(
  chatId: string,
  limit: number = 50
): Promise<ChatMessage[]> {
  const res = await apiCall(`/api/chat/${chatId}/messages?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch messages');
  return res.json();
}

/** Poll for video generation status */
export async function getVideoStatus(projectId: string): Promise<VideoStatusResponse> {
  const res = await apiCall(`/api/chat/video-status/${projectId}`);
  if (!res.ok) throw new Error('Failed to fetch video status');
  return res.json();
}

/** Get a single message (poll for video URL update) */
export async function getMessage(messageId: string): Promise<ChatMessage> {
  const res = await apiCall(`/api/chat/message/${messageId}`);
  if (!res.ok) throw new Error('Failed to fetch message');
  return res.json();
}

/** Archive (delete) a chat */
export async function archiveChat(chatId: string): Promise<void> {
  const res = await apiCall(`/api/chat/${chatId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete chat');
}

/** Update chat title */
export async function updateChatTitle(chatId: string, title: string): Promise<void> {
  const res = await apiCall(`/api/chat/${chatId}/title`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to update title');
}

/** Get available teaching modes */
export async function getModes(): Promise<ModeInfo[]> {
  const res = await apiCall('/api/chat/modes');
  if (!res.ok) throw new Error('Failed to fetch modes');
  return res.json();
}


// ═══════════════════════════════════════════════════════════════════════════
// PDF RAG API FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

export interface PDFInfo {
  pdf_id: string;
  filename: string;
  chunks: number;
  text_length: number;
  created_at?: string;
}

export interface PDFUploadResponse {
  status: string;
  pdf_id: string;
  filename: string;
  chunks: number;
  text_length: number;
  message: string;
}

export interface PDFListResponse {
  chat_id: string;
  pdfs: PDFInfo[];
  has_pdfs: boolean;
}

/** Upload a PDF file for RAG in a specific chat (multipart/form-data) */
export async function uploadPDF(file: File, chatId: string): Promise<PDFUploadResponse> {
  let token: string | null = null;
  if (_getToken) {
    token = await _getToken();
  } else {
    token = await (window as any).Clerk?.session?.getToken?.() ?? null;
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('chat_id', chatId);

  const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/pdf/upload`;

  console.log(`[API] 📤 Uploading PDF: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,  // No Content-Type — browser sets multipart boundary
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to upload PDF' }));
    throw new Error(err.detail || 'Failed to upload PDF');
  }

  console.log(`[API] ✅ PDF uploaded successfully`);
  return res.json();
}

/** List PDFs uploaded to a specific chat */
export async function listChatPDFs(chatId: string): Promise<PDFListResponse> {
  const res = await apiCall(`/api/pdf/list/${chatId}`);
  if (!res.ok) throw new Error('Failed to list PDFs');
  return res.json();
}

/** Delete a PDF from a chat */
export async function deletePDF(pdfId: string): Promise<void> {
  const res = await apiCall(`/api/pdf/${pdfId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete PDF');
}

