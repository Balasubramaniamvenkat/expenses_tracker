import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject, takeUntil } from 'rxjs';
import { AIService, AIModel, ChatMessage, PrivacyStatus } from '../../services/ai.service';
import { marked } from 'marked';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Component({
  selector: 'app-ai-chat',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatTooltipModule,
    MatSnackBarModule
  ],
  template: `
    <div class="chat-page">
      <!-- Animated Background -->
      <div class="animated-bg">
        <div class="gradient-orb orb-1"></div>
        <div class="gradient-orb orb-2"></div>
        <div class="gradient-orb orb-3"></div>
      </div>

      <div class="chat-container">
        <!-- Header -->
        <div class="header-section">
          <div class="header-content">
            <div class="header-left">
              <div class="ai-icon-wrapper">
                <mat-icon class="ai-icon">auto_awesome</mat-icon>
                <div class="ai-icon-glow"></div>
              </div>
              <div class="header-text">
                <h1>AI Insights</h1>
                <p>Your intelligent financial assistant</p>
              </div>
            </div>
            
            <!-- Model Selector -->
            <div class="model-selector-wrapper" *ngIf="models.length > 0">
              <mat-form-field appearance="outline" class="model-select">
                <mat-label>
                  <mat-icon>memory</mat-icon>
                  AI Model
                </mat-label>
                <mat-select [(value)]="selectedModel" (selectionChange)="onModelChange($event.value)">
                  <mat-optgroup *ngFor="let group of modelGroups" [label]="group.provider">
                    <mat-option *ngFor="let model of group.models" [value]="model.id">
                      <div class="model-option">
                        <span class="model-name">{{ model.name }}</span>
                        <span class="model-desc">{{ model.description }}</span>
                      </div>
                    </mat-option>
                  </mat-optgroup>
                </mat-select>
              </mat-form-field>
            </div>
            
            <div class="no-models-warning" *ngIf="models.length === 0 && !isLoadingModels">
              <mat-icon>warning_amber</mat-icon>
              <span>No AI models available</span>
            </div>
            
            <mat-spinner diameter="24" *ngIf="isLoadingModels"></mat-spinner>

            <!-- Privacy Shield Indicator -->
            <button class="privacy-shield-btn" 
                    (click)="showPrivacyDetails = !showPrivacyDetails"
                    [matTooltip]="privacyStatus?.message || 'Privacy protection active'">
              <mat-icon class="shield-icon">verified_user</mat-icon>
              <span class="shield-text">PII Protected</span>
            </button>
          </div>

          <!-- Privacy Details Panel -->
          <div class="privacy-details-panel" *ngIf="showPrivacyDetails && privacyStatus">
            <div class="privacy-header">
              <mat-icon>shield</mat-icon>
              <span>Privacy Protection Active</span>
              <button mat-icon-button (click)="showPrivacyDetails = false">
                <mat-icon>close</mat-icon>
              </button>
            </div>
            <p class="privacy-message">{{ privacyStatus.message }}</p>
            <div class="protection-list" *ngIf="privacyStatus && privacyStatus.protection_measures && privacyStatus.protection_measures.length > 0">
              <div class="protection-item" *ngFor="let measure of privacyStatus.protection_measures">
                <mat-icon>{{ measure.icon }}</mat-icon>
                <div class="protection-info">
                  <span class="protection-type">{{ measure.description }}</span>
                  <span class="protection-count" *ngIf="measure.count > 0">{{ measure.count }} items masked</span>
                </div>
              </div>
            </div>
            <div class="protection-total" *ngIf="privacyStatus && privacyStatus.total_items_protected > 0">
              <strong>Total protected:</strong> {{ privacyStatus.total_items_protected }} personal data items
            </div>
          </div>
        </div>

        <!-- Chat Messages Area -->
        <div class="messages-section">
          <div class="messages-container" #messagesContainer>
            <!-- Welcome Message -->
            <div class="welcome-container" *ngIf="messages.length === 0 && !isLoading">
              <div class="welcome-card">
                <div class="welcome-icon-container">
                  <div class="welcome-icon-bg"></div>
                  <mat-icon class="welcome-icon">psychology</mat-icon>
                  <div class="sparkle sparkle-1">✦</div>
                  <div class="sparkle sparkle-2">✦</div>
                  <div class="sparkle sparkle-3">✦</div>
                </div>
                
                <h2>Welcome to AI Insights!</h2>
                <p class="welcome-subtitle">Ask me anything about your financial data. I can help you with:</p>
                
                <div class="feature-grid">
                  <div class="feature-item">
                    <mat-icon>trending_up</mat-icon>
                    <span>Spending Patterns</span>
                  </div>
                  <div class="feature-item">
                    <mat-icon>search</mat-icon>
                    <span>Find Transactions</span>
                  </div>
                  <div class="feature-item">
                    <mat-icon>compare_arrows</mat-icon>
                    <span>Compare Periods</span>
                  </div>
                  <div class="feature-item">
                    <mat-icon>summarize</mat-icon>
                    <span>Financial Summaries</span>
                  </div>
                </div>
              </div>

              <!-- Quick Questions -->
              <div class="quick-questions-section" *ngIf="quickQuestions.length > 0">
                <div class="quick-questions-header">
                  <mat-icon>lightbulb</mat-icon>
                  <span>Try asking:</span>
                </div>
                <div class="quick-questions-grid">
                  <button class="quick-question-chip" 
                          *ngFor="let question of quickQuestions"
                          (click)="askQuestion(question)"
                          [disabled]="isLoading || !selectedModel">
                    <span class="chip-text">{{ question }}</span>
                    <mat-icon class="chip-arrow">arrow_forward</mat-icon>
                  </button>
                </div>
              </div>
            </div>

            <!-- Chat Messages -->
            <div *ngFor="let message of messages; let i = index" 
                 class="message-wrapper"
                 [class.user-wrapper]="message.role === 'user'"
                 [class.assistant-wrapper]="message.role === 'assistant'"
                 [style.animation-delay]="i * 0.1 + 's'">
              <div class="message" 
                   [class.user-message]="message.role === 'user'"
                   [class.assistant-message]="message.role === 'assistant'">
                <div class="message-avatar" [class.user-avatar]="message.role === 'user'" [class.ai-avatar]="message.role === 'assistant'">
                  <mat-icon *ngIf="message.role === 'user'">person</mat-icon>
                  <mat-icon *ngIf="message.role === 'assistant'">auto_awesome</mat-icon>
                </div>
                <div class="message-bubble" [class.user-bubble]="message.role === 'user'" [class.ai-bubble]="message.role === 'assistant'">
                  <div class="message-meta">
                    <span class="sender-name">{{ message.role === 'user' ? 'You' : 'AI Assistant' }}</span>
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                    <span class="model-tag" *ngIf="message.model">{{ message.model }}</span>
                  </div>
                  <div class="message-text" *ngIf="message.role === 'user'">{{ message.content }}</div>
                  <div class="message-text markdown-content" 
                       *ngIf="message.role === 'assistant'"
                       [innerHTML]="renderMarkdown(message.content)"></div>
                </div>
              </div>
            </div>

            <!-- Loading Indicator -->
            <div class="message-wrapper assistant-wrapper" *ngIf="isLoading">
              <div class="message assistant-message">
                <div class="message-avatar ai-avatar">
                  <mat-icon>auto_awesome</mat-icon>
                </div>
                <div class="message-bubble ai-bubble loading-bubble">
                  <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                  </div>
                  <span class="thinking-text">Analyzing your data...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-section">
          <div class="input-container">
            <!-- Quick Questions - Always visible -->
            <div class="quick-questions-inline" *ngIf="quickQuestions.length > 0">
              <button class="quick-btn" 
                      *ngFor="let question of quickQuestions"
                      (click)="askQuestion(question)"
                      [disabled]="isLoading || !selectedModel">
                {{ question }}
              </button>
            </div>
            
            <div class="input-wrapper">
              <mat-icon class="input-icon">chat_bubble_outline</mat-icon>
              <textarea 
                [(ngModel)]="userInput" 
                (keydown.enter)="sendMessage($event)"
                [disabled]="isLoading || !selectedModel"
                placeholder="Ask about your finances..."
                rows="1"
                class="chat-input"
                (input)="autoGrow($event)"></textarea>
              <button class="send-button" 
                      (click)="sendMessage()"
                      [disabled]="!userInput.trim() || isLoading || !selectedModel"
                      [class.active]="userInput.trim() && !isLoading && selectedModel">
                <mat-icon>{{ isLoading ? 'hourglass_empty' : 'send' }}</mat-icon>
              </button>
            </div>
            <div class="input-hint" *ngIf="!selectedModel && models.length > 0">
              <mat-icon>info_outline</mat-icon>
              <span>Select an AI model above to start chatting</span>
            </div>
            <div class="powered-by">
              Powered by <span class="highlight">LangChain</span> • Your data stays private
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    /* ===== Base Layout ===== */
    .chat-page {
      position: relative;
      min-height: calc(100vh - 64px);
      background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 50%, #faf8ff 100%);
      overflow: hidden;
    }

    /* ===== Animated Background ===== */
    .animated-bg {
      position: absolute;
      inset: 0;
      overflow: hidden;
      pointer-events: none;
      z-index: 0;
    }

    .gradient-orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(80px);
      opacity: 0.5;
      animation: float 20s ease-in-out infinite;
    }

    .orb-1 {
      width: 400px;
      height: 400px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      top: -100px;
      right: -100px;
      animation-delay: 0s;
    }

    .orb-2 {
      width: 300px;
      height: 300px;
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      bottom: -50px;
      left: -50px;
      animation-delay: -7s;
    }

    .orb-3 {
      width: 250px;
      height: 250px;
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      animation-delay: -14s;
    }

    @keyframes float {
      0%, 100% { transform: translate(0, 0) scale(1); }
      33% { transform: translate(30px, -30px) scale(1.1); }
      66% { transform: translate(-20px, 20px) scale(0.9); }
    }

    .chat-container {
      position: relative;
      z-index: 1;
      display: flex;
      flex-direction: column;
      height: calc(100vh - 64px);
      max-width: 1100px;
      margin: 0 auto;
      padding: 20px;
    }

    /* ===== Header Section ===== */
    .header-section {
      flex-shrink: 0;
      margin-bottom: 20px;
    }

    .header-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(255, 255, 255, 0.8);
      backdrop-filter: blur(20px);
      border-radius: 20px;
      padding: 20px 28px;
      box-shadow: 0 4px 24px rgba(102, 126, 234, 0.1), 0 1px 2px rgba(0, 0, 0, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .ai-icon-wrapper {
      position: relative;
      width: 56px;
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .ai-icon-glow {
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 16px;
      opacity: 0.2;
      filter: blur(8px);
      animation: pulse-glow 2s ease-in-out infinite;
    }

    @keyframes pulse-glow {
      0%, 100% { transform: scale(1); opacity: 0.2; }
      50% { transform: scale(1.2); opacity: 0.3; }
    }

    .ai-icon {
      position: relative;
      z-index: 1;
      font-size: 32px;
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .header-text h1 {
      margin: 0;
      font-size: 1.75rem;
      font-weight: 700;
      background: linear-gradient(135deg, #1a1a2e 0%, #4a4a6a 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .header-text p {
      margin: 4px 0 0 0;
      color: #6b7280;
      font-size: 0.95rem;
    }

    .model-selector-wrapper {
      flex-shrink: 0;
    }

    .model-select {
      width: 280px;
    }

    .model-select ::ng-deep .mat-mdc-form-field-subscript-wrapper {
      display: none;
    }

    .model-option {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .model-name {
      font-weight: 500;
    }

    .model-desc {
      font-size: 0.8em;
      color: #9ca3af;
    }

    .no-models-warning {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #ef4444;
      background: #fef2f2;
      padding: 10px 16px;
      border-radius: 12px;
      font-size: 0.9rem;
    }

    /* ===== Privacy Shield Button ===== */
    .privacy-shield-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      background: linear-gradient(135deg, #10b981, #059669);
      color: white;
      border: none;
      padding: 8px 14px;
      border-radius: 20px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.3s ease;
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
    }

    .privacy-shield-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    }

    .privacy-shield-btn .shield-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
    }

    .privacy-shield-btn .shield-text {
      white-space: nowrap;
    }

    /* ===== Privacy Details Panel ===== */
    .privacy-details-panel {
      background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
      border: 1px solid #86efac;
      border-radius: 16px;
      padding: 16px;
      margin: 12px 24px;
      animation: slideDown 0.3s ease-out;
    }

    @keyframes slideDown {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .privacy-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      color: #166534;
      font-weight: 600;
      font-size: 1rem;
    }

    .privacy-header mat-icon {
      color: #10b981;
    }

    .privacy-header button {
      margin-left: auto;
    }

    .privacy-message {
      color: #166534;
      margin: 0 0 12px 0;
      font-size: 0.9rem;
      line-height: 1.5;
    }

    .protection-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .protection-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      background: white;
      padding: 10px 14px;
      border-radius: 10px;
      border: 1px solid #d1fae5;
    }

    .protection-item mat-icon {
      color: #10b981;
      font-size: 20px;
      width: 20px;
      height: 20px;
      flex-shrink: 0;
      margin-top: 2px;
    }

    .protection-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .protection-type {
      font-size: 0.9rem;
      color: #374151;
    }

    .protection-count {
      font-size: 0.8rem;
      color: #059669;
      font-weight: 500;
    }

    .protection-total {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #d1fae5;
      font-size: 0.9rem;
      color: #166534;
    }

    /* ===== Messages Section ===== */
    .messages-section {
      flex: 1;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.6);
      backdrop-filter: blur(20px);
      border-radius: 24px;
      box-shadow: 0 4px 24px rgba(102, 126, 234, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    .messages-container {
      height: 100%;
      overflow-y: auto;
      padding: 24px;
      scroll-behavior: smooth;
    }

    .messages-container::-webkit-scrollbar {
      width: 6px;
    }

    .messages-container::-webkit-scrollbar-track {
      background: transparent;
    }

    .messages-container::-webkit-scrollbar-thumb {
      background: rgba(102, 126, 234, 0.3);
      border-radius: 3px;
    }

    /* ===== Welcome Container ===== */
    .welcome-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      animation: fadeInUp 0.6s ease-out;
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .welcome-card {
      text-align: center;
      max-width: 500px;
    }

    .welcome-icon-container {
      position: relative;
      width: 100px;
      height: 100px;
      margin: 0 auto 24px;
    }

    .welcome-icon-bg {
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 28px;
      transform: rotate(10deg);
      opacity: 0.1;
    }

    .welcome-icon {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 56px;
      width: 56px;
      height: 56px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .sparkle {
      position: absolute;
      font-size: 18px;
      color: #667eea;
      animation: sparkle 2s ease-in-out infinite;
    }

    .sparkle-1 { top: 5px; right: 10px; animation-delay: 0s; }
    .sparkle-2 { bottom: 10px; left: 5px; animation-delay: 0.4s; }
    .sparkle-3 { top: 15px; left: 15px; animation-delay: 0.8s; }

    @keyframes sparkle {
      0%, 100% { opacity: 0.3; transform: scale(0.8); }
      50% { opacity: 1; transform: scale(1.2); }
    }

    .welcome-card h2 {
      margin: 0 0 12px;
      font-size: 1.75rem;
      font-weight: 700;
      color: #1f2937;
    }

    .welcome-subtitle {
      color: #6b7280;
      margin: 0 0 28px;
      font-size: 1.05rem;
    }

    .feature-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      margin-bottom: 32px;
    }

    .feature-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 18px;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
      border-radius: 14px;
      color: #4b5563;
      font-size: 0.95rem;
      font-weight: 500;
      transition: all 0.3s ease;
    }

    .feature-item:hover {
      transform: translateY(-2px);
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
    }

    .feature-item mat-icon {
      color: #667eea;
      font-size: 22px;
      width: 22px;
      height: 22px;
    }

    /* ===== Quick Questions ===== */
    .quick-questions-section {
      width: 100%;
      max-width: 800px;
      margin-top: 20px;
    }

    .quick-questions-header {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #6b7280;
      font-size: 0.95rem;
      margin-bottom: 14px;
      font-weight: 500;
    }

    .quick-questions-header mat-icon {
      color: #f59e0b;
      font-size: 20px;
      width: 20px;
      height: 20px;
    }

    .quick-questions-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
    }

    .quick-question-chip {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 18px;
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 50px;
      cursor: pointer;
      transition: all 0.3s ease;
      font-size: 0.9rem;
      color: #4b5563;
      font-weight: 500;
    }

    .quick-question-chip:hover:not(:disabled) {
      border-color: #667eea;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }

    .quick-question-chip:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .chip-arrow {
      font-size: 16px;
      width: 16px;
      height: 16px;
      color: #9ca3af;
      transition: transform 0.3s ease;
    }

    .quick-question-chip:hover:not(:disabled) .chip-arrow {
      transform: translateX(3px);
      color: #667eea;
    }

    /* ===== Message Styles ===== */
    .message-wrapper {
      animation: slideIn 0.4s ease-out forwards;
      opacity: 0;
      margin-bottom: 20px;
    }

    @keyframes slideIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .user-wrapper {
      display: flex;
      justify-content: flex-end;
    }

    .assistant-wrapper {
      display: flex;
      justify-content: flex-start;
    }

    .message {
      display: flex;
      gap: 12px;
      max-width: 80%;
    }

    .user-message {
      flex-direction: row-reverse;
    }

    .message-avatar {
      width: 44px;
      height: 44px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: transform 0.3s ease;
    }

    .message-avatar:hover {
      transform: scale(1.05);
    }

    .user-avatar {
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .ai-avatar {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .message-bubble {
      padding: 16px 20px;
      border-radius: 20px;
      position: relative;
    }

    .user-bubble {
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      color: white;
      border-bottom-right-radius: 6px;
      box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
    }

    .ai-bubble {
      background: white;
      color: #1f2937;
      border-bottom-left-radius: 6px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
      border: 1px solid #f3f4f6;
    }

    .message-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }

    .sender-name {
      font-weight: 600;
      font-size: 0.85rem;
    }

    .user-bubble .sender-name {
      color: rgba(255, 255, 255, 0.9);
    }

    .ai-bubble .sender-name {
      color: #667eea;
    }

    .message-time {
      font-size: 0.75rem;
      opacity: 0.7;
    }

    .model-tag {
      font-size: 0.7rem;
      padding: 3px 10px;
      border-radius: 20px;
      font-weight: 500;
    }

    .user-bubble .model-tag {
      background: rgba(255, 255, 255, 0.2);
      color: white;
    }

    .ai-bubble .model-tag {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
      color: #667eea;
    }

    .message-text {
      line-height: 1.6;
      word-wrap: break-word;
      font-size: 0.95rem;
    }

    /* ===== Markdown Styles ===== */
    .markdown-content {
      ::ng-deep {
        p { margin: 0 0 12px 0; }
        p:last-child { margin: 0; }
        ul, ol { margin: 12px 0; padding-left: 24px; }
        li { margin: 6px 0; }
        strong { color: #1f2937; }
        code { 
          background: #f3f4f6; 
          padding: 3px 8px; 
          border-radius: 6px;
          font-size: 0.88em;
          font-family: 'Fira Code', monospace;
          color: #e11d48;
        }
        pre {
          background: #1f2937;
          color: #f9fafb;
          padding: 16px;
          border-radius: 12px;
          overflow-x: auto;
          margin: 12px 0;
        }
        pre code {
          background: none;
          padding: 0;
          color: inherit;
        }
        table {
          border-collapse: collapse;
          width: 100%;
          margin: 12px 0;
          border-radius: 8px;
          overflow: hidden;
        }
        th, td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }
        th {
          background: #f9fafb;
          font-weight: 600;
          color: #374151;
        }
        tr:last-child td {
          border-bottom: none;
        }
      }
    }

    /* ===== Typing Indicator ===== */
    .loading-bubble {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 24px;
    }

    .typing-indicator {
      display: flex;
      gap: 5px;
    }

    .typing-dot {
      width: 10px;
      height: 10px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 50%;
      animation: typing-bounce 1.4s infinite ease-in-out;
    }

    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }

    @keyframes typing-bounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
      40% { transform: scale(1); opacity: 1; }
    }

    .thinking-text {
      color: #9ca3af;
      font-size: 0.9rem;
      font-style: italic;
    }

    /* ===== Input Section ===== */
    .input-section {
      flex-shrink: 0;
      padding-top: 20px;
    }

    .input-container {
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(20px);
      border-radius: 24px;
      padding: 16px 24px 20px;
      box-shadow: 0 -4px 24px rgba(102, 126, 234, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.8);
    }

    /* Quick Questions Inline - Always visible above input */
    .quick-questions-inline {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
      padding-bottom: 14px;
      border-bottom: 1px solid #f0f0f0;
    }

    .quick-btn {
      padding: 8px 14px;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
      border: 1px solid rgba(102, 126, 234, 0.2);
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.25s ease;
      font-size: 0.82rem;
      color: #4b5563;
      font-weight: 500;
      white-space: nowrap;
    }

    .quick-btn:hover:not(:disabled) {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
      border-color: #667eea;
      color: #667eea;
      transform: translateY(-1px);
    }

    .quick-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .input-wrapper {
      display: flex;
      align-items: center;
      gap: 16px;
      background: #f9fafb;
      border: 2px solid #e5e7eb;
      border-radius: 16px;
      padding: 8px 16px;
      transition: all 0.3s ease;
    }

    .input-wrapper:focus-within {
      border-color: #667eea;
      background: white;
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
    }

    .input-icon {
      color: #9ca3af;
      font-size: 24px;
      width: 24px;
      height: 24px;
    }

    .chat-input {
      flex: 1;
      border: none;
      outline: none;
      background: transparent;
      font-size: 1rem;
      color: #1f2937;
      resize: none;
      min-height: 24px;
      max-height: 120px;
      line-height: 1.5;
      font-family: inherit;
    }

    .chat-input::placeholder {
      color: #9ca3af;
    }

    .chat-input:disabled {
      cursor: not-allowed;
    }

    .send-button {
      width: 48px;
      height: 48px;
      border-radius: 14px;
      border: none;
      background: #e5e7eb;
      color: #9ca3af;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
    }

    .send-button.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .send-button.active:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
    }

    .send-button:disabled {
      cursor: not-allowed;
    }

    .input-hint {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: #f59e0b;
      font-size: 0.9rem;
      margin-top: 12px;
      padding: 10px;
      background: #fffbeb;
      border-radius: 10px;
    }

    .powered-by {
      text-align: center;
      margin-top: 14px;
      font-size: 0.8rem;
      color: #9ca3af;
    }

    .powered-by .highlight {
      color: #667eea;
      font-weight: 600;
    }

    /* ===== Responsive ===== */
    @media (max-width: 768px) {
      .chat-container {
        padding: 12px;
      }

      .header-content {
        flex-direction: column;
        gap: 16px;
        padding: 16px;
      }

      .model-select {
        width: 100%;
      }

      .feature-grid {
        grid-template-columns: 1fr;
      }

      .message {
        max-width: 90%;
      }

      .quick-question-chip {
        font-size: 0.85rem;
        padding: 10px 14px;
      }
    }
  `]
})
export class AIChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;

  private destroy$ = new Subject<void>();
  
  models: AIModel[] = [];
  modelGroups: { provider: string; models: AIModel[] }[] = [];
  selectedModel: string | null = null;
  
  messages: ChatMessage[] = [];
  userInput = '';
  quickQuestions: string[] = [];
  
  isLoading = false;
  isLoadingModels = true;
  private shouldScrollToBottom = false;

  // Privacy protection status
  privacyStatus: PrivacyStatus | null = null;
  showPrivacyDetails = false;

  constructor(
    private aiService: AIService,
    private snackBar: MatSnackBar,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit() {
    // Load available models
    this.aiService.models$
      .pipe(takeUntil(this.destroy$))
      .subscribe(models => {
        this.models = models;
        this.groupModelsByProvider();
        this.isLoadingModels = false;
      });

    // Track selected model
    this.aiService.selectedModel$
      .pipe(takeUntil(this.destroy$))
      .subscribe(model => {
        this.selectedModel = model;
      });

    // Load quick questions
    this.aiService.getQuickQuestions()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.quickQuestions = response.questions;
        },
        error: (err) => {
          console.error('Failed to load quick questions:', err);
        }
      });

    // Load privacy status
    this.loadPrivacyStatus();
  }

  loadPrivacyStatus() {
    this.aiService.getPrivacyStatus()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (status) => {
          this.privacyStatus = status;
        },
        error: (err) => {
          console.error('Failed to load privacy status:', err);
          // Set default privacy status
          this.privacyStatus = {
            privacy_enabled: true,
            protection_measures: [],
            total_items_protected: 0,
            message: 'Privacy protection is enabled.'
          };
        }
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  groupModelsByProvider() {
    const groups = new Map<string, AIModel[]>();
    
    for (const model of this.models) {
      if (!groups.has(model.provider)) {
        groups.set(model.provider, []);
      }
      groups.get(model.provider)!.push(model);
    }

    this.modelGroups = Array.from(groups.entries()).map(([provider, models]) => ({
      provider,
      models
    }));
  }

  onModelChange(modelId: string) {
    this.aiService.setSelectedModel(modelId);
  }

  askQuestion(question: string) {
    this.userInput = question;
    this.sendMessage();
  }

  sendMessage(event?: Event) {
    if (event) {
      event.preventDefault();
    }

    const message = this.userInput.trim();
    if (!message || this.isLoading || !this.selectedModel) {
      return;
    }

    // Add user message
    this.messages.push({
      role: 'user',
      content: message,
      timestamp: new Date()
    });

    this.userInput = '';
    this.isLoading = true;
    this.shouldScrollToBottom = true;

    // Get history for context (last 10 messages)
    const history = this.messages.slice(-10);

    // Send to AI
    this.aiService.sendMessage(message, history)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.messages.push({
            role: 'assistant',
            content: response.response,
            timestamp: new Date(),
            model: response.model_used
          });
          this.isLoading = false;
          this.shouldScrollToBottom = true;
        },
        error: (error) => {
          console.error('Chat error:', error);
          this.snackBar.open(
            error.error?.detail || 'Failed to get AI response. Please try again.',
            'Close',
            { duration: 5000 }
          );
          this.isLoading = false;
        }
      });
  }

  renderMarkdown(content: string): SafeHtml {
    try {
      const html = marked(content, { breaks: true });
      return this.sanitizer.bypassSecurityTrustHtml(html as string);
    } catch {
      return content;
    }
  }

  formatTime(date: Date | undefined): string {
    if (!date) return '';
    return new Date(date).toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  }

  autoGrow(event: Event) {
    const textarea = event.target as HTMLTextAreaElement;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  }

  private scrollToBottom() {
    try {
      const container = this.messagesContainer?.nativeElement;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    } catch (err) {
      console.error('Scroll error:', err);
    }
  }
}
