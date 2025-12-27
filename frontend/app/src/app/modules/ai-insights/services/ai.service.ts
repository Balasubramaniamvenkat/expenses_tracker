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

@Injectable({
  providedIn: 'root'
})
export class AIService {
  private readonly apiUrl = 'http://localhost:8000/api/ai';
  
  private modelsSubject = new BehaviorSubject<AIModel[]>([]);
  public models$ = this.modelsSubject.asObservable();
  
  private selectedModelSubject = new BehaviorSubject<string | null>(null);
  public selectedModel$ = this.selectedModelSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadModels();
  }

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

  getHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }
}
