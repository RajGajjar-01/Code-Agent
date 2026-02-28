# Design Document: Sidebar Improvements

## Overview

This design document outlines the architecture and implementation strategy for improving sidebar functionality and achieving application-wide consistency across the IDE and Chat pages. The solution implements a dual-sidebar pattern inspired by VS Code, where the IDE page displays both a navigation sidebar (AppSidebar) and a file explorer sidebar (IdeSidebar). Both sidebars will support toggle/collapse functionality with persistent state management.

The key insight from research is that modern IDEs like VS Code successfully use a primary and secondary sidebar pattern, allowing users to have both navigation and context-specific tools visible simultaneously. We'll adopt this pattern while ensuring consistent styling and behavior across both pages.

### Design System Approach

The application already uses a robust design system foundation with:
- **shadcn/ui**: Component library with Radix UI primitives
- **Tailwind CSS 4**: Utility-first CSS with @theme directive
- **CSS Variables**: Design tokens defined in index.css
- **OKLCH Color Space**: Modern color system for consistent perception

We'll leverage this existing design system to ensure consistency by:
1. Using shared CSS variables for all sidebar styling
2. Creating reusable component patterns
3. Establishing consistent spacing, typography, and interaction patterns
4. Implementing a unified state management approach

## Architecture

### Component Hierarchy

```
App
├── RootLayout (Chat Page)
│   ├── AppSidebar (collapsible, left)
│   └── ChatPage
│       ├── Main Content Area
│       └── ConnectorsPanel (collapsible, right)
│
└── IdePage (standalone)
    ├── AppSidebar (collapsible, primary left)
    ├── IdeSidebar (collapsible, secondary left)
    └── Main Content Area
        ├── IdeHeader
        ├── EditorTabs
        └── CodeEditor
```

### State Management Strategy

We'll use Zustand stores for sidebar state management:

1. **SidebarStore**: New store for managing sidebar visibility states
   - Tracks AppSidebar open/closed state
   - Tracks IdeSidebar open/closed state
   - Tracks ConnectorsPanel open/closed state
   - Persists state to localStorage
   - Provides toggle functions

2. **IdeStore**: Existing store (enhanced)
   - Maintains file tree state
   - Handles file operations
   - No changes to core functionality

3. **ChatStore**: Existing store (no changes)
   - Maintains conversation state
   - Handles message operations

4. **AuthStore**: Existing store (refactored)
   - Remove `isPanelOpen` state (moved to SidebarStore)
   - Maintain Google Drive connection state
   - Handle authentication operations

### Layout Strategy

The IDE page will use a **dual-sidebar layout**:
- **Primary Sidebar (AppSidebar)**: Left-most, 300px width, navigation and conversations
- **Secondary Sidebar (IdeSidebar)**: Next to primary, 280px width, file explorer
- **Main Content**: Remaining space, editor and tabs

Both sidebars collapse independently, with smooth CSS transitions.

## Design Tokens and Consistency

### CSS Variables (Design Tokens)

All sidebar styling will use the existing CSS variables defined in `index.css`:

```css
/* Sidebar-specific tokens */
--sidebar: oklch(0.985 0 0);                    /* Background color */
--sidebar-foreground: oklch(0.145 0 0);         /* Text color */
--sidebar-primary: oklch(0.205 0 0);            /* Primary elements */
--sidebar-primary-foreground: oklch(0.985 0 0); /* Primary text */
--sidebar-accent: oklch(0.97 0 0);              /* Hover/active states */
--sidebar-accent-foreground: oklch(0.205 0 0);  /* Accent text */
--sidebar-border: oklch(0.922 0 0);             /* Border color */
--sidebar-ring: oklch(0.708 0 0);               /* Focus rings */

/* Shared tokens */
--radius: 0.625rem;                             /* Border radius */
--font-sans: 'Inter Variable', sans-serif;      /* Typography */
```

### Consistency Rules

To ensure application-wide consistency, all components must follow these rules:

1. **Color Usage**:
   - Use only CSS variables, never hardcoded colors
   - Sidebar backgrounds: `bg-sidebar`
   - Sidebar text: `text-sidebar-foreground`
   - Borders: `border-sidebar-border`
   - Hover states: `hover:bg-sidebar-accent`

2. **Spacing Scale**:
   - Header height: `h-[60px]` (consistent across all headers)
   - Sidebar padding: `px-4` or `px-5` (consistent within each sidebar)
   - Section gaps: `gap-2` or `gap-2.5`
   - Button padding: `px-3 py-2.5`

3. **Typography**:
   - Section headers: `text-[0.65rem] font-bold uppercase tracking-wider`
   - Regular text: `text-sm font-normal`
   - Button text: `text-sm font-medium`
   - All text uses `font-sans` (Inter Variable)

4. **Border Styles**:
   - All borders: `border-sidebar-border`
   - Border width: `border` (1px) or `border-r` for right borders
   - No custom border colors or widths

5. **Interactive States**:
   - Hover: `hover:bg-sidebar-accent`
   - Active: `bg-sidebar-accent`
   - Focus: `focus:ring-2 focus:ring-sidebar-ring`
   - Transitions: `transition-all` or `transition-colors`

6. **Icon Sizing**:
   - Small icons: `h-3.5 w-3.5`
   - Medium icons: `h-4 w-4`
   - Large icons: `h-5 w-5`
   - Header icons: `h-6 w-6`

7. **Border Radius**:
   - Buttons: `rounded-lg` (uses --radius-lg)
   - Cards/Items: `rounded-lg`
   - Inputs: `rounded-lg`

### Component Styling Standards

All sidebar components must use these Tailwind classes:

```typescript
// Sidebar container
className="w-[300px] min-w-[300px] bg-sidebar border-r border-sidebar-border flex flex-col shrink-0 overflow-hidden"

// Header section
className="flex items-center gap-2.5 h-[60px] px-5 border-b border-sidebar-border shrink-0"

// Section label
className="text-[0.65rem] font-bold uppercase tracking-wider text-muted-foreground"

// Interactive item
className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-all hover:bg-sidebar-accent"

// Button
className="h-11 px-4 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
```

## Components and Interfaces

### 1. SidebarStore (New)

```typescript
interface SidebarState {
  // State
  appSidebarOpen: boolean
  ideSidebarOpen: boolean
  connectorsPanelOpen: boolean
  
  // Actions
  toggleAppSidebar: () => void
  toggleIdeSidebar: () => void
  toggleConnectorsPanel: () => void
  setAppSidebarOpen: (open: boolean) => void
  setIdeSidebarOpen: (open: boolean) => void
  setConnectorsPanelOpen: (open: boolean) => void
}
```

### 2. AppSidebar (Enhanced)

```typescript
interface AppSidebarProps {
  // No props needed - uses store internally
}

// Internal state from stores:
// - useChatStore() for conversations
// - useSidebarStore() for collapse state
```

Enhancements:
- Add toggle button in header (consistent with IdeSidebar)
- Add collapse/expand animation (CSS transitions)
- Use sidebar store for state
- Maintain existing conversation functionality
- **Ensure consistent styling with IdeSidebar**

Styling Requirements:
- Width: `w-[300px]` (same as current)
- Background: `bg-sidebar`
- Border: `border-r border-sidebar-border`
- Header height: `h-[60px]` (consistent with IDE)
- Section labels: Use consistent typography
- Interactive items: Use consistent hover states

### 3. IdeSidebar (Enhanced)

```typescript
interface IdeSidebarProps {
  onCreateRequest: (parentPath: string, type: 'file' | 'directory') => void
}

// Internal state from stores:
// - useIdeStore() for file tree
// - useSidebarStore() for collapse state
```

Enhancements:
- Add toggle button in header (consistent with AppSidebar)
- Add collapse/expand animation (CSS transitions)
- Use sidebar store for state
- Fix file creation bugs
- Maintain existing file tree functionality
- **Ensure consistent styling with AppSidebar**

Styling Requirements:
- Width: `w-[280px]` (current, slightly narrower than AppSidebar)
- Background: `bg-sidebar`
- Border: `border-r border-sidebar-border`
- Header height: Match section header pattern
- Section labels: Use consistent typography
- Interactive items: Use consistent hover states

### 3.5. ConnectorsPanel (Refactored)

```typescript
interface ConnectorsPanelProps {
  // No props needed - uses stores internally
}

// Internal state from stores:
// - useAuthStore() for Google Drive connection
// - useSidebarStore() for collapse state
```

Refactoring:
- Move `isPanelOpen` state from AuthStore to SidebarStore
- Add toggle button in header (consistent with other sidebars)
- Add collapse/expand animation (CSS transitions)
- Use sidebar store for state
- Maintain existing Google Drive functionality
- **Ensure consistent styling with AppSidebar and IdeSidebar**

Styling Requirements:
- Width: `w-[320px]` (current width)
- Background: `bg-sidebar`
- Border: `border-l border-sidebar-border` (left border since it's on the right)
- Header height: `h-[60px]` (consistent with other sidebars)
- Header padding: `px-5` (consistent)
- Header border: `border-b border-sidebar-border`
- Section labels: Use consistent typography with uppercase and tracking
- Interactive items: Use consistent hover states (`hover:bg-sidebar-accent`)
- Card styling: Use consistent border radius and spacing
- Button styling: Use consistent padding and hover states

Current Issues to Fix:
- Header uses `h-[57px]` instead of standard `h-[60px]`
- Header uses `bg-background` instead of `bg-sidebar`
- Some hardcoded colors in card styling
- Inconsistent spacing patterns
- Missing toggle button functionality

### 4. Shared Components

#### SidebarHeader (New Shared Component)

```typescript
interface SidebarHeaderProps {
  title: string
  icon?: React.ReactNode
  actions?: React.ReactNode
  onToggle?: () => void
  isCollapsed?: boolean
}
```

A reusable header component that ensures consistency across all sidebars:
- Consistent height: `h-[60px]`
- Consistent padding: `px-5`
- Consistent border: `border-b border-sidebar-border`
- Optional toggle button
- Optional action buttons

#### SidebarSection (New Shared Component)

```typescript
interface SidebarSectionProps {
  label: string
  children: React.ReactNode
  className?: string
}
```

A reusable section component for consistent section styling:
- Consistent label typography
- Consistent spacing
- Consistent padding

#### SidebarItem (New Shared Component)

```typescript
interface SidebarItemProps {
  icon?: React.ReactNode
  label: string
  isActive?: boolean
  onClick?: () => void
  actions?: React.ReactNode
  className?: string
}
```

A reusable item component for lists:
- Consistent padding: `px-3 py-2.5`
- Consistent hover states
- Consistent active states
- Consistent icon sizing

### 5. IdePage (Refactored)

The IdePage component will be refactored to include both sidebars:

```typescript
export function IdePage() {
  const { appSidebarOpen, ideSidebarOpen } = useSidebarStore()
  
  return (
    <div className="flex h-screen bg-background">
      {/* Conditional rendering with smooth transitions */}
      <div className={cn(
        "transition-all duration-200 ease-in-out",
        appSidebarOpen ? "w-[300px]" : "w-0"
      )}>
        {appSidebarOpen && <AppSidebar />}
      </div>
      
      <div className={cn(
        "transition-all duration-200 ease-in-out",
        ideSidebarOpen ? "w-[280px]" : "w-0"
      )}>
        {ideSidebarOpen && <IdeSidebar onCreateRequest={...} />}
      </div>
      
      <main className="flex-1 min-w-0">
        {/* Editor content */}
      </main>
    </div>
  )
}
```

### 6. SidebarToggle (New Component)

```typescript
interface SidebarToggleProps {
  isOpen: boolean
  onToggle: () => void
  side: 'left' | 'right'
  ariaLabel: string
  className?: string
}
```

A reusable toggle button component:
- Consistent size: `h-6 w-6`
- Consistent icon: `PanelLeft` or `PanelRight` from lucide-react
- Consistent styling: `hover:bg-sidebar-accent`
- Proper ARIA attributes
- Keyboard accessible

### 7. Consistency Audit Component (Development Tool)

```typescript
interface ConsistencyAuditProps {
  enabled: boolean
}
```

A development-only component that:
- Scans all sidebar components
- Checks for consistent CSS variable usage
- Validates spacing and typography
- Reports inconsistencies to console
- Only runs in development mode

## Data Models

### Sidebar State (localStorage)

```typescript
interface PersistedSidebarState {
  appSidebarOpen: boolean       // default: true
  ideSidebarOpen: boolean        // default: true
  connectorsPanelOpen: boolean   // default: true
}

// Stored at key: 'sidebar-state'
```

### File Creation Request

```typescript
interface CreateNodeRequest {
  parentPath: string
  name: string
  type: 'file' | 'directory'
}

interface CreateNodeResponse {
  success: boolean
  error?: string
  path?: string
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Sidebar state persistence

*For any* sidebar toggle action, when the user toggles a sidebar and then refreshes the page, the sidebar state should be restored to the same open/closed state as before the refresh.

**Validates: Requirements 2.4**

### Property 2: Independent sidebar toggles

*For any* combination of sidebar states (both open, both closed, one open), toggling one sidebar should not affect the state of the other sidebar.

**Validates: Requirements 2.2**

### Property 3: Layout space utilization

*For any* sidebar state change, when a sidebar is collapsed, the main content area width should increase by the width of the collapsed sidebar, and when expanded, the main content area should decrease by the sidebar width.

**Validates: Requirements 2.3**

### Property 4: File creation validation

*For any* file or folder name containing invalid characters (/, \, :, *, ?, ", <, >, |), the system should reject the creation request and display an error message.

**Validates: Requirements 3.4**

### Property 5: File tree update after creation

*For any* successful file or folder creation, the file tree should immediately reflect the new item without requiring a manual refresh.

**Validates: Requirements 3.5**

### Property 6: Consistent border styling

*For any* sidebar component (AppSidebar, IdeSidebar, or ConnectorsPanel), the border styles (color, width, position) should match the design system standards to maintain visual consistency.

**Validates: Requirements 1.2, 1.4, 6.1**

### Property 7: Navigation preservation

*For any* conversation selected in the AppSidebar on the IDE page, clicking it should navigate to the Chat page with that specific conversation loaded and active.

**Validates: Requirements 4.4**

### Property 8: ConnectorsPanel styling consistency

*For any* CSS variable used in ConnectorsPanel, it should match the same variable used in AppSidebar and IdeSidebar for equivalent elements (headers, borders, backgrounds, hover states).

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 9: ConnectorsPanel toggle behavior

*For any* toggle action on the ConnectorsPanel, the transition duration and easing should match the transitions used for AppSidebar and IdeSidebar.

**Validates: Requirements 2.5, 6.5**

## Error Handling

### File Creation Errors

1. **Invalid Name**: Display toast notification with specific error
   - Empty name: "File name cannot be empty"
   - Invalid characters: "File name contains invalid characters: [list]"
   - Name too long: "File name exceeds maximum length"

2. **Network Errors**: Display toast with retry option
   - "Failed to create file. Please try again."

3. **Permission Errors**: Display toast with explanation
   - "Permission denied. Cannot create file in this directory."

### State Management Errors

1. **localStorage Unavailable**: Gracefully degrade to in-memory state
   - Log warning to console
   - Continue with default sidebar states

2. **State Corruption**: Reset to defaults
   - Clear corrupted localStorage entry
   - Use default open states

### Sidebar Rendering Errors

1. **Component Mount Errors**: Use Error Boundaries
   - Display fallback UI
   - Log error details
   - Allow app to continue functioning

## Testing Strategy

### Unit Tests

We'll write unit tests for:

1. **SidebarStore**:
   - Toggle functions update state correctly
   - State persists to localStorage
   - State loads from localStorage on init
   - Default states when localStorage is empty

2. **File Creation Validation**:
   - Invalid character detection
   - Empty name rejection
   - Valid name acceptance

3. **Component Rendering**:
   - Sidebars render with correct initial state
   - Toggle buttons trigger state changes
   - Conditional rendering based on state

### Property-Based Tests

We'll use **fast-check** (JavaScript/TypeScript property-based testing library) to implement property-based tests. Each test will run a minimum of 100 iterations.

1. **Property 1: Sidebar state persistence**
   - Generate random sidebar states
   - Simulate save and load
   - Verify loaded state matches saved state

2. **Property 2: Independent sidebar toggles**
   - Generate random initial states
   - Toggle one sidebar
   - Verify other sidebar unchanged

3. **Property 3: Layout space utilization**
   - Generate random sidebar states
   - Calculate expected widths
   - Verify actual widths match expected

4. **Property 4: File creation validation**
   - Generate random strings with invalid characters
   - Verify all are rejected
   - Generate valid strings
   - Verify all are accepted

5. **Property 5: File tree update**
   - Generate random file/folder names
   - Create items
   - Verify tree contains new items

6. **Property 6: Consistent border styling**
   - Extract computed styles from both sidebars
   - Verify border properties match

7. **Property 7: Navigation preservation**
   - Generate random conversation IDs
   - Simulate navigation
   - Verify correct conversation loaded

### Integration Tests

1. **Full Page Interactions**:
   - Navigate between Chat and IDE pages
   - Verify sidebar states persist per page
   - Verify no layout shifts or flickers

2. **File Operations**:
   - Create files and folders
   - Verify tree updates
   - Verify files can be opened

3. **Responsive Behavior**:
   - Test on different viewport sizes
   - Verify sidebars adapt appropriately

## Implementation Notes

### CSS Transitions

Use CSS transitions for smooth collapse/expand:

```css
/* Sidebar wrapper transitions */
.sidebar-wrapper {
  transition: width 0.2s ease-in-out;
  overflow: hidden;
}

.sidebar-wrapper.collapsed {
  width: 0;
}

/* Content transitions */
.sidebar-content {
  transition: opacity 0.15s ease-in-out;
}

.sidebar-wrapper.collapsed .sidebar-content {
  opacity: 0;
}
```

### Consistency Checklist

Before merging any sidebar changes, verify:

- [ ] All colors use CSS variables (no hardcoded hex/rgb)
- [ ] Spacing follows the defined scale
- [ ] Typography matches the standards
- [ ] Borders use `border-sidebar-border`
- [ ] Interactive states use `hover:bg-sidebar-accent`
- [ ] Icons use consistent sizing
- [ ] Border radius uses `rounded-lg`
- [ ] Transitions use `transition-all` or `transition-colors`
- [ ] Header height is `h-[60px]` where applicable
- [ ] Section labels use uppercase with tracking

### Refactoring Strategy

To ensure consistency, follow this refactoring order:

1. **Create shared components first**:
   - SidebarHeader
   - SidebarSection
   - SidebarItem
   - SidebarToggle

2. **Refactor AppSidebar**:
   - Replace custom header with SidebarHeader
   - Replace section labels with SidebarSection
   - Replace conversation items with SidebarItem
   - Add toggle functionality

3. **Refactor IdeSidebar**:
   - Replace custom header with SidebarHeader
   - Replace section labels with SidebarSection
   - Replace file tree items with SidebarItem (where applicable)
   - Add toggle functionality

4. **Update IdePage**:
   - Add AppSidebar
   - Implement dual-sidebar layout
   - Add transition wrappers

5. **Test consistency**:
   - Visual comparison
   - Interaction testing
   - Responsive testing

### Accessibility

1. **ARIA Attributes**:
   - `aria-expanded` on toggle buttons
   - `aria-controls` linking buttons to sidebars
   - `aria-label` for icon-only buttons
   - `role="navigation"` on sidebar containers
   - `role="list"` and `role="listitem"` for item lists

2. **Keyboard Navigation**:
   - Toggle buttons accessible via Tab
   - Keyboard shortcuts:
     - `Ctrl+B` (or `Cmd+B`): Toggle primary sidebar (AppSidebar)
     - `Ctrl+Shift+E` (or `Cmd+Shift+E`): Toggle file explorer (IdeSidebar)
   - Arrow keys for list navigation
   - Enter/Space to activate items

3. **Focus Management**:
   - Maintain focus when toggling
   - Trap focus in modals
   - Visible focus indicators using `focus:ring-2 focus:ring-sidebar-ring`
   - Skip links for keyboard users

4. **Screen Reader Support**:
   - Announce sidebar state changes
   - Descriptive labels for all interactive elements
   - Proper heading hierarchy

### Design System Documentation

Create a `DESIGN_SYSTEM.md` file documenting:

1. **Color Tokens**: All CSS variables and their usage
2. **Spacing Scale**: Standard spacing values
3. **Typography Scale**: Font sizes, weights, and line heights
4. **Component Patterns**: Reusable component examples
5. **Interaction Patterns**: Hover, active, focus states
6. **Animation Guidelines**: Transition durations and easings
7. **Accessibility Standards**: WCAG compliance guidelines

This documentation ensures future developers maintain consistency.

### Performance Considerations

1. **Lazy Rendering**: Don't unmount sidebars when collapsed, just hide with CSS
2. **Memoization**: 
   - Use `React.memo` for sidebar components
   - Use `useMemo` for expensive computations
   - Use `useCallback` for event handlers
3. **Debouncing**: Debounce localStorage writes (300ms)
4. **Virtual Scrolling**: Consider for large file trees (future enhancement)
5. **CSS Containment**: Use `contain: layout style` on sidebar containers
6. **Transition Performance**: Use `transform` and `opacity` for animations (GPU-accelerated)

### Browser Compatibility

- Target modern browsers (Chrome, Firefox, Safari, Edge)
- Use CSS Grid and Flexbox (widely supported)
- OKLCH color space (fallback to RGB if needed)
- CSS variables (widely supported)
- Fallback for localStorage unavailability

### Migration Path

For existing components using inconsistent styling:

1. **Identify**: Scan codebase for hardcoded colors, spacing, etc.
2. **Replace**: Update to use CSS variables and Tailwind classes
3. **Test**: Verify visual consistency
4. **Document**: Update component documentation

Example migration:

```typescript
// Before (inconsistent)
<div className="bg-white border-gray-200 px-4 py-3">

// After (consistent)
<div className="bg-sidebar border-sidebar-border px-4 py-3">
```

### Quality Assurance

1. **Visual Regression Testing**: 
   - Take screenshots before/after
   - Compare side-by-side
   - Check all interactive states

2. **Cross-Browser Testing**:
   - Test on Chrome, Firefox, Safari, Edge
   - Test on different OS (Windows, macOS, Linux)

3. **Responsive Testing**:
   - Test on different viewport sizes
   - Test sidebar behavior on mobile (future consideration)

4. **Accessibility Testing**:
   - Test with screen readers (NVDA, JAWS, VoiceOver)
   - Test keyboard navigation
   - Run axe DevTools audit

5. **Performance Testing**:
   - Measure render times
   - Check for memory leaks
   - Profile with React DevTools

## Dependencies

- **fast-check**: Property-based testing library (~4.0.0)
- **@testing-library/react**: Component testing (already in use)
- **zustand**: State management (already in use)
- **lucide-react**: Icons (already in use)
- **clsx** or **cn utility**: Conditional className merging (already in use via lib/utils)

No new major dependencies required. All styling uses existing Tailwind CSS and CSS variables.

## Design System Governance

### Style Guide Enforcement

To maintain consistency, implement these practices:

1. **Code Review Checklist**:
   - Verify CSS variable usage
   - Check spacing consistency
   - Validate typography
   - Confirm interaction patterns

2. **Linting Rules** (future enhancement):
   - ESLint plugin to detect hardcoded colors
   - Stylelint rules for CSS consistency
   - Custom rules for Tailwind class patterns

3. **Component Library**:
   - Document all shared components
   - Provide usage examples
   - Include do's and don'ts
   - Show interactive demos

4. **Design Tokens Documentation**:
   - Maintain up-to-date token list
   - Show visual examples
   - Explain usage contexts
   - Provide code snippets

### Consistency Metrics

Track these metrics to ensure consistency:

1. **CSS Variable Coverage**: % of components using CSS variables vs hardcoded values
2. **Component Reuse**: % of UI using shared components vs custom implementations
3. **Style Violations**: Number of inconsistent patterns detected
4. **Accessibility Score**: WCAG compliance level

Target: 100% CSS variable coverage, 80%+ component reuse
