import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SecurityContext } from '@angular/core';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { DomSanitizer } from '@angular/platform-browser';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AIChatComponent } from './ai-chat.component';
import { AIModel, AIService, PrivacyStatus } from '../../services/ai.service';

describe('AIChatComponent', () => {
  let fixture: ComponentFixture<AIChatComponent>;
  let component: AIChatComponent;
  let httpMock: HttpTestingController;
  let aiService: AIService;

  const models: AIModel[] = [
    { id: 'model-a', name: 'Model A', description: 'First model', provider: 'Provider A' },
    { id: 'model-b', name: 'Model B', description: 'Second model', provider: 'Provider A' },
    { id: 'model-c', name: 'Model C', description: 'Third model', provider: 'Provider B' }
  ];

  const privacyStatus: PrivacyStatus = {
    privacy_enabled: true,
    protection_measures: [],
    total_items_protected: 0,
    message: 'Your personal details are protected.'
  };

  const apiBase = 'http://localhost:8000/api/ai';

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AIChatComponent, HttpClientTestingModule]
    }).compileComponents();

    fixture = TestBed.createComponent(AIChatComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    aiService = TestBed.inject(AIService);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function initializePage(): void {
    component.ngOnInit();

    httpMock.expectOne(`${apiBase}/models`).flush({
      models,
      default_model: 'model-a'
    });
    httpMock.expectOne(`${apiBase}/quick-questions`).flush({
      questions: ['How much did I spend this month?', 'What is my top category?']
    });
    httpMock.expectOne(`${apiBase}/privacy-status`).flush(privacyStatus);
  }

  it('loads the AI models, quick questions, and privacy status for the menu page', () => {
    initializePage();

    expect(component.models).toEqual(models);
    expect(component.selectedModel).toBe('model-a');
    expect(component.quickQuestions).toEqual([
      'How much did I spend this month?',
      'What is my top category?'
    ]);
    expect(component.privacyStatus).toEqual(privacyStatus);
    expect(component.chatSessions.length).toBe(1);
    expect(component.activeChatId).toBe(component.chatSessions[0].id);
  });

  it('groups available models by provider and updates the selected model', () => {
    initializePage();

    expect(component.modelGroups.map(group => [group.provider, group.models.length])).toEqual([
      ['Provider A', 2],
      ['Provider B', 1]
    ]);

    component.onModelChange('model-c');
    expect(aiService.getSelectedModel()).toBe('model-c');
  });

  it('filters the model dropdown by the selected provider', () => {
    initializePage();

    expect(component.selectedProvider).toBe('Provider A');
    expect(component.modelsForSelectedProvider.map(model => model.id)).toEqual(['model-a', 'model-b']);

    component.onProviderChange('Provider B');
    expect(component.modelsForSelectedProvider.map(model => model.id)).toEqual(['model-c']);
    expect(aiService.getSelectedModel()).toBe('model-c');

    component.onProviderChange('Provider A');
    expect(aiService.getSelectedModel()).toBe('model-a');

    component.onModelChange('model-b');
    expect(component.selectedProvider).toBe('Provider A');
    expect(aiService.getSelectedModel()).toBe('model-b');
  });

  it('sends a trimmed question and adds the assistant response to the active chat', () => {
    initializePage();
    component.userInput = '  How much did I spend?  ';

    component.sendMessage();

    const request = httpMock.expectOne(`${apiBase}/chat`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      message: 'How much did I spend?',
      model_id: 'model-a',
      history: [{ role: 'user', content: 'How much did I spend?' }]
    });
    expect(component.isLoading).toBeTrue();
    request.flush({
      response: 'You spent ₹2,000.',
      model_used: 'model-a',
      timestamp: '2025-01-10T00:00:00Z'
    });

    expect(component.isLoading).toBeFalse();
    expect(component.userInput).toBe('');
    expect(component.messages.map(message => message.role)).toEqual(['user', 'assistant']);
    expect(component.messages[1].content).toBe('You spent ₹2,000.');
    expect(component.chatSessions[0].title).toBe('How much did I spend?');
  });

  it('keeps the server-generated chart payload with the assistant message', () => {
    initializePage();
    component.userInput = 'Show a chart of monthly expenses';
    component.sendMessage();

    const chart = {
      type: 'line' as const,
      title: 'Expenses by month',
      labels: ['2026-09'],
      datasets: [{ label: 'Expenses', data: [1250] }]
    };

    httpMock.expectOne(`${apiBase}/chat`).flush({
      response: 'Your expenses are shown below.',
      chart,
      model_used: 'model-a',
      timestamp: '2026-10-23T00:00:00Z'
    });

    expect(component.messages[1].chart).toEqual(chart);
    expect(component.messages[1].chartId).toContain('ai-chart-');
  });

  it('does not send blank messages or send while no model is selected', () => {
    initializePage();
    component.userInput = '   ';
    component.sendMessage();
    httpMock.expectNone(`${apiBase}/chat`);

    component.selectedModel = null;
    component.userInput = 'Question';
    component.sendMessage();
    httpMock.expectNone(`${apiBase}/chat`);
    expect(component.userInput).toBe('Question');
  });

  it('surfaces chat API errors and always clears the loading state', () => {
    initializePage();
    component.userInput = 'Question';
    const snackBar = fixture.debugElement.injector.get(MatSnackBar);
    spyOn(snackBar, 'open');

    component.sendMessage();
    httpMock.expectOne(`${apiBase}/chat`).flush(
      { detail: 'The model is unavailable.' },
      { status: 503, statusText: 'Unavailable' }
    );

    expect(component.isLoading).toBeFalse();
    expect(snackBar.open).toHaveBeenCalledWith(
      'The model is unavailable.',
      'Close',
      { duration: 5000 }
    );
  });

  it('creates, switches between, and deletes chats while keeping the active chat valid', () => {
    initializePage();
    const firstChatId = component.activeChatId!;

    component.createNewChat();
    const secondChatId = component.activeChatId!;
    expect(secondChatId).not.toBe(firstChatId);
    expect(component.chatSessions.length).toBe(2);

    component.switchToChat(firstChatId);
    expect(component.activeChatId).toBe(firstChatId);

    const clickEvent = new MouseEvent('click');
    const stopPropagation = spyOn(clickEvent, 'stopPropagation').and.callThrough();
    component.deleteChat(firstChatId, clickEvent);

    expect(stopPropagation).toHaveBeenCalled();
    expect(component.chatSessions.map(chat => chat.id)).toEqual([secondChatId]);
    expect(component.activeChatId).toBe(secondChatId);
  });

  it('requires confirmation before clearing every chat', () => {
    initializePage();
    const confirm = spyOn(window, 'confirm').and.returnValue(false);

    component.clearAllChats();
    expect(component.chatSessions.length).toBe(1);

    confirm.and.returnValue(true);
    component.clearAllChats();
    expect(component.chatSessions).toEqual([]);
    expect(component.activeChatId).toBeNull();
    expect(component.messages).toEqual([]);
  });

  it('toggles the chat sidebar and renders markdown safely', () => {
    initializePage();

    expect(component.sidebarCollapsed).toBeFalse();
    component.toggleSidebar();
    expect(component.sidebarCollapsed).toBeTrue();
    component.toggleSidebar();
    expect(component.sidebarCollapsed).toBeFalse();

    const sanitizer = TestBed.inject(DomSanitizer);
    const html = sanitizer.sanitize(SecurityContext.HTML, component.renderMarkdown('**Budget**'));
    expect(html).toContain('<strong>Budget</strong>');
  });
});
