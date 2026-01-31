import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface AIModel {
  id: string;
  name: string;
  description: string;
  provider: string;
}

export interface ModelsResponse {
  models: AIModel[];
  default_model: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
  model?: string;
}

export interface ChatResponse {
  response: string;
  model_used: string;
  timestamp: string;
}

export interface PrivacyProtection {
  type: string;
  description: string;
  count: number;
  icon: string;
}

export interface PrivacyStatus {
  privacy_enabled: boolean;
  protection_measures: PrivacyProtection[];
  total_items_protected: number;
  message: string;
}

// ========================================
// Chat Session Models
// ========================================

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

@Injectable({
  providedIn: 'root'
})
export class AIService {
  private readonly apiUrl = 'http://localhost:8000/api/ai';
  
  private modelsSubject = new BehaviorSubject<AIModel[]>([]);
  public models$ = this.modelsSubject.asObservable();
  
  private selectedModelSubject = new BehaviorSubject<string | null>(null);
  public selectedModel$ = this.selectedModelSubject.asObservable();

  // ========================================
  // Chat Session Management (In-Memory)
  // ========================================
  private chatSessionsSubject = new BehaviorSubject<ChatSession[]>([]);
  public chatSessions$ = this.chatSessionsSubject.asObservable();

  private activeChatIdSubject = new BehaviorSubject<string | null>(null);
  public activeChatId$ = this.activeChatIdSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadModels();
  }

  // ========================================
  // Chat Session Methods
  // ========================================

  /**
   * Create a new chat session
   */
  createNewChat(): ChatSession {
    const newChat: ChatSession = {
      id: this.generateChatId(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };

    const currentSessions = this.chatSessionsSubject.value;
    this.chatSessionsSubject.next([newChat, ...currentSessions]);
    this.activeChatIdSubject.next(newChat.id);

    return newChat;
  }

  /**
   * Get all chat sessions
   */
  getChatSessions(): ChatSession[] {
    return this.chatSessionsSubject.value;
  }

  /**
   * Get the active chat session
   */
  getActiveChat(): ChatSession | null {
    const activeId = this.activeChatIdSubject.value;
    if (!activeId) return null;
    return this.chatSessionsSubject.value.find(c => c.id === activeId) || null;
  }

  /**
   * Set the active chat by ID
   */
  setActiveChat(chatId: string): void {
    const chat = this.chatSessionsSubject.value.find(c => c.id === chatId);
    if (chat) {
      this.activeChatIdSubject.next(chatId);
    }
  }

  /**
   * Add a message to the active chat
   */
  addMessageToActiveChat(message: ChatMessage): void {
    const activeId = this.activeChatIdSubject.value;
    if (!activeId) return;

    const sessions = this.chatSessionsSubject.value.map(chat => {
      if (chat.id === activeId) {
        const updatedMessages = [...chat.messages, message];
        
        // Update title from first user message if still "New Chat"
        let title = chat.title;
        if (title === 'New Chat' && message.role === 'user') {
          title = message.content.slice(0, 40) + (message.content.length > 40 ? '...' : '');
        }

        return {
          ...chat,
          messages: updatedMessages,
          title,
          updatedAt: new Date()
        };
      }
      return chat;
    });

    this.chatSessionsSubject.next(sessions);
  }

  /**
   * Get messages from the active chat
   */
  getActiveChatMessages(): ChatMessage[] {
    const activeChat = this.getActiveChat();
    return activeChat ? activeChat.messages : [];
  }

  /**
   * Delete a chat session
   */
  deleteChat(chatId: string): void {
    const sessions = this.chatSessionsSubject.value.filter(c => c.id !== chatId);
    this.chatSessionsSubject.next(sessions);

    // If we deleted the active chat, switch to another or clear
    if (this.activeChatIdSubject.value === chatId) {
      if (sessions.length > 0) {
        this.activeChatIdSubject.next(sessions[0].id);
      } else {
        this.activeChatIdSubject.next(null);
      }
    }
  }

  /**
   * Clear all chat sessions (reset)
   */
  clearAllChats(): void {
    this.chatSessionsSubject.next([]);
    this.activeChatIdSubject.next(null);
  }

  /**
   * Generate unique chat ID
   */
  private generateChatId(): string {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // ========================================
  // Model Management Methods
  // ========================================

  loadModels(): void {
    this.getAvailableModels().subscribe({
      next: (response) => {
        this.modelsSubject.next(response.models);
        if (response.default_model) {
          this.selectedModelSubject.next(response.default_model);
        }
      },
      error: (err) => {
        console.error('Failed to load AI models:', err);
      }
    });
  }

  getAvailableModels(): Observable<ModelsResponse> {
    return this.http.get<ModelsResponse>(`${this.apiUrl}/models`);
  }

  setSelectedModel(modelId: string): void {
    this.selectedModelSubject.next(modelId);
  }

  getSelectedModel(): string | null {
    return this.selectedModelSubject.value;
  }

  sendMessage(message: string, history: ChatMessage[] = []): Observable<ChatResponse> {
    const modelId = this.selectedModelSubject.value;
    if (!modelId) {
      throw new Error('No AI model selected');
    }

    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, {
      message,
      model_id: modelId,
      history: history.map(m => ({ role: m.role, content: m.content }))
    });
  }

  getQuickQuestions(): Observable<{ questions: string[] }> {
    return this.http.get<{ questions: string[] }>(`${this.apiUrl}/quick-questions`);
  }

  getPrivacyStatus(): Observable<PrivacyStatus> {
    return this.http.get<PrivacyStatus>(`${this.apiUrl}/privacy-status`);
  }

  getHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }
}
