# Cocktail Cartography — Art Deco Style Guide

This document defines the visual design system for Cocktail Cartography, inspired by the geometric elegance and opulent glamour of 1920s Art Deco design.

---

## Design Philosophy

The Art Deco movement (1920s-1930s) emphasized:
- **Geometric patterns** — chevrons, zigzags, stepped forms, sunbursts
- **Luxurious materials** — gold, silver, chrome, rich jewel tones
- **Bold contrasts** — deep blacks with brilliant metallics
- **Elegant typography** — geometric sans-serifs with generous letter-spacing
- **Symmetry and order** — clean lines, structured layouts

Our implementation balances historical authenticity with modern accessibility standards.

---

## Color Palette

### Primary Colors

| Color | Hex | Usage | Notes |
|-------|-----|-------|-------|
| **Deco Black** | `#1a1a1d` | Primary background | Softer than pure black for reduced eye strain |
| **Deco Charcoal** | `#2d2d30` | Secondary backgrounds, elevated surfaces | Panels, buttons, hover states |
| **Deco Gold** | `#D4AF37` | Primary accent, borders, interactive elements | Classic Art Deco gold |
| **Deco Gold Dark** | `#B8941E` | Gradients, shadows | Depth variation of gold |

### Text Colors (Accessibility-First)

| Color | Hex | Usage | Contrast Ratio |
|-------|-----|-------|----------------|
| **Cream** | `#F5F5DC` | Primary text, headings | 12.8:1 on Deco Black ✓ WCAG AAA |
| **Cream Dark** | `#E8E8CF` | Hover states | 11.2:1 on Deco Black ✓ WCAG AAA |
| **Silver** | `#C0C0C0` | Secondary text | 9.4:1 on Deco Black ✓ WCAG AAA |
| **Text Secondary** | `#C5C5B0` | Body text, labels | 8.1:1 on Deco Black ✓ WCAG AAA |
| **Text Tertiary** | `#9A9A88` | Metadata, subtle info | 5.2:1 on Deco Black ✓ WCAG AA |
| **Text Muted** | `#6B6B60` | Disabled states, minimized info | 3.5:1 on Deco Black ✓ WCAG AA Large |

### Jewel Tones (Data Visualization)

| Color | Hex | Usage |
|-------|-----|-------|
| **Emerald** | `#50C878` | Success states, agave spirits |
| **Sapphire** | `#0F52BA` | Gin, citrus highlights |
| **Ruby** | `#E0115F` | Brandy, fruit accents |
| **Bronze** | `#CD7F32` | Whiskey, aged spirits |

### Semantic Colors

```css
--border-primary: #D4AF37;      /* Gold borders for emphasis */
--border-secondary: #4a4a3d;    /* Subtle dividers */
--bg-panel: #1a1a1d;            /* Panel backgrounds */
--bg-panel-lighter: #2d2d30;    /* Elevated panels */
```

---

## Typography

### Font Stack

```css
font-family: "Futura", "Century Gothic", "Avenir Next", "Helvetica Neue", Arial, sans-serif;
```

**Rationale**: Futura and Century Gothic are quintessential Art Deco typefaces — geometric, clean, modern. Fallbacks ensure consistency across platforms.

### Type Scale

| Element | Size | Weight | Letter-spacing | Transform |
|---------|------|--------|----------------|-----------|
| **H1 (Main Title)** | 18px | 300 | 0.15em | uppercase |
| **H2 (Section Labels)** | 10px | 600 | 0.16em | uppercase |
| **Strategy Title** | 12px | 600 | 0.05em | none |
| **Body Text** | 13px | 400 | 0.01em | none |
| **Small Text** | 11px | 400 | 0.03em | none |
| **Tiny Labels** | 9-10px | 700 | 0.12em | uppercase |

### Typography Rules

1. **Uppercase sparingly** — Headers and labels only, never body text
2. **Letter-spacing for elegance** — Generously space uppercase text (0.12em–0.16em)
3. **Lighter weights for large text** — Font-weight 300 for titles creates sophistication
4. **Tabular numbers** — Use `font-variant-numeric: tabular-nums` for aligned data

---

## Layout & Spacing

### Grid System

- **Sidebar width**: 280px (min 180px, max 520px) — resizable
- **Panel padding**: 18-20px horizontal, 16-20px vertical
- **Component gaps**: 20-24px between major sections
- **Item spacing**: 6-8px between list items
- **Micro-spacing**: 3-4px for tight groupings

### Border Styles

```css
/* Primary emphasis */
border: 2px solid var(--deco-gold);

/* Subtle dividers */
border: 2px solid var(--border-secondary);

/* Inline accents */
border-left: 2px solid var(--deco-gold);
```

**Note**: Art Deco favors **sharp corners** (border-radius: 0 or 2px) over rounded edges.

---

## Patterns & Decorative Elements

### Chevron Pattern (Header Accent)

```css
background: linear-gradient(
  135deg,
  transparent 25%,
  var(--deco-gold) 25%,
  var(--deco-gold) 50%,
  transparent 50%,
  transparent 75%,
  var(--deco-gold) 75%,
  var(--deco-gold)
);
background-size: 8px 8px;
height: 4px;
```

**Usage**: Top border of sidebars and panels

### Gradient Dividers

```css
/* Horizontal fade */
background: linear-gradient(90deg, var(--deco-gold) 0%, transparent 100%);
height: 2px;

/* Vertical fade for stepped borders */
background: linear-gradient(180deg, var(--deco-gold) 0%, var(--deco-gold-dark) 50%, var(--deco-gold) 100%);
```

### Corner Accents (Tooltips)

```css
#tooltip::before,
#tooltip::after {
  content: "";
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid var(--deco-gold);
}

#tooltip::before {
  top: -3px;
  left: -3px;
  border-right: none;
  border-bottom: none;
}

#tooltip::after {
  bottom: -3px;
  right: -3px;
  border-left: none;
  border-top: none;
}
```

### Vertical Accent Bar (Active States)

```css
.strategy-btn::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--deco-gold);
}
```

---

## Interactive States

### Buttons & Controls

```css
/* Resting */
background: var(--bg-panel-lighter);
border: 2px solid var(--border-secondary);
color: var(--text-secondary);

/* Hover */
background: var(--deco-charcoal);
border-color: var(--deco-gold);
color: var(--deco-gold);
box-shadow: 0 0 8px rgba(212, 175, 55, 0.3);

/* Active/Pressed */
background: var(--deco-gold);
color: var(--deco-black);

/* Focus */
border-color: var(--deco-gold);
box-shadow: 0 0 8px rgba(212, 175, 55, 0.3);
outline: none;
```

### Transitions

```css
/* Standard interaction */
transition: all 0.2s ease;

/* Fast micro-interactions */
transition: all 0.15s ease;

/* Smooth layouts */
transition: max-height 0.3s ease, opacity 0.25s ease;
```

---

## Components

### Strategy Buttons

- **Border**: 2px solid, sharp corners (border-radius: 2px)
- **Vertical accent**: 4px gold bar on left when active
- **Hover glow**: Gold shadow (0 0 8px rgba(212, 175, 55, 0.3))
- **Padding**: 12px 14px

### Sliders

- **Track height**: 6px
- **Accent color**: Gold
- **Step buttons**: 24×24px, sharp corners, gold hover
- **Labels**: Small uppercase text (10px, 0.03em letter-spacing)

### Tooltips

- **Border**: 3px solid gold
- **Corner accents**: L-shaped gold corners (12×12px)
- **Title**: Gold, uppercase, 0.08em letter-spacing
- **Shadow**: Layered (blur + glow)
  ```css
  box-shadow:
    0 12px 40px rgba(0,0,0,0.7),
    0 0 20px rgba(212, 175, 55, 0.2);
  ```

### Ingredient Panel Groups

- **Group header**: Gold uppercase labels with chevron
- **Hover state**: Charcoal background
- **Action buttons**: Small (9px), uppercase, gold hover
- **Subgroups**: Divided by subtle gold lines (1px, 15% opacity)

### Legend

- **Border**: 2px solid gold
- **Title**: Gold, divider below
- **Swatches**: 14×14px squares with subtle border
- **Shadow**: Same as tooltips (layered depth)

---

## Accessibility Checklist

### Contrast Requirements (WCAG 2.1)

- ✅ **AAA for body text** — Cream (#F5F5DC) on Black (#1a1a1d): 12.8:1
- ✅ **AAA for UI text** — Text Secondary (#C5C5B0) on Black: 8.1:1
- ✅ **AA for all interactive elements** — Minimum 4.5:1
- ✅ **Gold accents** — Used for emphasis, not primary text (except tooltips)

### Focus Indicators

All interactive elements must have visible focus states:
```css
element:focus {
  border-color: var(--deco-gold);
  box-shadow: 0 0 8px rgba(212, 175, 55, 0.3);
  outline: none; /* Custom outline replaces default */
}
```

### Motion & Animation

- **Respect prefers-reduced-motion** (not yet implemented — future enhancement)
- **Smooth easing** — Use `ease` or `ease-in-out`, not linear
- **Reasonable durations** — 150-300ms for UI, never >500ms

---

## Data Visualization Colors

When coloring dots by category, use vibrant, accessible palettes:

### Base Spirits
```javascript
whiskey: "#CD7F32",  // Bronze
gin:     "#22d3ee",  // Cyan (retained for contrast)
agave:   "#50C878",  // Emerald
rum:     "#a78bfa",  // Purple (retained)
brandy:  "#fb7185",  // Pink (retained)
vodka:   "#fbbf24",  // Amber (retained)
```

**Note**: Some original colors retained where they already meet contrast requirements and fit the palette.

---

## Implementation Notes

### CSS Variables

All design tokens are defined in `:root`:
```css
:root {
  --deco-black: #1a1a1d;
  --deco-charcoal: #2d2d30;
  --deco-gold: #D4AF37;
  --text-primary: #F5F5DC;
  /* etc. */
}
```

**Benefits**:
- Centralized theme management
- Easy to create alternate themes (light mode, high contrast)
- Consistent color usage across components

### Browser Support

- **CSS Variables**: All modern browsers (IE11 not supported)
- **CSS Grid/Flexbox**: All modern browsers
- **Gradients**: All modern browsers
- **Filter effects** (blur, drop-shadow): All modern browsers

### Performance

- **GPU-accelerated properties** for animations: `transform`, `opacity`
- **Avoid animating** `width`, `height`, `top`, `left` (use `transform` instead)
- **Reflow-safe** hover effects

---

## Future Enhancements

1. **Light mode variant** — Cream background, charcoal text, bronze accents
2. **High contrast mode** — Increased contrast for accessibility
3. **Reduced motion mode** — Disable transitions when `prefers-reduced-motion: reduce`
4. **Additional patterns** — Sunburst backgrounds, zigzag dividers
5. **Custom fonts** — Self-hosted Futura for consistent rendering

---

## Resources

### Art Deco Design References
- [The Met Collection — Art Deco](https://www.metmuseum.org/toah/hd/ardc/hd_ardc.htm)
- [V&A Museum — Art Deco Style Guide](https://www.vam.ac.uk/articles/an-introduction-to-art-deco)

### Accessibility Tools
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Typography
- [Fonts In Use — Art Deco](https://fontsinuse.com/in/2/styles/art-deco)
- [Futura Typeface History](https://www.fonts.com/font/linotype/futura)

---

**Last Updated**: February 2026
**Version**: 1.0
**Maintained By**: Cocktail Cartography Team
