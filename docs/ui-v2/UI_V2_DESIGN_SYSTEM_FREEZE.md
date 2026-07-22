# YGIT UI V2 Design System Freeze Specification

**Document ID:** YGIT-UIV2-DS-001<br>
**Version:** 0.1.0<br>
**Status:** Draft for Review<br>
**Owner:** YGIT Platform<br>
**Product:** YGIT<br>
**Company:** Vib Tools<br>
**Depends On:**<br>
- `UI_V2_MASTER_ARCHITECTURE.md`<br>
- `UI_V2_API_ARCHITECTURE.md`<br>

**Last Updated:** 2026-07-22<br>

---

## Revision History

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-22 | Draft for Review | Initial UI V2 design system freeze specification |

---

## 1. Purpose

This document defines and freezes the visual design system for YGIT UI V2.

Its purpose is to ensure that every current and future YGIT page, feature, button, form, table, card, modal, status, empty state, and navigation element follows one consistent professional system.

This specification is intended to allow any YGIT developer to build or extend UI V2 without inventing new visual rules.

The design system must remain:

```text
Professional
Premium
Modern
Developer First
Fast
Reliable
Minimal
Enterprise Grade
Open Source
Focused
```

It must not appear:

```text
Colorful
Fancy
Startup-like
Gaming-oriented
Playful
Cartoon-like
Material Design-like
Bootstrap-template-like
```

---

## 2. Product Feeling

YGIT must feel like a serious infrastructure product.

The intended product impression is:

```text
GitHub professionalism
+
Vercel simplicity
+
Linear clean typography
+
Cloudflare infrastructure feeling
```

YGIT UI V2 must communicate:

- control;
- trust;
- technical clarity;
- deployment readiness;
- infrastructure ownership;
- predictable behavior;
- developer efficiency;
- low visual noise.

The product must never feel decorative before it feels operational.

---

## 3. Design Philosophy

### 3.1 Primary Direction

```text
Dark First
Developer First
Minimal
Professional
Fast
Git Native
Cloud Native
Keyboard Friendly
Responsive
```

### 3.2 Dark Mode Position

Dark mode is not an optional theme for the initial release.

```text
Dark mode is the product.
```

The dark theme is the only frozen production theme for UI V2 initial release.

A light theme may be introduced later through a separately approved design-system revision.

### 3.3 Visual Restraint

UI V2 must avoid:

- visual decoration without function;
- oversized hero typography;
- excessive whitespace;
- excessive density;
- glassmorphism;
- gradients used as decoration;
- glowing borders;
- animated backgrounds;
- colorful card collections;
- unnecessary illustrations;
- excessive shadows;
- decorative blur;
- floating layout tricks.

---

## 4. Design System Authority

The design system is implemented through:

```text
Mantine Theme
    ↓
YGIT Semantic Tokens
    ↓
YGIT Shared Components
    ↓
Feature Composition
```

The following are prohibited:

- feature-specific color systems;
- page-specific typography systems;
- duplicated button styles;
- arbitrary inline colors;
- arbitrary spacing values;
- uncontrolled CSS overrides;
- competing global stylesheets;
- visual rules stored inside feature business logic;
- random `z-index` values;
- arbitrary `!important`;
- layout based on absolute positioning.

The UI V2 design-system source of truth will be:

```text
frontend-v2/src/theme/
├── tokens.ts
├── theme.ts
├── components.ts
└── typography.ts
```

---

## 5. Brand Identity

### 5.1 Brand Name

```text
YGIT
```

### 5.2 Product Category

```text
Open Source Deployment Platform
```

### 5.3 Parent Brand

```text
Vib Tools
```

### 5.4 Brand Presentation Rules

YGIT branding must be:

- direct;
- compact;
- technical;
- readable;
- consistent;
- free from decorative distortion.

The logo must not be:

- stretched;
- compressed;
- recolored without approval;
- placed on low-contrast surfaces;
- surrounded by decorative effects;
- animated;
- used as a background pattern.

---

## 6. Logo System

The approved logo asset categories are:

```text
Primary dark-theme logo
Compact logo mark
Favicon
Application icon
Authentication/logo variant where required
```

Initial asset locations:

```text
frontend-v2/public/brand/
├── ygit-logo-dark.svg
├── ygit-logo-compact.svg
├── favicon.svg
├── favicon.ico
└── apple-touch-icon.png
```

Final filenames may reflect existing approved YGIT assets.

### 6.1 Logo Usage

- Sidebar uses the primary dark-theme logo or compact mark according to width.
- Mobile shell may use the compact mark.
- Favicon uses the compact approved brand mark.
- Logo clear space must be at least `8px`.
- Logo must not be placed inside a decorative card.
- Logo height must remain consistent across the application shell.

### 6.2 Logo Sizing

| Context | Approved Size |
|---|---:|
| Full sidebar logo width | 128–156px |
| Compact mark | 28–32px |
| Mobile mark | 28px |
| Favicon source | 32px minimum source |
| Authentication logo | Defined by auth surface, maximum 180px width |

Exact final asset dimensions will be verified during implementation.

---

## 7. Color System

All colors must be represented as semantic tokens.

Feature code must not use raw hex values unless the value is part of an approved token definition.

---

## 8. Core Background Colors

### 8.1 Main Background

```css
#030712
```

Token:

```text
--ygit-color-background
```

Usage:

- application background;
- page canvas;
- navigation shell background where appropriate.

The main background is dark navy, not pure black.

### 8.2 Surface

```css
#111827
```

Token:

```text
--ygit-color-surface
```

Usage:

- cards;
- sidebar sections;
- panels;
- header surfaces;
- tables;
- modals.

### 8.3 Elevated Surface

```css
#0F172A
```

Token:

```text
--ygit-color-surface-elevated
```

Usage:

- dropdowns;
- popovers;
- raised panels;
- modal inner surfaces;
- nested controls.

### 8.4 Input Surface

```css
#070D18
```

Token:

```text
--ygit-color-input
```

Usage:

- inputs;
- selects;
- textareas;
- search controls.

---

## 9. Border Colors

### 9.1 Default Border

```css
rgba(255,255,255,.08)
```

Token:

```text
--ygit-color-border
```

### 9.2 Strong Border

```css
rgba(255,255,255,.14)
```

Token:

```text
--ygit-color-border-strong
```

### 9.3 Focus Border

Focus border uses the approved accent color.

Borders must remain visible but visually quiet.

No component may use a bright border without semantic status meaning.

---

## 10. Brand and Semantic Colors

### 10.1 Primary

```css
#2563EB
```

Token:

```text
--ygit-color-primary
```

Usage:

- primary actions;
- selected navigation;
- selected state;
- primary progress;
- primary links where required.

### 10.2 Primary Hover

```css
#1D4ED8
```

Token:

```text
--ygit-color-primary-hover
```

### 10.3 Accent

```css
#38BDF8
```

Token:

```text
--ygit-color-accent
```

Accent is restricted to:

- focus;
- selection;
- loading;
- highlighted infrastructure state;
- small active indicators.

Accent must not become a second primary color.

### 10.4 Success

```css
#10B981
```

Token:

```text
--ygit-color-success
```

Usage:

- deployment success;
- connected provider;
- healthy service;
- completed operation.

### 10.5 Warning

```css
#F59E0B
```

Token:

```text
--ygit-color-warning
```

Usage:

- deployment blocker;
- reconnect required;
- incomplete configuration;
- pending warning.

### 10.6 Danger

```css
#EF4444
```

Token:

```text
--ygit-color-danger
```

Usage:

- destructive action;
- failed deployment;
- disconnected critical dependency;
- permanent error.

### 10.7 Info

```css
#3B82F6
```

Token:

```text
--ygit-color-info
```

Usage:

- neutral information;
- non-blocking informational notices;
- linked infrastructure state.

---

## 11. Text Colors

Approved text tokens:

| Token | Purpose | Value |
|---|---|---|
| `--ygit-color-text-primary` | Headings and primary content | `#F1F5F9` |
| `--ygit-color-text-secondary` | Standard body content | `#CBD5E1` |
| `--ygit-color-text-muted` | Supporting text | `#94A3B8` |
| `--ygit-color-text-faint` | Captions and inactive metadata | `#64748B` |
| `--ygit-color-text-inverse` | Text on primary buttons | `#FFFFFF` |

Text contrast must remain accessible against approved surfaces.

---

## 12. Color Usage Rules

### Allowed

- semantic status colors;
- primary blue for action;
- accent blue for focus and highlight;
- subtle neutral surfaces;
- subtle status backgrounds.

### Forbidden

- random feature colors;
- rainbow data cards;
- decorative gradients;
- neon colors;
- status colors used without semantic meaning;
- multi-colored buttons;
- arbitrary opacity combinations;
- low-contrast muted text.

Status color must never be the only indicator. A label, icon, or status text must accompany it.

---

## 13. Typography System

Only two font families are approved.

### 13.1 Primary Font

```text
Inter
```

Usage:

- all application UI;
- headings;
- body;
- navigation;
- buttons;
- forms;
- tables;
- modals.

### 13.2 Code Font

```text
JetBrains Mono
```

Usage:

- commit SHA;
- repository path;
- build command;
- environment key name;
- log excerpt;
- code;
- command;
- technical identifiers where monospace improves readability.

### 13.3 Font Fallbacks

```css
Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

```css
"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace
```

No additional font family is approved.

---

## 14. Font Weights

Approved weights:

```text
400
500
600
700
```

Usage:

| Weight | Usage |
|---:|---|
| 400 | Body and supporting copy |
| 500 | Navigation, inputs, secondary emphasis |
| 600 | Buttons, card titles, section labels |
| 700 | Page headings and strong status emphasis |

Weights above `700` are prohibited.

---

## 15. Typography Scale

YGIT avoids oversized hero typography.

### 15.1 Heading Scale

| Semantic Role | Size | Line Height | Weight |
|---|---:|---:|---:|
| H1 | 36px | 1.2 | 700 |
| H2 | 30px | 1.25 | 700 |
| H3 | 24px | 1.3 | 600 |
| H4 | 20px | 1.35 | 600 |

These headings are available across the ecosystem but should be used sparingly inside the dashboard.

### 15.2 Dashboard-Specific Roles

| Role | Size | Line Height | Weight |
|---|---:|---:|---:|
| Dashboard page title | 28px | 1.25 | 700 |
| Dashboard section title | 22px | 1.3 | 600 |
| Card title | 18px | 1.35 | 600 |
| Body | 16px | 1.5 | 400 |
| Small | 14px | 1.5 | 400 |
| Caption | 13px | 1.45 | 400 |
| Badge | 12px | 1.2 | 600 |
| Navigation | 14px | 1.4 | 500 |
| Sidebar item | 14px | 1.4 | 500 |
| Button | 14px | 1.2 | 600 |
| Input | 14px | 1.4 | 400 |
| Code | 13px | 1.5 | 400 |

### 15.3 Typography Interpretation

The `H1–H4` scale is the global semantic heading system.

The `Dashboard page title` is a specialized application-shell role and intentionally uses `28px` to maintain compact information density.

Dashboard pages must not use `36px` headings unless a future approved page type explicitly requires it.

---

## 16. Line Height

Default body line height:

```text
1.5
```

Approved heading line heights are defined in the typography tables.

Dense data tables may use:

```text
1.4
```

Code and logs may use:

```text
1.5
```

---

## 17. Letter Spacing

Default:

```text
normal
```

Allowed exception:

```text
H1: -0.02em
Dashboard page title: -0.02em
```

Uppercase technical labels may use:

```text
0.08em
```

Uppercase text must remain limited to:

- eyebrow labels;
- table metadata labels;
- small infrastructure labels;
- compact status headings.

Body text and navigation must not use wide letter spacing.

---

## 18. Spacing System

YGIT uses an `8px` grid with approved intermediate values.

Approved spacing scale:

```text
4
8
12
16
24
32
48
64
96
```

Semantic mapping:

| Token | Value | Typical Use |
|---|---:|---|
| `space-1` | 4px | icon/text micro-gap |
| `space-2` | 8px | compact internal gap |
| `space-3` | 12px | form/control gap |
| `space-4` | 16px | card internal gap |
| `space-5` | 24px | section gap |
| `space-6` | 32px | page subsection spacing |
| `space-7` | 48px | major section spacing |
| `space-8` | 64px | large layout separation |
| `space-9` | 96px | rare marketing-level spacing |

Dashboard pages should primarily use `8–32px`.

The `64px` and `96px` values must not be used for routine dashboard card spacing.

---

## 19. Border Radius

Approved radii:

| Component | Radius |
|---|---:|
| Card | 12px |
| Panel | 12px |
| Button | 10px |
| Input | 10px |
| Select | 10px |
| Textarea | 10px |
| Dropdown | 12px |
| Modal | 16px |
| Drawer | 16px where visible |
| Badge | 999px |
| Tooltip | 8px |
| Code block | 10px |

No feature may invent a new radius without design-system revision.

---

## 20. Shadow System

Shadows must remain minimal.

### 20.1 Default Shadow

```css
0 1px 2px rgba(0,0,0,.15)
```

### 20.2 Hover or Elevated Shadow

```css
0 8px 24px rgba(0,0,0,.20)
```

### 20.3 Rules

- cards do not require hover shadows unless interactive;
- buttons do not use large shadows;
- modals may use a controlled elevated shadow;
- no glowing shadows;
- no colored shadows;
- no permanent deep elevation;
- no glassmorphism.

---

## 21. Icon System

Only one icon family is approved:

```text
Lucide
```

Rules:

- outline icons only;
- consistent stroke width;
- no mixed icon libraries;
- no filled icons except approved status marks where necessary;
- icons must not replace essential text;
- icon-only buttons require accessible labels;
- decorative icons use `aria-hidden`;
- icon sizes follow the approved scale.

Approved icon sizes:

```text
14px
16px
18px
20px
24px
```

Routine dashboard icons should use `16px` or `18px`.

---

## 22. Motion System

### 22.1 Allowed Motion

```text
Fade
Slide
Hover transition
Opacity transition
Small color transition
Small border transition
```

### 22.2 Forbidden Motion

```text
Bounce
Zoom
Rotate
Particles
Background animation
Heavy motion
Continuous pulse
Decorative parallax
```

### 22.3 Timing

Approved duration range:

```text
120ms–200ms
```

Default:

```text
150ms
```

Approved easing:

```css
ease
ease-out
```

Motion must respect reduced-motion preferences.

---

## 23. UI Density

Approved density:

```text
Medium
```

Target feeling:

```text
GitHub   ✅
Linear   ✅
Vercel   ✅
```

Avoid:

```text
Notion-style excessive whitespace
Bootstrap-dashboard crowding
```

Density rules:

- controls remain easy to click;
- data remains compact;
- cards should not be oversized;
- page sections should not be separated by large blank areas;
- tables may be dense but readable;
- mobile layouts may increase vertical spacing slightly.

---

## 24. Control Dimensions

| Control | Height |
|---|---:|
| Primary button | 40px |
| Secondary button | 40px |
| Compact button | 32px |
| Icon button | 40px |
| Input | 40px |
| Select | 40px |
| Search | 40px |
| Textarea minimum | 96px |
| Navigation row | 36–40px |
| Table row | 44–48px |

Large dashboard buttons above `44px` are not approved unless used in a dedicated onboarding state.

---

## 25. Button System

Approved variants:

```text
Primary
Secondary
Ghost
Danger
Link
Icon
```

Approved states:

```text
Default
Hover
Focus
Disabled
Loading
Active
```

### 25.1 Primary Button

Usage:

- one main action per local section;
- create project;
- continue;
- confirm a safe primary flow.

Primary actions must not be repeated excessively across the same viewport.

### 25.2 Secondary Button

Usage:

- supporting actions;
- open;
- manage;
- refresh;
- cancel where neutral.

### 25.3 Ghost Button

Usage:

- low-emphasis actions;
- toolbar actions;
- optional navigation actions.

### 25.4 Danger Button

Usage:

- disconnect;
- delete;
- remove;
- irreversible action.

Danger actions require confirmation.

### 25.5 Button Rules

- no feature-specific button colors;
- no gradients;
- no oversized pill buttons;
- no decorative icons without text for important actions;
- loading state must preserve button width when practical;
- disabled state must remain readable;
- destructive buttons must not appear primary-blue.

---

## 26. Form System

Approved form controls:

```text
TextInput
Textarea
Select
MultiSelect where justified
Checkbox
Radio
Switch
PasswordInput where required
SearchInput
```

Rules:

- every control requires a label;
- placeholder is not a label;
- helper text is optional but must be concise;
- validation message appears near the control;
- required fields are clearly indicated;
- backend validation remains authoritative;
- form spacing uses the approved grid;
- field groups use consistent widths;
- submit controls appear at the end of the form;
- destructive forms require confirmation.

---

## 27. Card and Panel System

### 27.1 Card

Use for:

- project summary;
- deployment summary;
- provider summary;
- metric;
- independent actionable content.

### 27.2 Panel

Use for:

- larger page section;
- table container;
- project details;
- settings group;
- combined content region.

### 27.3 Rules

- cards use `12px` radius;
- cards use subtle border;
- cards use minimal shadow;
- cards do not use glass effects;
- cards remain in normal document flow;
- cards must not be positioned absolutely for primary layout;
- cards require consistent internal spacing;
- clickable cards require visible hover and focus states;
- non-clickable cards must not simulate clickability.

---

## 28. Status System

Approved semantic statuses:

```text
Neutral
Info
Success
Warning
Danger
```

Status components:

```text
StatusBadge
StatusDot
StatusBanner
InlineStatus
```

Rules:

- status includes text;
- color is supplementary;
- status labels use stable wording;
- unknown states render as neutral;
- success is not used for incomplete operations;
- warning is used for recoverable blockers;
- danger is used for failure or destructive risk.

Examples:

```text
Connected
Reconnect required
Deploy ready
Deployment blocked
Running
Completed
Failed
```

---

## 29. Navigation System

### 29.1 Primary Sidebar

The sidebar is the primary application navigation.

Initial navigation categories may include:

```text
Dashboard
Projects
Deployments
Templates
Apps
Connected Accounts
Settings
```

Actual feature availability remains controlled by approved product scope and backend capability.

### 29.2 Topbar

The topbar may include:

```text
Page title context
Search
Notifications
Workspace selector
Primary page action
Profile control
```

### 29.3 Rules

- selected navigation uses primary blue;
- hover is subtle;
- icons use Lucide outline;
- labels remain visible on desktop;
- compact mode may use icon plus tooltip;
- mobile uses an approved drawer or compact navigation pattern;
- navigation must remain keyboard accessible;
- no nested navigation deeper than necessary.

---

## 30. Layout System

Primary layout:

```text
┌──────────────────────────────────────────────┐
│ Logo                    Search      Profile │
├──────────────┬───────────────────────────────┤
│              │                               │
│ Dashboard    │ Page Content                  │
│ Projects     │                               │
│ Deployments  │ Panels / Cards / Tables       │
│ Templates    │                               │
│ Apps         │                               │
│ Accounts     │                               │
│ Settings     │                               │
│              │                               │
└──────────────┴───────────────────────────────┘
```

### 30.1 Desktop Shell

- fixed or sticky sidebar;
- scrollable main content;
- topbar inside main region;
- consistent maximum content width;
- no horizontal overflow;
- normal document flow.

### 30.2 Main Content Width

Approved maximum page content width:

```text
1440px
```

Dense table pages may use the full available width inside this boundary.

### 30.3 Sidebar Width

Approved desktop sidebar width:

```text
240px
```

Compact future mode may be introduced separately.

### 30.4 Topbar Height

Approved topbar minimum height:

```text
64px
```

---

## 31. Responsive Breakpoints

Approved breakpoints:

| Name | Width |
|---|---:|
| `xs` | 36em / 576px |
| `sm` | 48em / 768px |
| `md` | 62em / 992px |
| `lg` | 75em / 1200px |
| `xl` | 88em / 1408px |

These align with the selected UI framework and may be represented through Mantine theme configuration.

### 31.1 Responsive Rules

- desktop navigation may become a drawer below `md`;
- multi-column grids collapse progressively;
- tables may scroll horizontally only when unavoidable;
- primary content must never depend on absolute positioning;
- buttons may wrap on small screens;
- page headers stack on small screens;
- forms become single-column on small screens;
- cards remain full-width inside mobile flow;
- no content may be clipped by hidden overflow.

---

## 32. Table System

Tables are required for enterprise-grade data presentation.

Approved table features:

```text
Header
Rows
Empty state
Loading state
Sorting indicator
Pagination
Row action menu
Status cell
Technical identifier cell
Responsive overflow
```

Rules:

- table headers are concise;
- text alignment is consistent;
- numeric values align predictably;
- technical identifiers may use JetBrains Mono;
- full-row click is used only when clearly indicated;
- action menus remain explicit;
- tables must not become colorful;
- sticky headers may be used on long tables;
- zebra striping is not required.

---

## 33. Modal, Drawer, and Popover System

### 33.1 Modal

Use for:

- confirmation;
- focused form;
- critical details;
- short multi-step action.

### 33.2 Drawer

Use for:

- mobile navigation;
- contextual details;
- secondary configuration;
- narrow responsive workflows.

### 33.3 Popover and Menu

Use for:

- compact action menus;
- filters;
- small contextual choices.

Rules:

- modal radius is `16px`;
- focus must be trapped correctly;
- escape closes non-destructive dialogs;
- destructive confirmations remain explicit;
- large pages must not be placed inside modals;
- modal nesting is prohibited;
- popovers must remain inside viewport.

---

## 34. Feedback States

Every page and feature must support:

```text
Loading
Empty
Success
Warning
Error
Partial data
Unauthorized
Not found
```

### 34.1 Loading

Use:

- skeleton;
- compact spinner;
- progress text.

Avoid:

- full-page blocking spinner for optional data;
- decorative animation.

### 34.2 Empty State

Must contain:

- concise title;
- explanation;
- one clear next action when available.

### 34.3 Error State

Must contain:

- safe message;
- recovery action where appropriate;
- request ID when useful for support;
- no raw backend object;
- no stack trace.

---

## 35. Code and Technical Data

Use JetBrains Mono for:

- repository URL where technical scanning benefits;
- commit SHA;
- branch;
- environment key;
- build command;
- output directory;
- deployment ID;
- logs;
- commands.

Rules:

- code text must remain readable;
- long values support copy;
- long identifiers use truncation with full value available;
- sensitive values must never be displayed;
- secrets must not be partially revealed unless an approved security pattern exists.

---

## 36. Search and Filter System

Search fields:

- use `40px` height;
- use Lucide search icon;
- provide clear button when useful;
- support keyboard focus;
- debounce remote search;
- preserve meaningful route state.

Filter controls:

- use approved select, menu, or chips;
- remain semantically neutral;
- show active-filter count when helpful;
- provide clear-all action;
- do not use bright colors for ordinary filters.

---

## 37. Tooltip System

Tooltips are allowed for:

- icon-only actions;
- truncated technical values;
- compact infrastructure explanations;
- keyboard shortcut hints.

Tooltips must not:

- contain critical instructions;
- replace labels;
- contain large blocks of content;
- appear without hover or keyboard focus support.

---

## 38. Notification System

Approved notification types:

```text
Success
Info
Warning
Error
```

Rules:

- concise message;
- no decorative animation;
- dismissible where appropriate;
- important failures remain visible in page context;
- notifications do not replace form validation;
- deployment status is not communicated only through a transient toast.

---

## 39. Accessibility Requirements

UI V2 must support:

- keyboard navigation;
- visible focus;
- semantic headings;
- accessible labels;
- status announcements;
- sufficient contrast;
- reduced motion;
- screen-reader-friendly controls;
- proper modal focus management;
- accessible error messages;
- non-color status indicators.

Minimum target:

```text
WCAG 2.1 AA
```

No component is considered approved if it is visually correct but inaccessible.

---

## 40. Design System Component Inventory

The initial frozen component inventory is:

### Actions

```text
Button
IconButton
CopyButton
ActionMenu
```

### Forms

```text
TextInput
Textarea
Select
Checkbox
Radio
Switch
SearchInput
FormField
FormError
```

### Navigation

```text
AppShell
Sidebar
Topbar
NavItem
Breadcrumb
Tabs
MobileNavigation
```

### Surfaces

```text
Card
Panel
Modal
Drawer
Popover
Tooltip
DropdownMenu
```

### Data Display

```text
Badge
StatusBadge
StatusDot
MetricCard
DataTable
Pagination
KeyValueList
CodeValue
Timeline
```

### Feedback

```text
Alert
Notification
LoadingState
Skeleton
EmptyState
ErrorState
PartialDataState
ConfirmationDialog
```

### Page Composition

```text
PageHeader
SectionHeader
PageContainer
PageActions
FilterBar
Toolbar
```

No new foundational component should be created before checking this inventory.

---

## 41. Component Variant Governance

A new variant requires:

1. a documented use case;
2. confirmation that an existing variant is insufficient;
3. accessibility review;
4. design-system update;
5. component test;
6. visual approval.

Feature developers may compose components but must not silently create new design-system variants.

---

## 42. Admin-Controlled Theme Boundary

UI V2 initial release uses code-defined theme values.

The following may be exposed to an admin configuration system later:

```text
Primary color preset
Logo reference
Favicon reference
Approved font preset
Density preset
Radius preset
```

The following remain prohibited:

```text
Arbitrary CSS
Arbitrary HTML
Arbitrary JavaScript
Page layout JSON
Per-component style editing
Raw font URL
Responsive breakpoint editing
Route editing
Business-logic editing
```

This preserves UI stability and prevents UI V2 from becoming a CMS or website builder.

---

## 43. Asset Management

Brand assets are source-controlled initially.

Future approved external asset storage may use Cloudflare R2, but UI V2 must receive only safe published references.

Rules:

- assets require versioning;
- missing assets use safe fallback;
- unsupported file types are rejected;
- logos require transparent or approved background;
- favicon changes require rebuild or approved asset-version update;
- no remote arbitrary asset URL may be injected into the interface.

---

## 44. CSS and Styling Restrictions

Prohibited:

```text
Global feature-specific selectors
Unscoped overrides
Repeated raw hex values
Random spacing values
Absolute positioning for primary layout
Negative margins for structural layout
Hidden overflow used to conceal layout defects
Arbitrary z-index
!important outside approved framework integration
Inline CSS copied between pages
Mutable permanently named production CSS
```

Approved:

```text
Mantine theme tokens
Mantine component props
Shared YGIT wrappers
Scoped CSS modules
Semantic class names
Normal Grid/Flex layout
Content-hashed build assets
```

---

## 45. Visual Quality Gate

A component or page is not complete until it passes:

```text
Desktop review
Tablet review
Mobile review
Keyboard review
Loading-state review
Empty-state review
Error-state review
Long-content review
No-overflow review
No-console-error review
```

Final automated browser and screenshot requirements will be defined in:

```text
UI_V2_TESTING_AND_RELEASE_GATE.md
```

---

## 46. Page Design Standard

Every page must use:

```text
AppShell
  ↓
PageHeader
  ↓
Optional Toolbar / FilterBar
  ↓
Content Sections
  ↓
Loading / Empty / Error handling
```

Every page must define:

- title;
- short description where necessary;
- primary action;
- loading state;
- empty state;
- error state;
- responsive behavior;
- keyboard behavior;
- API state ownership;
- acceptance criteria.

Pages must not introduce:

- unique navigation;
- unique typography scales;
- unique colors;
- unique button systems;
- unique spacing systems.

---

## 47. Initial Page Visual Direction

### Dashboard

```text
Operational overview
Compact metrics
Recent projects
Recent deployments
Provider status
Platform status
No oversized hero
```

### Projects

```text
List-first
Clear create action
Readable project status
Compact repository metadata
```

### Project Details

```text
Structured technical information
Readable readiness blockers
Repository Analysis summary
Deployment actions controlled by backend readiness
```

### Deployments

```text
Timeline and table clarity
Status-first presentation
Technical identifiers available
Logs separated from summary
```

### Connected Accounts

```text
Provider identity
Connection status
Permissions summary
Last sync
Explicit manage/disconnect actions
```

### Settings

```text
Grouped configuration
Clear ownership
No decorative cards
Safe confirmations
```

---

## 48. Prohibited Visual Outcomes

YGIT UI V2 must not resemble:

```text
A generic Bootstrap admin template
A Material Design dashboard
A colorful startup analytics dashboard
A gaming control panel
A no-code website builder
A CMS theme editor
A glassmorphism concept
A marketing landing page inside the dashboard
```

---

## 49. Design Freeze Governance

Document lifecycle:

```text
Draft
  ↓
Review
  ↓
Approved
  ↓
Frozen
  ↓
Implementation
```

After freeze, changes require:

1. change request;
2. reason;
3. affected tokens or components;
4. responsive impact;
5. accessibility impact;
6. migration impact;
7. updated revision history;
8. explicit approval.

---

## 50. Acceptance Criteria

This document is ready for approval when the following are accepted:

- dark-first product direction;
- background `#030712`;
- surface `#111827`;
- subtle border `rgba(255,255,255,.08)`;
- primary `#2563EB`;
- primary hover `#1D4ED8`;
- accent `#38BDF8`;
- success `#10B981`;
- warning `#F59E0B`;
- danger `#EF4444`;
- info `#3B82F6`;
- Inter as primary font;
- JetBrains Mono as code font;
- weights limited to `400–700`;
- global heading scale `36/30/24/20`;
- dashboard page title `28px`;
- section title `22px`;
- card title `18px`;
- body `16px`;
- medium density;
- 8px spacing system;
- approved radii;
- minimal shadows;
- Lucide-only icon system;
- restrained motion;
- `240px` sidebar;
- `1440px` maximum content width;
- Mantine as component foundation;
- no arbitrary database-driven UI;
- no absolute positioning for primary layout;
- no feature-specific design systems.

---

## 51. Frozen Rules After Approval

After approval:

1. Dark is the only initial production theme.
2. Inter and JetBrains Mono are the only approved fonts.
3. The approved color tokens are mandatory.
4. The approved spacing scale is mandatory.
5. The approved typography scale is mandatory.
6. Weights above `700` are prohibited.
7. Lucide is the only icon family.
8. Glassmorphism is prohibited.
9. Decorative gradients are prohibited.
10. Primary layout uses normal document flow.
11. Cards, buttons, inputs, modals, and badges use approved radii.
12. Motion remains subtle and bounded.
13. Medium density is mandatory.
14. Mantine primitives are preferred.
15. Shared YGIT components are required for repeated patterns.
16. Feature-specific button, color, or typography systems are prohibited.
17. Arbitrary CSS, HTML, and JavaScript configuration is prohibited.
18. New design variants require formal review.
19. All pages must support loading, empty, and error states.
20. All approved UI must meet accessibility requirements.

---

## 52. Next Documentation Step

After approval, the next document is:

```text
YGIT UI V2 Migration Plan
```

No UI V2 implementation is authorized by this draft.

---

## 53. Approval Record

| Role | Name | Decision | Date |
|---|---|---|---|
| Product Owner | Pending | Pending | Pending |
| Design Owner | Pending | Pending | Pending |
| Architecture Owner | Pending | Pending | Pending |
| Frontend Owner | Pending | Pending | Pending |
| Accessibility Reviewer | Pending | Pending | Pending |

---

**End of Document**
