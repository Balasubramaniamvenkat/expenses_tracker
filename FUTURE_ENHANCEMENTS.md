# Future Enhancements — Family Finance Tracker

> **Created:** February 6, 2026  
> **Purpose:** Comprehensive reference for planned improvements, bug fixes, aesthetic upgrades, and mobile conversion roadmap.  
> **How to use:** Pick items by priority, check them off as completed. Each item includes the files involved and what needs to change.

---

## Table of Contents

1. [Critical Bugs to Fix (P0)](#1-critical-bugs-to-fix-p0)
2. [Architecture Improvements (P1)](#2-architecture-improvements-p1)
3. [Frontend Code Quality (P1)](#3-frontend-code-quality-p1)
4. [Aesthetic & UI Fixes (P1-P2)](#4-aesthetic--ui-fixes-p1-p2)
5. [New Feature Enhancements (P2)](#5-new-feature-enhancements-p2)
6. [Backend Improvements (P2)](#6-backend-improvements-p2)
7. [Aesthetic Polish & Delight (P3)](#7-aesthetic-polish--delight-p3)
8. [Mobile App Conversion Roadmap](#8-mobile-app-conversion-roadmap)
9. [Priority Summary Table](#9-priority-summary-table)

---

## 1. Critical Bugs to Fix (P0)

### 1.1 App Boots with Mock Upload Service

- **Problem:** `frontend/app/src/app/app.config.ts` imports from `app.config.mock.ts` — the real `UploadService` is never used. Users silently get fake data on upload.
- **Files to change:**
  - `frontend/app/src/app/app.config.ts` — switch to real service provider
  - `frontend/app/src/app/app.config.mock.ts` — keep as reference, but do NOT import in production
- **Fix:** Update the provider in `app.config.ts` to use the real `UploadService` instead of the mock. Add environment-based switching:
  ```typescript
  providers: [
    environment.useMocks
      ? { provide: UploadService, useClass: MockUploadService }
      : UploadService
  ]
  ```
- [ ] **Done**

---

### 1.2 Hardcoded `localhost:8000` in Frontend Services

- **Problem:** Dashboard service, AI chat service, and categories service use hardcoded `http://localhost:8000/api` instead of environment-based URL. This breaks any non-local deployment.
- **Files to change:**
  - `frontend/app/src/app/pages/dashboard/dashboard-enhanced.component.ts`
  - `frontend/app/src/app/modules/ai-insights/ai-chat.component.ts`
  - `frontend/app/src/app/modules/categories/categories.service.ts` (if exists)
  - `frontend/app/src/environments/environment.ts`
  - `frontend/app/src/environments/environment.prod.ts`
- **Fix:** Define `apiUrl` in environment files and inject it in all services:
  ```typescript
  // environment.ts
  export const environment = {
    production: false,
    apiUrl: 'http://localhost:8000/api'
  };
  ```
- [ ] **Done**

---

### 1.3 Missing NgRx Actions

- **Problem:** The categories reducer (`categories.reducer.ts`) handles `RecategorizeTransactions`, `LearnCategory`, and `ResetCategories` — but these actions are never defined in the actions file. Dispatching them causes runtime crashes.
- **Files to change:**
  - `frontend/app/src/app/modules/categories/store/categories.actions.ts` — add missing action definitions
  - `frontend/app/src/app/modules/categories/store/categories.reducer.ts` — verify handlers match
- [ ] **Done**

---

### 1.4 Dead Routing File

- **Problem:** `frontend/app/src/app/app-routing.module.ts` exists but is never used — standalone bootstrap uses `app.routes.ts`. Creates confusion.
- **Files to change:**
  - `frontend/app/src/app/app-routing.module.ts` — DELETE this file
- [ ] **Done**

---

### 1.5 Production CORS Configuration

- **Problem:** `backend/api/main.py` hardcodes `allow_origins=["http://localhost:4200"]`. This blocks any other origin.
- **Files to change:**
  - `backend/api/main.py` — make origins configurable via environment variable
- **Fix:**
  ```python
  import os
  origins = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
  app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
  ```
- [ ] **Done**

---

## 2. Architecture Improvements (P1)

### 2.1 Keep CSV-Based Storage (Current) — SQLite Deferred to Future

- **Current approach:** All data lives in `processed_data.csv` — this is simple, transparent, and works well for single-user local usage. Keep this as the data layer for now.
- **Immediate improvement:** Consolidate CSV loading logic into a shared helper (see 2.2 below) so all API endpoints read from one consistent place.
- **When to revisit SQLite:** Consider migrating to SQLite only when:
  - Multi-user support is needed
  - Dataset size exceeds ~50K transactions and performance suffers
  - Mobile app conversion begins (Capacitor + SQLite is the natural path)
  - Concurrent access becomes a real problem
- **Status:** ✅ CSV approach retained. SQLite migration deferred to Future/P3.

> **Future reference (SQLite schema for when needed):**
> ```sql
> CREATE TABLE transactions (
>   id INTEGER PRIMARY KEY, date DATE, description TEXT,
>   amount REAL, balance REAL, category TEXT, subcategory TEXT,
>   account TEXT DEFAULT 'Default', source_file TEXT,
>   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
> );
> CREATE TABLE user_category_mappings (
>   id INTEGER PRIMARY KEY, keyword TEXT, category TEXT,
>   subcategory TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
> );
> CREATE TABLE chat_history (
>   id INTEGER PRIMARY KEY, session_id TEXT, role TEXT,
>   content TEXT, model_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
> );
> ```

- [ ] **Done**

---

### 2.2 Extract Shared CSV Data Helper (Eliminate Duplication)

- **Problem:** Every API file independently does path-finding for `processed_data.csv`:
  ```python
  possible_paths = ['processed_data.csv', '../processed_data.csv', ...]
  ```
  This logic is duplicated 5 times across `upload.py`, `transactions.py`, `dashboard.py`, `categories.py`, `categories_hierarchy.py`.
- **Files to change:**
  - NEW: `backend/SRC/csv_data_helper.py` — single helper class for CSV loading, path resolution, and common data cleaning
  - All 5 API files above — import from `csv_data_helper` instead of doing their own loading
- **What the helper should do:**
  ```python
  class CSVDataHelper:
      @staticmethod
      def get_processed_data_path() -> str: ...       # One place for path resolution
      @staticmethod
      def load_transactions() -> pd.DataFrame: ...     # Load + clean + parse dates
      @staticmethod
      def save_transactions(df) -> bool: ...           # Save processed data
      @staticmethod
      def get_income_df(df) -> pd.DataFrame: ...       # Filter income rows
      @staticmethod
      def get_expense_df(df) -> pd.DataFrame: ...      # Filter expense rows
  ```
- [ ] **Done**

---

### 2.3 Add Angular HTTP Interceptor

- **Problem:** No global error handling for API calls. No retry logic, no request logging, no centralized error toasts.
- **Files to create:**
  - NEW: `frontend/app/src/app/core/interceptors/api.interceptor.ts`
  - NEW: `frontend/app/src/app/core/interceptors/error.interceptor.ts`
- **Features:**
  - Inject `environment.apiUrl` as base URL
  - Catch all HTTP errors → show user-friendly snackbar
  - Add retry logic for transient 5xx errors
  - Log requests in development mode
- [ ] **Done**

---

### 2.4 Fix Python Import System

- **Problem:** Every API file uses `sys.path.insert(0, ...)` and `importlib.util.spec_from_file_location()` to find modules. This is fragile and non-standard.
- **Files to change:**
  - `backend/SRC/__init__.py` — ensure proper package structure
  - `backend/api/__init__.py` — ensure proper package structure
  - All API files — replace `sys.path` hacks with proper relative imports
- **Fix:** Use proper Python package imports:
  ```python
  from ..SRC.data_extraction import extract_data_from_file
  from ..SRC.refined_categories import RefinedCategorizer
  ```
- [ ] **Done**

---

## 3. Frontend Code Quality (P1)

### 3.1 Split Massive Inline Components

- **Problem:** Several components have gigantic inline templates + styles in a single `.ts` file:
  - `AIChatComponent` → 1,829 lines
  - `SimpleUploadComponent` → 1,471 lines
  - `DashboardComponent` → 806 lines
- **Fix:** Extract into separate files:
  ```
  ai-chat.component.ts      → logic only
  ai-chat.component.html    → template
  ai-chat.component.scss    → styles
  ```
  Further break down into child components:
  - `AIChatComponent` → `ChatMessageComponent`, `ChatSidebarComponent`, `ChatInputComponent`, `ChatWelcomeComponent`
  - `SimpleUploadComponent` → `DropZoneComponent`, `FilePreviewComponent`, `UploadSuccessComponent`
- [ ] **Done**

---

### 3.2 Remove Unused Dependencies

- **Problem:** Several packages are installed but never imported:
  - `d3` + `@types/d3` (~500KB) — completely unused
  - `ng2-charts` — not imported (raw Chart.js used directly)
  - `ngx-color-picker` — never imported
  - `ngx-file-drop` — partially replaced by native drag-and-drop
- **File to change:**
  - `frontend/app/package.json` — remove unused packages
- **Run after:** `npm uninstall d3 @types/d3 ng2-charts ngx-color-picker`
- [ ] **Done**

---

### 3.3 Delete Duplicate Upload Services

- **Problem:** Three versions of UploadService exist:
  - `upload.service.ts` (real)
  - `upload.service.mock.ts` (mock)
  - Another mock variant (dead code)
- **Fix:** Keep one real service, one mock service. Delete all others.
- [ ] **Done**

---

### 3.4 Add `trackBy` to `*ngFor` Loops

- **Problem:** Chat messages, nav items, and transaction lists re-render entirely on every change.
- **Files to change:** All components using `*ngFor` — add `trackBy` functions.
  ```html
  <div *ngFor="let msg of messages; trackBy: trackByMessageId">
  ```
- [ ] **Done**

---

### 3.5 Replace console.log with Logging Service

- **Problem:** `console.log` statements are everywhere in production code across all services and components.
- **Fix:** Create a `LoggerService` with log levels (debug/info/warn/error) that can be disabled in production.
- [ ] **Done**

---

### 3.6 Remove Hardcoded Fallback Data

- **Problem:** `categories.service.ts` returns hardcoded financial numbers when the API fails, silently masking errors.
- **Fix:** Return proper empty states or show error UI instead of fake data.
- [ ] **Done**

---

## 4. Aesthetic & UI Fixes (P1-P2)

### 4.1 Unify Color Palette Across All Components (P1 — HIGHEST IMPACT)

- **Problem:** Three competing color systems make the app feel like 3 different products:
  | Page | Primary Color | Source |
  |------|--------------|--------|
  | Global / Nav / Upload | `#1976D2` | CSS variables ✅ |
  | Dashboard / AI Chat | `#667eea` | Hardcoded ❌ |
  | Transactions | `#6366f1` | SCSS variables ❌ |
- **Files to change:**
  - `frontend/app/src/styles.scss` — keep as the single source of truth for CSS variables
  - `frontend/app/src/app/pages/dashboard/dashboard-enhanced.component.ts` — replace all hardcoded hex colors with `var(--primary-color)`, `var(--primary-dark)`, etc.
  - `frontend/app/src/app/modules/transactions/transaction-list.component.ts` — remove local SCSS `$primary` variable, use global CSS variables
  - `frontend/app/src/app/modules/ai-insights/ai-chat.component.ts` — replace `#667eea` with `var(--primary-color)`
  - `frontend/app/src/styles.scss` (dropdown panels) — replace `#667eea` references with `var(--primary-color)`
- **Decision needed:** Pick ONE primary color for the entire app. Options:
  - `#1976D2` (current Material Blue — trustworthy, bank-like)
  - `#667eea` (Indigo — modern, trendy)
  - `#6366f1` (Tailwind Indigo — similar to above)
- [ ] **Done**

---

### 4.2 Fix Missing Font Weights (P1)

- **Problem:** `index.html` loads `Roboto:wght@300;400;500` but components use weights 600, 700, 800 everywhere. Browser renders faux-bold which looks blurry.
- **File to change:**
  - `frontend/app/src/index.html` — update Google Fonts link
- **Fix:** Change to:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  ```
- [ ] **Done**

---

### 4.3 Fix Font Family Mismatch in Transactions (P1)

- **Problem:** Transaction list component declares `font-family: 'Inter', ...` but Inter is never loaded. Falls back to system fonts, looking different from other pages.
- **File to change:**
  - `frontend/app/src/app/modules/transactions/transaction-list.component.ts` (inline styles)
- **Fix:** Remove the Inter font-family declaration, inherit from global Roboto.
- [ ] **Done**

---

### 4.4 Unify Border Radius, Shadows, Spacing (P1)

- **Problem:** Inconsistent values across components:
  | Component | Radius | Shadow | Spacing |
  |-----------|--------|--------|---------|
  | Global cards | `var(--radius-large)` = 16px | `var(--shadow-medium)` | `var(--spacing-lg)` |
  | Transactions | `24px` hardcoded | 7 custom shadow variables | `32px` hardcoded |
  | AI Chat | `20px` hardcoded | Hardcoded | Hardcoded |
  | Upload | Uses CSS vars ✅ | Uses CSS vars ✅ | Uses CSS vars ✅ |
- **Fix:** Make Dashboard, Transactions, and AI Chat use the global CSS variable tokens, following Upload component as the gold standard.
- [ ] **Done**

---

### 4.5 Clean Up `!important` Epidemic (P1)

- **Problem:** Global styles have 100+ `!important` declarations, including 3 duplicate definitions of `.cdk-overlay-container` and `.cdk-overlay-pane`. This is an escalating specificity war.
- **File to change:**
  - `frontend/app/src/styles.scss` — remove duplicate blocks, use Angular Material theming system
- **Fix:** Use `@use '@angular/material' as mat;` theming with custom density/color/typography configs to eliminate most `!important` overrides.
- [ ] **Done**

---

### 4.6 Implement Dark Mode (P1)

- **Problem:** Only the Navigation has a partial `prefers-color-scheme: dark` query. Enabling OS dark mode gives a dark nav with blinding white body.
- **Files to change:**
  - `frontend/app/src/styles.scss` — add dark theme CSS variables
  - Navigation component — add theme toggle button
  - NEW: `frontend/app/src/app/core/services/theme.service.ts` — manage theme state
- **Fix:** Use the existing CSS variable system:
  ```scss
  [data-theme="dark"] {
    --surface: #1e1e2e;
    --background: #11111b;
    --on-surface: #cdd6f4;
    --on-surface-medium: #a6adc8;
    --shadow-medium: 0 4px 8px rgba(0, 0, 0, 0.4);
  }
  ```
- [ ] **Done**

---

### 4.7 Remove Emojis from Chart Axes (P2)

- **Problem:** Transaction timeline chart uses `'💰 Income'`, `'💳 Expenses'`, `'📊 Amount (₹)'` as axis labels. Looks unprofessional and renders inconsistently across OS/browsers.
- **File to change:**
  - `frontend/app/src/app/modules/transactions/transaction-list.component.ts`
- **Fix:** Use plain text labels. Reserve emojis for category badges only.
- [ ] **Done**

---

### 4.8 Fix Table Row Hover Effect (P2)

- **Problem:** `.mat-mdc-row:hover { transform: scale(1.005) }` causes table rows to "pop out" breaking grid alignment.
- **File to change:**
  - `frontend/app/src/app/modules/transactions/transaction-list.component.ts` (inline styles)
- **Fix:** Replace `transform: scale()` with subtle `background-color` change on hover.
- [ ] **Done**

---

### 4.9 Unify Dashboard Header Gradient with Nav (P2)

- **Problem:** Nav bar uses `var(--primary-color) → var(--primary-dark)` (blue gradient) but dashboard chart headers use `#667eea → #764ba2` (purple gradient). Visually jarring side-by-side.
- **Fix:** Make chart headers use the same primary gradient as the nav bar.
- [ ] **Done**

---

### 4.10 Define Typography Scale Tokens (P2)

- **Problem:** Every component invents its own font sizes. Dashboard uses `28px` titles, Transactions uses `2.25rem` (36px) titles.
- **File to change:**
  - `frontend/app/src/styles.scss` — add typography tokens
- **Fix:** Add and enforce:
  ```scss
  :root {
    --text-h1: 28px;     /* Page titles */
    --text-h2: 20px;     /* Section titles */
    --text-h3: 16px;     /* Card titles */
    --text-body: 14px;   /* Body text */
    --text-caption: 12px; /* Captions, labels */
    --text-overline: 11px; /* Overlines, uppercase */
  }
  ```
- [ ] **Done**

---

### 4.11 Upload Drop Zone Accessibility (P2)

- **Problem:** Drop zone is a `<div>` with no `tabindex` — keyboard users can't reach it. No `role` or `keydown` handler.
- **File to change:**
  - `frontend/app/src/app/modules/upload/simple-upload.component.ts`
- **Fix:** Add `tabindex="0"`, `role="button"`, `aria-label="Upload CSV file"`, and `(keydown.enter)` / `(keydown.space)` handlers.
- [ ] **Done**

---

### 4.12 AI Chat Accessibility (P2)

- **Problem:** No `aria-live` on messages container (screen readers won't announce new messages). No `role` on chat area. Send button has no `aria-label`.
- **File to change:**
  - `frontend/app/src/app/modules/ai-insights/ai-chat.component.ts`
- **Fix:** Add `aria-live="polite"` to messages container, `role="log"`, `aria-label="Send message"` on send button, `aria-expanded` on sidebar toggle.
- [ ] **Done**

---

## 5. New Feature Enhancements (P2)

### 5.1 Multi-Bank Support

- **Problem:** Currently HDFC-only. Indian users commonly use SBI, ICICI, Axis, Kotak, etc.
- **Files to change:**
  - `backend/SRC/data_extraction.py` — add parser plugins for each bank format
  - NEW: `backend/SRC/bank_parsers/` directory with individual parsers
  - NEW: `backend/SRC/bank_parsers/hdfc.py`, `sbi.py`, `icici.py`, `axis.py`, `kotak.py`
  - `backend/api/upload.py` — auto-detect bank format from CSV headers
  - Frontend upload component — let user select bank if auto-detection fails
- **Note:** `ColumnMappingComponent` already exists (commented out in upload module) — re-enable it as fallback for unknown formats.
- [ ] **Done**

---

### 5.2 Budget Tracking UI

- **Problem:** Data model already has `budget_target` fields in category analytics, but there's no UI to set or view budgets.
- **Files to create:**
  - NEW: `frontend/app/src/app/modules/budget/` — new module
  - NEW: `backend/api/budget.py` — budget CRUD endpoints
- **Features:**
  - Budget configuration page (set monthly limits per category)
  - Budget vs. actual comparison bars on dashboard
  - Alert notifications when spending exceeds thresholds
  - Progress rings per category
- [ ] **Done**

---

### 5.3 Recurring Transaction Detection

- **Problem:** No detection of recurring patterns (rent, SIP, EMI, subscriptions).
- **Files to create:**
  - NEW: `backend/SRC/recurring_detector.py` — pattern analysis engine
  - NEW: `backend/api/recurring.py` — API endpoints
- **Features:**
  - Detect monthly patterns from transaction history
  - "Upcoming bills" widget on dashboard
  - Subscription tracker with monthly total
  - Alert for unusual recurring charge changes
- [ ] **Done**

---

### 5.4 Export Capabilities

- **Problem:** No way to export data.
- **Features to add:**
  - Export filtered transactions as CSV / Excel / PDF
  - Export dashboard charts as PNG images
  - Monthly/yearly financial report generation
- [ ] **Done**

---

### 5.5 Financial Goals & Savings Tracker

- **Features:**
  - Set goals (e.g., "Save ₹5L for vacation by Dec 2026")
  - Progress bars with automatic tracking based on savings rate
  - AI-powered recommendations to reach goals faster
- [ ] **Done**

---

### 5.6 Smart Auto-Generated Insights

- **Problem:** Users must ask AI questions manually. Auto-generate insights instead.
- **Features:**
  - "Your food spending increased 40% this month"
  - "You have 3 recurring subscriptions totaling ₹2,500/month"
  - "Your savings rate improved from 15% to 22%"
  - "Spending anomaly: 3x more on Shopping this month"
- [ ] **Done**

---

### 5.7 Family Member Tagging

- **Problem:** This is a "Family Finance Tracker" but can't tag transactions to family members.
- **Features:**
  - Tag transactions to family members
  - Per-member spending analytics
  - Answer: "How much did we spend on kids' education?"
- [ ] **Done**

---

### 5.8 Receipt / Invoice Attachment

- **Features:**
  - Attach photos of receipts to transactions
  - Store locally (privacy-first)
  - Searchable receipt archive
- [ ] **Done**

---

## 6. Backend Improvements (P2)

### 6.1 Authentication & Multi-User Support

- **Problem:** No auth — anyone on the network can access the API.
- **Features:**
  - Simple local auth (PIN/password)
  - Per-user data isolation
  - Session management
- [ ] **Done**

---

### 6.2 API Versioning

- **Problem:** No API versioning — breaking changes will affect clients.
- **Fix:** Prefix all routes with `/api/v1/`.
- [ ] **Done**

---

### 6.3 File Upload Security

- **Problem:** The upload UI limits each file to 50MB, but the API does not enforce a
  server-side file or total-request size limit. Batch file count is intentionally not capped.
- **Fix:**
  - Enforce per-file and total-request size limits on the server
  - Rate limiting on AI chat endpoint
  - Better CSV validation with clear error messages
- [ ] **Done**

---

### 6.4 Persist AI Chat History

- **Problem:** Chat sessions are stored only in browser memory (BehaviorSubject) — lost on refresh.
- **Fix:** Save to **LocalStorage** (simple, for small history) or **IndexedDB** (for larger chat history with search). Since we're keeping CSV-based storage, no backend DB table is needed — keep this entirely on the frontend.
- **Implementation options:**
  - Quick: `localStorage.setItem('chat_sessions', JSON.stringify(sessions))`
  - Better: Use `idb` library for IndexedDB with async access and larger storage limits
- [ ] **Done**

---

## 7. Aesthetic Polish & Delight (P3)

### 7.1 Skeleton Loading Screens

- **Note:** A `shimmer` keyframe animation is already defined in `styles.scss` but never used!
- **Fix:** Replace plain spinners with skeleton placeholder cards that shimmer (like YouTube/Facebook).
- [ ] **Done**

---

### 7.2 Page Transition Animations

- **Fix:** Add Angular route animations — subtle fade-in on page enter, staggered card entry using the `fadeInUp` keyframe already defined globally.
- [ ] **Done**

---

### 7.3 Micro-Interactions

- Ripple effects on clickable chart elements
- Subtle scale on category cards when drilling down
- Number count-up animations on dashboard summary cards (₹0 → ₹85,000 over 500ms)
- Success animation on upload completion
- [ ] **Done**

---

### 7.4 SVG Empty State Illustrations

- Replace plain text + icon empty states with lightweight SVG illustrations
- Empty dashboard → chart illustration with "+" icon
- No transactions → receipt illustration
- AI chat welcome → robot assistant illustration
- **Resource:** [unDraw](https://undraw.co) for free SVG illustrations
- [ ] **Done**

---

### 7.5 Navigation Bar Enhancements

- User avatar/initials badge (top-right)
- Active route indicator with smooth sliding animation
- "Collapse to icons-only" option for desktop (more content space)
- [ ] **Done**

---

### 7.6 Consistent Iconography

- Use Material Icons consistently for navigation and actions
- Reserve emoji for category badges only (🍔 Food, 🛒 Shopping, etc.)
- Remove emoji from chart axes and table headers
- [ ] **Done**

---

### 7.7 AI Chat Background Performance

- **Problem:** Three floating gradient orbs with `blur(80px)` and infinite animation can cause GPU pressure on lower-end devices.
- **Fix:** Add `@media (prefers-reduced-motion: reduce)` to disable animations. Pause when chat isn't active.
- [ ] **Done**

---

## 8. Mobile App Conversion Roadmap

### 8.1 Recommended Approach: Ionic + Capacitor

**Why:** Maximum code reuse (~70%) from existing Angular codebase.

#### What Maps Directly (No Changes)
- All Angular components, templates, styles
- Chart.js visualizations
- NgRx state management
- AI Chat (calls LLM APIs directly from device)
- Material UI components
- `merchant_database.json` (bundle as app asset)

#### What Needs Replacement

| Web Version | Mobile Version |
|-------------|----------------|
| CSV file upload (primary input) | SMS reader (primary) + CSV (fallback) |
| FastAPI backend on localhost | On-device TypeScript services |
| `processed_data.csv` | CSV file via Capacitor Filesystem (or SQLite later if needed) |
| Browser localStorage | Capacitor Preferences API |

#### New Components to Build

| Component | Effort | Description |
|-----------|--------|-------------|
| SMS Permission & Reader | 1 week | Capacitor plugin + Android permission flow |
| Bank SMS Parser | 1-2 weeks | Regex patterns for 5-6 major Indian banks |
| TypeScript Categorizer | 1 week | Port from Python `refined_categories.py`, reuse `merchant_database.json` |
| On-Device CSV Data Layer | 3-4 days | Read/write CSV via Capacitor Filesystem API (same format as web app) |
| iOS Fallback (CSV/Manual) | 3-4 days | Already exists, polish for mobile |

**Total estimated effort:** 4-6 weeks

---

### 8.2 SMS Reading Capability

#### Platform Support
| Platform | Can Read SMS? | Method |
|----------|--------------|--------|
| **Android** | ✅ Yes | `android.permission.READ_SMS` + Capacitor plugin |
| **iOS** | ❌ No | Apple blocks ALL SMS access. No exceptions. |

#### Bank SMS Sender IDs (India)
```
HDFC  → HDFCBK, HDFCBN, HDFC
SBI   → SBIINB, SBIATM, SBIUPI
ICICI → ICICIB, ICICIR
Axis  → AXISBK, AxisBk
Kotak → KOTAKB
Yes   → YESBK
```

#### SMS Parsing Regex Patterns
```typescript
// Amount extraction
/Rs\.?\s*([\d,]+\.?\d*)\s*(debited|credited|withdrawn|deposited)/i

// Date extraction
/on\s+(\d{2}[-\/]\d{2}[-\/]\d{2,4})/i

// UPI merchant
/UPI\s+(?:txn\s+)?(?:to|from)\s+([A-Za-z0-9\s]+?)(?:\.|Ref)/i

// Balance
/(?:Bal|Balance)[:\s]*Rs\.?\s*([\d,]+\.?\d*)/i

// Account number (masked)
/a\/c\s*[*Xx]*(\d{4})/i
```

#### Processing Pipeline
```
Phone SMS Inbox
      │
      ▼
SMS Filter (bank senders only)
      │
      ▼
SMS Parser (regex extraction)
      │
      ▼
Categorization Engine (merchant_database.json + refined_categories logic)
      │
      ▼
CSV File Storage (on-device, same processed_data.csv format as web)
      │
      ▼
Existing Angular UI (Dashboard, Charts, AI Chat)
```

---

### 8.3 iOS Alternatives (Since SMS is Blocked)

1. **CSV upload** — existing flow (users export from bank app)
2. **Account Aggregator (AA) framework** — India's open banking standard (requires RBI-licensed AA registration)
3. **Screenshot OCR** — user takes screenshots of bank app, OCR amounts using Apple Vision framework
4. **Manual entry** — with smart autocomplete from merchant database

---

### 8.4 Capacitor Setup Steps

```bash
# 1. Install Ionic CLI and Capacitor
npm install -g @ionic/cli
npm install @capacitor/core @capacitor/cli

# 2. Initialize Capacitor in existing Angular project
npx cap init "Family Finance Tracker" "com.familyfinance.tracker"

# 3. Add platforms
npx cap add android
npx cap add ios

# 4. Install required plugins
npm install @capacitor/filesystem             # CSV file read/write on device
npm install @capacitor/preferences           # Key-value storage (settings, chat history)
npm install @capacitor/camera                # Receipt photos
npm install @capacitor/share                 # Export sharing
# npm install capacitor-sms-reader           # SMS reading (Android)
# npm install @capacitor-community/sqlite    # SQLite (only if migrating from CSV later)

# 5. Build and sync
ng build --configuration production
npx cap sync

# 6. Open in native IDE
npx cap open android   # Opens Android Studio
npx cap open ios       # Opens Xcode
```

---

### 8.5 Alternative Approaches (Not Recommended)

| Approach | Effort | Code Reuse | Notes |
|----------|--------|------------|-------|
| **PWA** | 1-2 weeks | ~95% | ❌ Cannot read SMS on any platform |
| **Flutter rewrite** | 3-6 months | ~5% | Full rewrite, only reuse JSON/logic |
| **React Native rewrite** | 2-4 months | ~10% | Full rewrite |
| **Ionic + Capacitor** ✅ | 4-6 weeks | ~70% | Best path for this codebase |

---

## 9. Priority Summary Table

| # | Priority | Item | Impact | Effort |
|---|----------|------|--------|--------|
| 1.1 | 🔴 P0 | Fix mock service injection | App doesn't work with real data | 30 min |
| 1.2 | 🔴 P0 | Fix hardcoded API URLs | Deployment blocker | 1 hour |
| 1.3 | 🔴 P0 | Fix missing NgRx actions | Runtime crashes | 30 min |
| 1.4 | 🔴 P0 | Delete dead routing file | Code clarity | 5 min |
| 1.5 | 🔴 P0 | Fix CORS configuration | Deployment blocker | 15 min |
| 4.1 | 🟡 P1 | Unify color palette | Visual consistency (highest UI impact) | 2-3 hours |
| 4.2 | 🟡 P1 | Fix missing font weights | Typography quality | 5 min |
| 4.3 | 🟡 P1 | Fix font family mismatch | Typography consistency | 15 min |
| 4.4 | 🟡 P1 | Unify radius/shadows/spacing | Design system consistency | 2 hours |
| 4.5 | 🟡 P1 | Clean up `!important` overrides | Maintainability | 3-4 hours |
| 4.6 | 🟡 P1 | Implement dark mode | Modern expectation | 1-2 days |
| 2.1 | � Future | SQLite database (deferred) | Keep CSV for now; revisit for mobile/scale | — |
| 2.2 | 🟡 P1 | Extract shared CSV helper | Code deduplication (5 files → 1 helper) | 1 day |
| 2.3 | 🟡 P1 | HTTP interceptor | Error handling | 1 day |
| 2.4 | 🟡 P1 | Fix Python imports | Code quality | 2 hours |
| 3.1 | 🟢 P2 | Split large components | Maintainability | 1-2 days |
| 3.2 | 🟢 P2 | Remove unused dependencies | Bundle size | 30 min |
| 4.7 | 🟢 P2 | Remove emoji from chart axes | Professionalism | 30 min |
| 4.8 | 🟢 P2 | Fix table row hover | Visual bug | 15 min |
| 4.10 | 🟢 P2 | Typography scale tokens | Design system | 1 hour |
| 5.1 | 🟢 P2 | Multi-bank support | User reach | 1-2 weeks |
| 5.2 | 🟢 P2 | Budget tracking UI | Feature gap | 1 week |
| 5.3 | 🟢 P2 | Recurring transaction detection | Smart insights | 1 week |
| 5.4 | 🟢 P2 | Export capabilities | User need | 3-4 days |
| 7.1 | 🔵 P3 | Skeleton loading screens | Perceived performance | 1 day |
| 7.2 | 🔵 P3 | Page transitions | Polish | 1 day |
| 7.3 | 🔵 P3 | Micro-interactions | Delight | 2-3 days |
| 5.5 | 🔵 P3 | Financial goals | Premium feature | 1-2 weeks |
| 5.7 | 🔵 P3 | Family member tagging | Differentiation | 1 week |
| 8.x | 🔵 P3 | Mobile app conversion | Platform expansion | 4-6 weeks |

---

> **Tip:** Start with all P0 items (takes ~2-3 hours total), then tackle item 4.1 (unify colors) for the single biggest visual impact.
