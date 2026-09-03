# Neo-Brutalist Tactical UI Design System — Agent Design Specification

> **Instructions for the AI Agent:**
> You are acting as the Lead Frontend Architect and Design System Specialist. Your task is to style and build the user interface of this project to strictly adhere to the **Neo-Brutalist Tactical Cockpit** design language specified below. 
> Every screen, layout, button, form element, modal, and badge you create or refactor MUST strictly follow the design tokens, typography rules, interaction physics, and component patterns documented in this file.

---

## 1. Design Philosophy & Golden Rules

This design system combines **Neo-Brutalist physical tactility** with a **warm industrial operator aesthetic** (inspired by blueprint diagrams, analog cockpit instruments, and precision hardware).

### Non-Negotiable Rules
1. **High-Contrast Hard Borders**: Every container, card, button, input, and badge must have a crisp, solid border (`2px` or `3px`). Borderless or soft-faded UI is strictly forbidden.
2. **Solid Offset Drop Shadows (No Blur)**: Never use blurred shadows (`box-shadow: 0 4px 6px rgba(0,0,0,0.1)`). All shadows must be hard, solid offset ink shadows:
   - Small: `2px 2px 0px var(--color-dark)`
   - Medium: `4px 4px 0px var(--color-dark)`
   - Large: `6px 6px 0px var(--color-dark)`
3. **Tactile Button Physics (Mechanical Click)**: Interactive elements must feel physical. On hover, items slightly compress or lift; on `:active` (press), they physically depress (`transform: translate(2px, 2px)` or `translate(4px, 4px)`) and the shadow collapses to `0px 0px 0px`.
4. **No Gratuitous Color Gradients**: Keep backgrounds, cards, and buttons flat and solid. Contrast is achieved through warm paper backdrops, deep blueprint ink, and punchy amber/gold accents.
5. **Precision Typography Trio**:
   - **Headings & Actions**: `Space Grotesk` (Geometric, bold, tight tracking `-0.02em`, uppercase for labels).
   - **Body & Content**: `DM Sans` (Clean, legible, medium weight 500).
   - **Data, Stats, Timestamps, Fractions**: `JetBrains Mono` (Terminal / instrument precision).
6. **Structural Background Patterns**: Pages should sit on an engineering graph-paper grid (`.bg-grid`) or comic/halftone dot pattern (`.bg-dots`).
7. **Tight, Intentional Radii**: Use tight geometric rounding (`4px` for small elements, `8px` for cards, `12px` for large containers/dialogs, `9999px` for status pills). Avoid bubbly, overly rounded designs.

---

## 2. Color Palette & Design Tokens

### CSS Custom Properties (`index.css` or `globals.css`)

Copy and paste this root configuration directly into your global stylesheet:

```css
/* ============================================================
   NEO-BRUTALIST TACTICAL COCKPIT DESIGN TOKENS
   ============================================================ */

/* --- Google Fonts Import --- */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
  /* --- Palette (Light Mode - Warm Engineering Parchment) --- */
  --color-bg-base: #E8E2DB;         /* Warm craft paper / parchment */
  --color-bg-surface: #FFFFFF;      /* Crisp white cards & containers */
  --color-bg-elevated: #F5F1EC;     /* Soft warm stone / secondary surface */
  
  --color-accent: #FAB95B;          /* Industrial Amber / Golden Mustard */
  --color-accent-hover: #E8A84A;    /* Darkened Amber */
  --color-dark: #1A3263;            /* Deep Blueprint Navy / Heavy Ink */
  --color-muted: #547792;           /* Slate Steel Blue */
  --color-border: #0F172A;          /* High-contrast solid border ink */
  
  --color-text-primary: #1A3263;    /* Main reading text */
  --color-text-secondary: #547792;  /* Subtitles & metadata */
  --color-text-muted: #8A9BB5;      /* Inactive & placeholder text */
  --color-text-on-accent: #1A3263;  /* High readability on yellow */
  --color-text-on-dark: #E8E2DB;    /* Light text on dark buttons */
  
  --color-success: #4CAF50;         /* Verified / completed green */
  --color-danger: #E53935;          /* Critical alert / destructive red */
  --color-warning: #FAB95B;         /* Warning amber */

  /* --- Typography --- */
  --font-heading: 'Space Grotesk', system-ui, -apple-system, sans-serif;
  --font-body: 'DM Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;

  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 2rem;      /* 32px */
  --text-4xl: 2.5rem;    /* 40px */

  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;

  --tracking-tight: -0.02em;
  --tracking-normal: 0;
  --tracking-wide: 0.05em;

  /* --- Spacing Scale --- */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* --- Borders & Radii --- */
  --border-thin: 2px solid var(--color-border);
  --border-thick: 3px solid var(--color-border);
  --border-accent: 3px solid var(--color-dark);

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* --- Hard Offset Shadows --- */
  --shadow-sm: 2px 2px 0px var(--color-dark);
  --shadow-md: 4px 4px 0px var(--color-dark);
  --shadow-lg: 6px 6px 0px var(--color-dark);
  --shadow-pressed: 0px 0px 0px var(--color-dark);

  /* --- Layout Constants --- */
  --rail-width-collapsed: 72px;
  --rail-width-expanded: 220px;
  --tab-bar-height: 64px;
  --header-height: 56px;
  --content-max-width: 860px;

  /* --- Animation Durations --- */
  --transition-fast: 120ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 350ms ease;
  --transition-bounce: 200ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* --- Dark Theme Overrides ([data-theme="dark"]) --- */
[data-theme="dark"] {
  --color-bg-base: #1A3263;         /* Deep Blueprint Navy */
  --color-bg-surface: #1E3A6F;      /* Navy Card Surface */
  --color-bg-elevated: #24427A;     /* Elevated Slate Navy */
  --color-text-primary: #E8E2DB;    /* Parchment text */
  --color-text-secondary: #B0BDD0;  /* Cool Slate */
  --color-text-muted: #7A8DA8;
  --color-border: #E8E2DB;          /* High contrast pale border */
  --shadow-sm: 2px 2px 0px rgba(232, 226, 219, 0.35);
  --shadow-md: 4px 4px 0px rgba(232, 226, 219, 0.35);
  --shadow-lg: 6px 6px 0px rgba(232, 226, 219, 0.35);
  --shadow-pressed: 0px 0px 0px rgba(232, 226, 219, 0.35);
}
```

---

## 3. Tailwind CSS Configuration (If Project Uses Tailwind)

If your new project uses Tailwind CSS, extend `tailwind.config.js` with these values:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        base: '#E8E2DB',
        surface: '#FFFFFF',
        elevated: '#F5F1EC',
        accent: {
          DEFAULT: '#FAB95B',
          hover: '#E8A84A',
        },
        dark: '#1A3263',
        muted: '#547792',
        border: '#0F172A',
      },
      fontFamily: {
        heading: ['Space Grotesk', 'system-ui', 'sans-serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'neo-sm': '2px 2px 0px #1A3263',
        'neo-md': '4px 4px 0px #1A3263',
        'neo-lg': '6px 6px 0px #1A3263',
        'neo-dark-sm': '2px 2px 0px rgba(232, 226, 219, 0.35)',
        'neo-dark-md': '4px 4px 0px rgba(232, 226, 219, 0.35)',
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
      borderWidth: {
        '2': '2px',
        '3': '3px',
      }
    },
  },
  plugins: [],
}
```

---

## 4. Background Engineering Textures

Include these utility classes in your CSS for page containers:

```css
/* Graph paper blueprint grid (24px x 24px) */
.bg-grid {
  background-image:
    linear-gradient(to right, rgba(84, 119, 146, 0.08) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(84, 119, 146, 0.08) 1px, transparent 1px);
  background-size: 24px 24px;
  background-position: center center;
}

[data-theme="dark"] .bg-grid {
  background-image:
    linear-gradient(to right, rgba(232, 226, 219, 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(232, 226, 219, 0.06) 1px, transparent 1px);
}

/* Halftone / Dot pattern (16px x 16px) */
.bg-dots {
  background-image: radial-gradient(circle, rgba(84, 119, 146, 0.12) 1px, transparent 1px);
  background-size: 16px 16px;
}

[data-theme="dark"] .bg-dots {
  background-image: radial-gradient(circle, rgba(232, 226, 219, 0.08) 1px, transparent 1px);
}
```

---

## 5. UI Component Catalog & Code Specifications

### 5.1 Buttons

Buttons must always display an uppercase bold label in `Space Grotesk`, with crisp borders and tactile click depression.

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  font-family: var(--font-heading);
  font-weight: var(--weight-semibold);
  font-size: var(--text-sm);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  border-radius: var(--radius-sm);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast), background-color var(--transition-fast);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

/* Primary Button (Industrial Yellow Accent) */
.btn-primary {
  background-color: var(--color-accent);
  color: var(--color-text-on-accent);
  border: var(--border-accent);
  box-shadow: var(--shadow-md);
}

.btn-primary:hover {
  background-color: var(--color-accent-hover);
  transform: translate(1px, 1px);
  box-shadow: 3px 3px 0px var(--color-dark);
}

.btn-primary:active {
  transform: translate(4px, 4px);
  box-shadow: var(--shadow-pressed);
}

/* Secondary Button (Surface White) */
.btn-secondary {
  background-color: var(--color-bg-surface);
  color: var(--color-text-primary);
  border: var(--border-thin);
  box-shadow: var(--shadow-sm);
}

.btn-secondary:hover {
  background-color: var(--color-bg-elevated);
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0px var(--color-dark);
}

.btn-secondary:active {
  transform: translate(2px, 2px);
  box-shadow: var(--shadow-pressed);
}

/* Danger Button (Alert Red) */
.btn-danger {
  background-color: var(--color-danger);
  color: #FFFFFF;
  border: var(--border-accent);
  box-shadow: var(--shadow-sm);
}

.btn-danger:hover {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0px var(--color-dark);
}

.btn-danger:active {
  transform: translate(2px, 2px);
  box-shadow: var(--shadow-pressed);
}

/* Ghost Button */
.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
  border: 2px solid transparent;
}

.btn-ghost:hover {
  color: var(--color-text-primary);
  background-color: var(--color-bg-elevated);
}

/* Square Icon Button */
.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: var(--radius-sm);
  border: var(--border-thin);
  background-color: var(--color-bg-surface);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background-color: var(--color-bg-elevated);
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0px var(--color-dark);
}

.btn-icon:active {
  transform: scale(0.92);
}
```

---

### 5.2 Cards & Containers

```css
/* Standard Content Card */
.card {
  background-color: var(--color-bg-surface);
  border: var(--border-thin);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: var(--space-4);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.card:hover {
  transform: translate(-1px, -1px);
  box-shadow: var(--shadow-md);
}

/* Accent Card (Highlight / Banner) */
.card-accent {
  background-color: var(--color-accent);
  border: var(--border-accent);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: var(--space-4);
  color: var(--color-text-on-accent);
}

/* Metric / Operator Stat Card */
.stat-card {
  padding: var(--space-4);
  border: var(--border-thick);
  border-radius: var(--radius-lg);
  background: var(--color-bg-elevated);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: var(--weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-muted);
}

.stat-value {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 900;
  color: var(--color-text-primary);
  line-height: 1;
}
```

---

### 5.3 Form Inputs & Controls

```css
.input, .textarea, .select {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-body);
  font-size: var(--text-base);
  color: var(--color-text-primary);
  background-color: var(--color-bg-surface);
  border: var(--border-thin);
  border-radius: var(--radius-sm);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  box-sizing: border-box;
}

.input:focus, .textarea:focus, .select:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(250, 185, 91, 0.4);
}

.input::placeholder, .textarea::placeholder {
  color: var(--color-text-muted);
}

.field-label {
  display: block;
  font-family: var(--font-heading);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}
```

#### Custom Neo-Brutalist Checkbox
Square, bold 3px border, fills with Amber and shows a bold check icon:

```tsx
// React example
export function Checkbox({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <div
      onClick={onChange}
      className={`checkbox ${checked ? 'checked' : ''}`}
      role="checkbox"
      aria-checked={checked}
    >
      {checked && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      )}
    </div>
  );
}
```

```css
.checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  min-width: 28px;
  border: var(--border-thick);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg-surface);
  cursor: pointer;
  transition: background-color var(--transition-fast), transform var(--transition-fast);
  flex-shrink: 0;
}

.checkbox:hover {
  background-color: var(--color-bg-elevated);
  transform: scale(1.05);
}

.checkbox:active {
  transform: scale(0.92);
}

.checkbox.checked {
  background-color: var(--color-accent);
  border-color: var(--color-dark);
}

.checkbox.checked svg {
  color: var(--color-dark);
}
```

---

### 5.4 Badges, Chips & Status Pills

```css
/* Uppercase Category Chip */
.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  font-family: var(--font-heading);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  white-space: nowrap;
  user-select: none;
}

/* Priority Badges (Mono) */
.chip-critical {
  border-color: var(--color-danger);
  background-color: rgba(229, 57, 53, 0.12);
  color: var(--color-danger);
}

.chip-high {
  border-color: var(--color-accent);
  background-color: rgba(250, 185, 91, 0.15);
  color: var(--color-text-primary);
}

.chip-low {
  border-color: var(--color-muted);
  background-color: transparent;
  color: var(--color-muted);
}

/* Circular Pulsing Notification Badge */
.notif-badge {
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: #EF4444;
  color: white;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 900;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--color-bg-surface);
  line-height: 1;
  animation: badgePulse 2s ease-in-out infinite;
}

@keyframes badgePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
```

---

### 5.5 Progress Bars (No Gradients, Solid Precision Fill)

```html
<div class="progress-container">
  <div class="progress-fill" style="width: 75%;"></div>
  <span class="progress-label">75% (3/4 COMPLETED)</span>
</div>
```

```css
.progress-container {
  width: 100%;
  height: 24px;
  border: var(--border-thin);
  border-radius: var(--radius-sm);
  background-color: var(--color-bg-surface);
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background-color: var(--color-accent);
  transition: width var(--transition-slow);
}

.progress-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: var(--font-mono);
  font-weight: var(--weight-semibold);
  font-size: var(--text-xs);
  color: var(--color-text-primary);
  white-space: nowrap;
}
```

---

### 5.6 Segmented Tabs & Stepper Controls

```css
.tab-list {
  display: flex;
  gap: var(--space-2);
  border-bottom: 3px solid var(--color-border);
  padding-bottom: var(--space-2);
  margin-bottom: var(--space-4);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--color-text-secondary);
  background: transparent;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
}

.tab-btn.active {
  color: var(--color-text-on-accent);
  background: var(--color-accent);
  border-color: var(--color-border);
  box-shadow: var(--shadow-sm);
}
```

---

### 5.7 Dialogs, Modals & Bottom Sheets

- **Mobile Viewport (< 768px)**: Bottom Sheet that slides up from screen edge.
- **Desktop Viewport (>= 768px)**: Centered dialog with 3px thick border, 6px hard shadow, and bouncy scale animation.

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(26, 50, 99, 0.45);
  backdrop-filter: blur(2px);
  z-index: 100;
  animation: fadeIn var(--transition-fast) ease;
}

.modal-dialog {
  position: fixed;
  z-index: 101;
  background-color: var(--color-bg-surface);
  border: var(--border-thick);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6);
  box-sizing: border-box;
}

/* Mobile: Bottom Sheet */
@media (max-width: 767px) {
  .modal-dialog {
    bottom: 0;
    left: 0;
    right: 0;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    border-bottom: none;
    max-height: 90dvh;
    overflow-y: auto;
    animation: slideInUp var(--transition-bounce);
  }
}

/* Desktop: Center Modal */
@media (min-width: 768px) {
  .modal-dialog {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 520px;
    max-width: 90vw;
    border-radius: var(--radius-lg);
    animation: scaleIn var(--transition-bounce);
  }
}
```

---

## 6. Layout Shell: Dual Cockpit Architecture

This system uses a dedicated, highly ergonomic dual-layout shell:
1. **Desktop (>= 768px)**:
   - Fixed vertical **Side Rail Navigation** (`72px` collapsed, expanding to `220px` on hover or toggle).
   - Thick solid border-right separating navigation from the content.
   - Central container bounded to `--content-max-width: 860px` with margins `0 auto` for focus and reading clarity.
2. **Mobile (< 768px)**:
   - Sticky top **Mobile Header** (`56px` high, 3px border-bottom) with brand logo and quick action triggers.
   - Fixed **Bottom Navigation Tab Bar** (`64px` high, 3px border-top) with active top-border indicator tab highlights.
   - Main content padded at bottom: `padding-bottom: calc(var(--tab-bar-height) + var(--space-4))`.

### App Layout HTML / React Template

```tsx
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout bg-grid">
      {/* Desktop Side Rail */}
      <aside className="side-rail hide-mobile">
        <div className="rail-header">
          <div className="rail-logo">⚡</div>
          <span className="rail-brand">PROJECT</span>
        </div>
        <nav className="rail-nav">
          {/* Navigation Items */}
        </nav>
      </aside>

      {/* Mobile Top Header */}
      <header className="mobile-header hide-desktop">
        <div className="mobile-header-brand">
          <div className="mobile-logo">⚡</div>
          <span className="mobile-title">PROJECT</span>
        </div>
      </header>

      {/* Main Routed Content */}
      <main className="main-content">
        <div className="screen-container">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Tab Bar */}
      <nav className="bottom-tab-bar hide-desktop">
        {/* Tab Items */}
      </nav>
    </div>
  );
}
```

---

## 7. Keyframe Animations & Micro-interactions

Always include these keyframes for tactile fluid transitions:

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}

.animate-fade-in { animation: fadeIn var(--transition-normal) ease; }
.animate-fade-in-up { animation: fadeInUp var(--transition-slow) ease; }
.animate-scale-in { animation: scaleIn var(--transition-bounce); }
```

---

## 8. Agent Refactoring & Implementation Checklist

When styling a new screen or refactoring existing components, run through this checklist:

- [ ] **Import Fonts**: Is `@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');` loaded at the top of CSS?
- [ ] **Backgrounds**: Is the page body background `#E8E2DB` with `.bg-grid` engineering grid applied?
- [ ] **Borders**: Does every card, button, and input have a solid `2px` or `3px` solid border using `var(--color-border)` (`#0F172A`)?
- [ ] **Hard Shadows**: Are all soft blur shadows replaced with `2px 2px 0px` or `4px 4px 0px`?
- [ ] **Buttons**: Are primary action buttons colored `#FAB95B` with uppercase `Space Grotesk` font and physical translate `:active` press state?
- [ ] **Inputs**: Are text inputs bordered in 2px/3px ink with an amber focus ring on active?
- [ ] **Numbers & Timestamps**: Are numbers, counters, dates, and metrics rendered in `JetBrains Mono`?
- [ ] **Responsive Navigation**: Does desktop have a side rail and mobile have a bottom tab bar?
