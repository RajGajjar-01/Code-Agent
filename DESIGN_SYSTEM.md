# Design System Documentation

## Overview

This document defines the design system for the WP Agent application, ensuring consistency across all UI components, particularly sidebars and navigation elements.

## Color Tokens

### CSS Variables

All colors are defined using CSS variables in OKLCH color space for consistent perception across different displays.

#### Light Mode

```css
--background: oklch(1 0 0);                     /* Pure white */
--foreground: oklch(0.145 0 0);                 /* Near black */
--primary: #0088ff;                             /* Brand blue */
--primary-foreground: oklch(1 0 0);             /* White */
--secondary: oklch(0.97 0 0);                   /* Light gray */
--muted-foreground: oklch(0.556 0 0);           /* Medium gray */
--border: oklch(0.922 0 0);                     /* Light border */
--destructive: oklch(0.58 0.22 27);             /* Red */
```

#### Sidebar-Specific Tokens

```css
--sidebar: oklch(0.985 0 0);                    /* Sidebar background */
--sidebar-foreground: oklch(0.145 0 0);         /* Sidebar text */
--sidebar-primary: oklch(0.205 0 0);            /* Primary elements */
--sidebar-primary-foreground: oklch(0.985 0 0); /* Primary text */
--sidebar-accent: oklch(0.97 0 0);              /* Hover/active states */
--sidebar-accent-foreground: oklch(0.205 0 0);  /* Accent text */
--sidebar-border: oklch(0.922 0 0);             /* Border color */
--sidebar-ring: oklch(0.708 0 0);               /* Focus rings */
```

#### Dark Mode

```css
--sidebar: oklch(0.205 0 0);                    /* Dark sidebar background */
--sidebar-foreground: oklch(0.985 0 0);         /* Light text */
--sidebar-accent: oklch(0.269 0 0);             /* Darker hover state */
--sidebar-border: oklch(1 0 0 / 10%);           /* Subtle border */
```

### Usage Guidelines

1. **Always use CSS variables** - Never hardcode color values
2. **Sidebar backgrounds** - Use `bg-sidebar`
3. **Sidebar text** - Use `text-sidebar-foreground`
4. **Borders** - Use `border-sidebar-border`
5. **Hover states** - Use `hover:bg-sidebar-accent`
6. **Active states** - Use `bg-sidebar-accent`
7. **Focus rings** - Use `focus:ring-2 focus:ring-sidebar-ring`

## Spacing Scale

### Standard Spacing Values

- **Extra small**: `gap-1` (4px) - Tight spacing within elements
- **Small**: `gap-2` (8px) - Default spacing between related items
- **Medium**: `gap-2.5` (10px) - Spacing in headers and sections
- **Large**: `gap-4` (16px) - Spacing between sections
- **Extra large**: `gap-6` (24px) - Major section separation

### Padding Standards

- **Sidebar padding**: `px-4` or `px-5` (16px or 20px)
- **Header padding**: `px-5` (20px)
- **Button padding**: `px-3 py-2.5` (12px horizontal, 10px vertical)
- **Section padding**: `p-4` (16px)

### Height Standards

- **Header height**: `h-[60px]` - Consistent across all sidebars
- **Button height**: `h-9` (36px) for compact buttons, `h-11` (44px) for primary actions
- **Icon button**: `h-6 w-6` (24px) for toggle buttons

## Typography Scale

### Font Family

```css
--font-sans: 'Inter Variable', sans-serif;
```

All text uses Inter Variable font for consistent typography.

### Text Sizes

- **Section headers**: `text-[0.65rem]` (10.4px) - Uppercase with tracking
- **Regular text**: `text-sm` (14px) - Body text
- **Button text**: `text-sm` (14px) - Medium weight
- **Large headers**: `text-lg` (18px) - Bold weight
- **Small text**: `text-xs` (12px) - Helper text

### Font Weights

- **Regular**: `font-normal` (400)
- **Medium**: `font-medium` (500) - Buttons and emphasis
- **Bold**: `font-bold` (700) - Headers and titles

### Text Styles

#### Section Labels
```tsx
className="text-[0.65rem] font-bold uppercase tracking-wider text-muted-foreground"
```

#### Regular Text
```tsx
className="text-sm font-normal text-sidebar-foreground"
```

#### Button Text
```tsx
className="text-sm font-medium"
```

## Component Patterns

### Sidebar Container

```tsx
<aside className="w-[300px] min-w-[300px] bg-sidebar border-r border-sidebar-border flex flex-col shrink-0 overflow-hidden">
  {/* Sidebar content */}
</aside>
```

**Key properties:**
- Fixed width with min-width to prevent collapse
- `bg-sidebar` for background
- `border-r border-sidebar-border` for right border (use `border-l` for right-side sidebars)
- `flex flex-col` for vertical layout
- `shrink-0` to prevent flex shrinking
- `overflow-hidden` to contain content

### Sidebar Header

```tsx
<div className="flex items-center justify-between h-[60px] px-5 border-b border-sidebar-border shrink-0">
  <h3 className="text-[0.95rem] font-bold truncate text-sidebar-foreground">
    Title
  </h3>
  <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-sidebar-accent">
    <Icon className="h-4 w-4" />
  </Button>
</div>
```

**Key properties:**
- Height: `h-[60px]`
- Padding: `px-5`
- Border: `border-b border-sidebar-border`
- `shrink-0` to prevent compression

### Section Label

```tsx
<div className="text-[0.65rem] font-bold uppercase tracking-wider text-muted-foreground px-2 py-2">
  Section Name
</div>
```

**Key properties:**
- Uppercase with letter spacing
- Muted foreground color
- Small font size

### Interactive Item

```tsx
<button className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-all hover:bg-sidebar-accent">
  <Icon className="h-4 w-4" />
  <span>Item Label</span>
</button>
```

**Key properties:**
- Padding: `px-3 py-2.5`
- Border radius: `rounded-lg`
- Hover state: `hover:bg-sidebar-accent`
- Smooth transitions: `transition-all`

### Primary Button

```tsx
<Button className="h-11 px-4 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-medium">
  Action
</Button>
```

**Key properties:**
- Height: `h-11` for primary actions
- Padding: `px-4`
- Border radius: `rounded-lg`
- Hover opacity: `hover:bg-primary/90`

## Interaction Patterns

### Hover States

All interactive elements should have hover states:

```tsx
// Sidebar items
hover:bg-sidebar-accent

// Buttons
hover:bg-primary/90

// Links
hover:text-primary

// Icons
hover:opacity-80
```

### Active States

Active/selected items should be visually distinct:

```tsx
// Active sidebar item
bg-sidebar-accent text-sidebar-accent-foreground

// Active tab
border-b-2 border-primary
```

### Focus States

All interactive elements must have visible focus indicators:

```tsx
focus:ring-2 focus:ring-sidebar-ring focus:outline-none
```

### Disabled States

Disabled elements should be visually muted:

```tsx
disabled:opacity-50 disabled:pointer-events-none
```

## Animation Guidelines

### Transition Durations

- **Fast**: 150ms - Opacity changes, color transitions
- **Standard**: 200ms - Width changes, transforms
- **Slow**: 300ms - Complex animations, page transitions

### Easing Functions

- **Standard**: `ease-in-out` - Most transitions
- **Enter**: `ease-out` - Elements appearing
- **Exit**: `ease-in` - Elements disappearing

### Sidebar Transitions

```css
.sidebar-wrapper {
  transition: width 200ms ease-in-out;
  overflow: hidden;
}

.sidebar-content {
  transition: opacity 150ms ease-in-out;
}
```

### GPU-Accelerated Properties

For best performance, animate these properties:
- `transform` - Position and scale changes
- `opacity` - Visibility changes
- `filter` - Visual effects

Avoid animating:
- `width` (use `transform: scaleX()` instead when possible)
- `height`
- `margin`
- `padding`

## Icon Guidelines

### Icon Sizes

- **Small**: `h-3.5 w-3.5` (14px) - Inline icons, menu actions
- **Medium**: `h-4 w-4` (16px) - Standard icons in lists
- **Large**: `h-5 w-5` (20px) - Primary action icons
- **Header**: `h-6 w-6` (24px) - Logo and header icons

### Icon Stroke Width

- **Regular**: `strokeWidth={2}` - Standard icons
- **Bold**: `strokeWidth={2.5}` - Emphasis icons (logo, primary actions)

### Icon Usage

```tsx
import { Icon } from 'lucide-react'

// Standard icon
<Icon className="h-4 w-4" strokeWidth={2} />

// Bold icon
<Icon className="h-6 w-6" strokeWidth={2.5} />
```

## Border Radius

### Standard Radii

```css
--radius: 0.625rem;                             /* Base radius (10px) */
--radius-sm: calc(var(--radius) - 4px);         /* 6px */
--radius-md: calc(var(--radius) - 2px);         /* 8px */
--radius-lg: var(--radius);                     /* 10px */
--radius-xl: calc(var(--radius) + 4px);         /* 14px */
--radius-2xl: calc(var(--radius) + 8px);        /* 18px */
```

### Usage

- **Buttons**: `rounded-lg` (10px)
- **Cards**: `rounded-lg` or `rounded-2xl` (10px or 18px)
- **Inputs**: `rounded-lg` (10px)
- **Modals**: `rounded-xl` (14px)
- **Small elements**: `rounded-md` (8px)

## Accessibility Standards

### ARIA Attributes

#### Sidebars

```tsx
<aside 
  role="complementary" 
  aria-label="Descriptive sidebar name"
>
  {/* Content */}
</aside>
```

#### Toggle Buttons

```tsx
<button
  aria-label="Toggle sidebar"
  aria-expanded={isOpen}
  aria-controls="sidebar-content-id"
>
  <Icon />
</button>
```

#### Navigation

```tsx
<nav role="navigation" aria-label="Main navigation">
  <ul role="list">
    <li role="listitem">
      {/* Item */}
    </li>
  </ul>
</nav>
```

### Keyboard Navigation

#### Required Shortcuts

- **Ctrl+B** (Cmd+B on Mac): Toggle primary sidebar (AppSidebar)
- **Ctrl+Shift+E** (Cmd+Shift+E on Mac): Toggle file explorer (IdeSidebar)
- **Ctrl+Shift+D** (Cmd+Shift+D on Mac): Toggle connectors panel
- **Tab**: Navigate between interactive elements
- **Enter/Space**: Activate buttons and links
- **Escape**: Close modals and dropdowns

#### Focus Management

1. **Visible focus indicators** - All interactive elements must show focus state
2. **Logical tab order** - Follow visual layout
3. **Focus trapping** - Trap focus in modals
4. **Skip links** - Provide skip navigation for keyboard users

### Screen Reader Support

1. **Descriptive labels** - All interactive elements have clear labels
2. **State announcements** - Announce sidebar state changes
3. **Proper heading hierarchy** - Use h1-h6 appropriately
4. **Alternative text** - All images have alt text

### Color Contrast

All text must meet WCAG AA standards:
- **Normal text**: 4.5:1 contrast ratio
- **Large text**: 3:1 contrast ratio
- **UI components**: 3:1 contrast ratio

## Consistency Checklist

Before merging any sidebar or UI changes, verify:

- [ ] All colors use CSS variables (no hardcoded hex/rgb)
- [ ] Spacing follows the defined scale
- [ ] Typography matches the standards
- [ ] Borders use `border-sidebar-border`
- [ ] Interactive states use `hover:bg-sidebar-accent`
- [ ] Icons use consistent sizing
- [ ] Border radius uses `rounded-lg` or defined variants
- [ ] Transitions use `transition-all` or `transition-colors`
- [ ] Header height is `h-[60px]` where applicable
- [ ] Section labels use uppercase with tracking
- [ ] ARIA attributes are present and correct
- [ ] Keyboard navigation works properly
- [ ] Focus indicators are visible
- [ ] Color contrast meets WCAG AA standards

## Component Examples

### Complete Sidebar Example

```tsx
import { PanelRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSidebarStore } from '@/stores/sidebar-store'

export function ExampleSidebar() {
  const { exampleSidebarOpen, toggleExampleSidebar } = useSidebarStore()

  if (!exampleSidebarOpen) return null

  return (
    <aside 
      className="w-[300px] min-w-[300px] bg-sidebar border-r border-sidebar-border flex flex-col shrink-0 h-full overflow-hidden"
      role="complementary"
      aria-label="Example sidebar"
    >
      {/* Header */}
      <div className="flex items-center justify-between h-[60px] px-5 border-b border-sidebar-border shrink-0">
        <h3 className="text-[0.95rem] font-bold truncate text-sidebar-foreground">
          Example
        </h3>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleExampleSidebar}
          className="h-6 w-6 hover:bg-sidebar-accent"
          aria-label="Toggle example sidebar"
          aria-expanded={exampleSidebarOpen}
          aria-controls="example-sidebar-content"
        >
          <PanelRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea 
        className="flex-1 w-full" 
        id="example-sidebar-content"
        role="region"
        aria-label="Example sidebar content"
      >
        <div className="p-4 space-y-4">
          {/* Section */}
          <div>
            <div className="text-[0.65rem] font-bold uppercase tracking-wider text-muted-foreground px-2 py-2">
              Section Name
            </div>
            
            {/* Items */}
            <div className="space-y-1">
              <button className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-all hover:bg-sidebar-accent text-sidebar-foreground">
                <span>Item 1</span>
              </button>
              <button className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-all hover:bg-sidebar-accent text-sidebar-foreground">
                <span>Item 2</span>
              </button>
            </div>
          </div>
        </div>
      </ScrollArea>
    </aside>
  )
}
```

## Maintenance

### Adding New Colors

1. Define in `:root` and `.dark` in `index.css`
2. Add to `@theme inline` section
3. Document in this file
4. Update components to use new variable

### Adding New Components

1. Follow existing patterns
2. Use CSS variables for all colors
3. Add proper ARIA attributes
4. Test keyboard navigation
5. Verify color contrast
6. Document in this file

### Updating Spacing

1. Use existing Tailwind classes when possible
2. Only add custom spacing if absolutely necessary
3. Document any new spacing values
4. Ensure consistency across all components

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Lucide Icons](https://lucide.dev/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [OKLCH Color Space](https://oklch.com/)
- [Inter Font](https://rsms.me/inter/)
