# UI Simplification and About Page Implementation Plan

**Date**: February 2026
**Status**: Implemented
**Goal**: Simplify the visualization from 5 to 3 strategies, fix UI bugs, and create an interactive About page for different audience levels.

---

## Executive Summary

This plan outlines a comprehensive UI redesign to make Cocktail Cartography more approachable for a general audience while maintaining its analytical depth. Key changes include:

1. Reducing from 5 to 3 vectorization strategies (removing redundancy)
2. Fixing critical bugs (broken tooltips and inverted alpha slider)
3. Creating collapsible UI sections for better space utilization
4. Moving all display controls to a bottom panel
5. Building an interactive About page that adapts to reader expertise level

## Critical Bugs to Fix First

### Bug 1: Broken Cocktail Information Display
**Severity**: CRITICAL - Core functionality broken
**Symptoms**:
- Hovering over cocktails doesn't show preview tooltip
- Clicking cocktails doesn't pin information
- Users cannot see cocktail details or nearest neighbors

**Likely causes to investigate**:
- Event handlers not properly attached
- Tooltip element hidden or positioned incorrectly
- Z-index issues with other UI elements
- JavaScript errors preventing tooltip code from running

### Bug 2: Inverted Alpha Slider Labels
**Severity**: HIGH - Confusing user experience
**Symptoms**:
- Left side labeled "More flavor" but actually shows structure
- Right side labeled "More structure" but actually shows flavor
- Status text contradicts slider position

---

## Part 1: Strategy Simplification

### Current State (5 Strategies)
1. **Flavor Blend** - Volume-weighted average of ingredient flavors
2. **Blend+Struct** - Interpolates between flavor and structure (α slider)
3. **Role-Slot** - Compares drinks by ingredient roles
4. **Perceptual** - Fixed at punch_weight=0.4 for intense ingredients
5. **Tau** - Softmax perceptual with τ parameter (0.1 to 316)

### Problem Analysis
- **Tau at high τ (≈316)** converges to Flavor Blend (volume-proportional)
- **Tau at low τ (≈0.1)** acts like Perceptual (intense ingredients dominate)
- Having both Flavor Blend AND Perceptual as separate strategies is redundant

### New State (3 Strategies)

#### 1. Perceptual Blend (formerly Tau)
- **What it does**: Controls how much intense ingredients influence the clustering
- **Slider range**: τ from 0.1 to 316 (25 steps, log scale)
- **Slider labels**:
  - Left: "Intense wins" or "Punchy dominates"
  - Right: "By volume" or "Everything proportional"
- **Replaces**: Both "Flavor Blend" and "Perceptual" strategies

#### 2. Taste + Structure (formerly Blend+Struct)
- **What it does**: Balances between flavor similarity and structural similarity
- **Slider range**: α from 0 to 1 (21 steps)
- **Slider labels**:
  - Left: "How it's made" (α=0, pure structure)
  - Right: "How it tastes" (α=1, pure flavor)
- **Critical bug to fix**: Currently labels are inverted

#### 3. Recipe Grammar (formerly Role-Slot)
- **What it does**: Compares drinks by matching ingredient roles
- **No slider**: This is a pure structural view
- **Unique value**: Only strategy that compares slot-to-slot

---

## Part 2: Critical Bug Fix - Alpha Slider

### The Bug
The Blend+Structure slider has inverted logic:
- **Current labels**: "← More flavor" ... "More structure →"
- **Current values**: α=0 (left) is pure structure, α=1 (right) is pure flavor
- **Result**: Labels say opposite of what's happening

### The Fix

#### Option A: Swap the Labels (Recommended)
```javascript
// Change from:
<span>← More flavor</span>
<span>More structure →</span>

// To:
<span>← How it's made</span>
<span>How it tastes →</span>
```

#### Option B: Invert the Alpha Value
```javascript
// When looking up data, use (1 - alpha)
const effectiveAlpha = 1 - ALPHA_STEPS[currentAlpha];
const key = `blend_struct_a${Math.round(effectiveAlpha * 100)}`;
```

**Recommendation**: Option A (swap labels) is cleaner and more intuitive.

---

## Part 3: UI Redesign - Collapsible Sections

### Strategy Selection (Sidebar)

#### Current Design
All strategies show full descriptions at once, taking up significant vertical space.

#### New Design
Collapsible accordion-style sections:

```
┌─────────────────────────────────────┐
│ ▶ Perceptual Blend                  │ ← Collapsed (default)
│   How intense flavors matter        │
└─────────────────────────────────────┘
│ ▼ Taste + Structure                 │ ← Expanded (active)
│                                     │
│ Balances between how a cocktail    │
│ tastes and how it's constructed.   │
│ Use the slider to explore...       │
│                                     │
│ How it's made ←──●──→ How it tastes │
│        α = 0.50 (balanced)          │
└─────────────────────────────────────┘
│ ▶ Recipe Grammar                    │ ← Collapsed
│   Compare by ingredient roles       │
└─────────────────────────────────────┘
```

**Benefits**:
- More room for "About This View" explanation
- Cleaner, less overwhelming interface
- Focus on one strategy at a time

### Display Controls (Bottom Panel)

#### Current Location
All controls are in the sidebar:
- Color by dropdown
- Highlight family checkboxes
- Show labels checkbox

#### New Location
Collapsible panel at bottom of visualization:

```
┌──────────────────────────────────────────────────┐
│ ▼ Display Options                                │ ← Click to collapse
├──────────────────────────────────────────────────┤
│ Color by: [Base spirit ▼]                        │
│           • Base spirit                          │
│           • Cocktail family                      │
│           • Served style                         │
│           • Dominant flavor                      │
│           • Individual flavors...                │
│                                                  │
│ Highlight families:                              │
│ ☑ Sour  ☑ Spirit-forward  ☑ Built  ☑ Other     │
│                                                  │
│ ☑ Show cocktail names                            │
└──────────────────────────────────────────────────┘

When collapsed:
┌──────────────────────────────────────────────────┐
│ ▲ Display Options                                │
└──────────────────────────────────────────────────┘
```

**Implementation notes**:
- Position: fixed at bottom of viewport
- Z-index: above visualization but below tooltip
- Animation: smooth slide up/down
- Default state: Collapsed on load

---

## Part 4: Interactive About Page

### URL: `/viz/about.html`

### Content Structure

#### Fixed Header (Always Visible)
```markdown
# Cocktail Cartography

An interactive map of 102 classic cocktails that shows you which
drinks are similar to each other — and lets you explore *why*
they're similar by switching between different ways of thinking
about cocktails.

## Why this exists

One thing I love about cocktails is their variety. So it took
me a lot of years... [personal story continues]
```

#### Reader Selection Interface
```html
<div class="reader-question">
  <p><em>How did you make this?</em></p>
  <p><em>I'm...</em></p>

  <div class="reader-options">
    <label class="reader-radio">
      <input type="radio" name="reader-type" value="curious" checked>
      <span>Curious</span>
    </label>

    <label class="reader-checkbox">
      <input type="checkbox" id="cocktail-nerd">
      <span>a cocktail nerd</span>
    </label>

    <label class="reader-checkbox">
      <input type="checkbox" id="data-nerd">
      <span>a data nerd</span>
    </label>
  </div>
</div>
```

### Content Sources

| Selection | Content File | Description |
|-----------|-------------|-------------|
| Curious (default) | About-CURIOUS.md | General audience explanation |
| Cocktail nerd | About-COCKTAIL_NERD.md | Detailed cocktail theory |
| Data nerd | About-DATA_NERD.md | Technical implementation |
| Both nerds | About-COCKTAIL_DATA_NERD.md | Combined deep dive |

### Interaction Behavior

1. **Mutual Exclusivity**:
   - Selecting "Curious" unchecks both nerd checkboxes
   - Checking any nerd box deselects "Curious"

2. **Content Loading**:
   - Content updates dynamically without page reload
   - Smooth transition between content sections
   - Maintain scroll position when switching

3. **URL State** (optional):
   - Update URL hash: `about.html#curious`, `about.html#cocktail`, etc.
   - Allow direct linking to specific content levels

### Styling
- Match Art Deco theme from main visualization
- Same color palette (gold, cream, charcoal)
- Responsive design for mobile viewing

---

## Part 5: Implementation Steps

### Phase 1: Critical Fixes (Do First)
1. **Fix tooltip/cocktail info bug** in viz/index.html
   - **Critical**: Cocktail information not showing on hover or click
   - Debug event handlers for mouseover/click events
   - Check tooltip display logic and CSS
   - Ensure both hover preview and click-to-pin functionality work
   - Test on different browsers

2. **Fix alpha slider bug** in viz/index.html
   - Swap labels to "How it's made" ← → "How it tastes"
   - Fix status text to match

### Phase 2: Strategy Simplification
2. **Remove redundant strategies** from viz/index.html
   - Remove "blend" strategy option
   - Remove "perceptual" strategy option

3. **Rename remaining strategies**
   - "tau" → "perceptual_blend"
   - "blend_struct" → "taste_structure"
   - "role_slot" → "recipe_grammar"

4. **Update slider labels**
   - Tau: "Intense wins" ← → "By volume"
   - Alpha: "How it's made" ← → "How it tastes"

### Phase 3: UI Reorganization
5. **Implement collapsible strategy sections**
   - Add expand/collapse functionality
   - Show only active strategy details
   - Animate transitions

6. **Move display controls to bottom**
   - Create fixed bottom panel
   - Move color, highlight, and label controls
   - Implement collapse/expand for panel

### Phase 4: About Page
7. **Create about.html**
   - Set up page structure
   - Implement reader selection logic
   - Load content from About-*.md files
   - Style to match main viz

8. **Add About link** to main viz
   - Place in sidebar or header
   - Style consistently

### Phase 5: Cleanup
9. **Remove old README files**
   - Delete README_CURIOUS.md
   - Delete README_COCKTAIL_NERD.md
   - Delete README_DATA_NERD.md
   - Keep README.md for technical documentation

---

## Part 6: Testing Checklist

**Testing Approach**: Since I cannot directly access browsers, I will:
1. **Analyze code** to identify bugs and write fixes based on the code structure
2. **Provide specific test cases** for you to verify in your browser
3. **Create console commands** you can run to test functionality
4. **Debug iteratively** based on error messages and feedback you provide

You will need to:
- Run the local server (`python -m http.server 8000`) and test in your browser
- Verify visual appearance and interactions
- Report any console errors or unexpected behavior
- Confirm cross-browser compatibility

### Functionality Tests
- [x] **Cocktail tooltips work on hover** (shows preview)
- [x] **Cocktail tooltips work on click** (pins the tooltip)
- [x] Alpha slider shows correct labels and values
- [x] Tau slider smoothly transitions between extremes
- [x] Strategy selection shows only one expanded at a time
- [x] Bottom panel collapses and expands properly
- [x] About page reader selection works correctly
- [x] Content switches without page reload

### Visual Tests
- [x] Collapsed strategies show enough info to understand
- [x] Expanded strategies have room for full explanation
- [x] Bottom panel doesn't obscure visualization
- [x] About page matches main viz styling
- [ ] Mobile responsive design works

### Data Integrity
- [x] All 102 cocktails still appear
- [ ] Clustering remains consistent with data
- [ ] Nearest neighbors still calculate correctly
- [x] Color modes all work

---

## Part 7: Future Considerations

### Potential Enhancements
1. **URL State Management**: Add URL parameters for current strategy and slider positions
2. **Keyboard Navigation**: Arrow keys for sliders, number keys for strategies
3. **Export Feature**: Save current view as image or data
4. **Search**: Find specific cocktails quickly
5. **Custom Cocktails**: Let users add their own recipes

### Technical Debt
1. **Python Scripts**: Currently generate all 5 strategies (can optimize later)
2. **Data Files**: embeddings.json contains redundant strategy data
3. **Performance**: Consider lazy loading for About page content

---

## Success Metrics

1. **Reduced Cognitive Load**: Users understand the 3 strategies without confusion
2. **Increased Engagement**: Users explore multiple strategies via clear UI
3. **Better Shareability**: About page helps users of different levels engage
4. **Bug-Free Experience**: No more inverted sliders or confusing labels
5. **Preserved Personality**: Personal story and voice remain prominent

---

## Appendix: File Structure

### Current Structure
```
cocktail_cartography/
├── viz/
│   └── index.html          # Main visualization
├── data/
│   ├── embeddings.json     # UMAP coordinates
│   ├── recipes.json        # Cocktail recipes
│   └── ingredients.csv     # Ingredient profiles
├── About-CURIOUS.md        # General audience content
├── About-COCKTAIL_NERD.md  # Cocktail theory content
├── About-DATA_NERD.md      # Technical content
└── README*.md              # (To be removed)
```

### New Structure
```
cocktail_cartography/
├── viz/
│   ├── index.html          # Main visualization (updated)
│   └── about.html          # New About page
├── data/                   # (unchanged)
├── docs/
│   ├── plans/
│   │   └── ui-simplification-plan.md  # This document
│   └── content/
│       ├── About-CURIOUS.md
│       ├── About-COCKTAIL_NERD.md
│       └── About-DATA_NERD.md
└── README.md               # Technical documentation only
```

---

## Sign-off

This plan provides a comprehensive approach to simplifying and improving the Cocktail Cartography user interface. The changes maintain the project's analytical depth while making it more accessible to a general audience.

**Ready to proceed with implementation.**

---

## Implementation Notes

### Phase 1: Critical Fixes
- Fixed tooltip bug: changed `position: relative` to `position: absolute` on the tooltip element, resolving the broken hover/click cocktail information display.
- Swapped alpha slider labels so they correctly reflect the underlying data (left = "How it's made", right = "How it tastes").

### Phase 2: Strategy Simplification
- Removed the `blend` and `perceptual` strategies entirely from the UI.
- Renamed remaining strategies:
  - `tau` → **Perceptual Blend**
  - `blend_struct` → **Taste + Structure**
  - `role_slot` → **Recipe Grammar**
- Default strategy is now **Perceptual Blend** (tau).

### Phase 3: UI Reorganization
- Strategy descriptions collapse to title-only when not the active strategy; only the selected strategy expands to show its full description and controls.
- Display controls (color mode, highlight families, show labels) moved from the sidebar to a bottom sliding panel.
- Added an **About** link in the sidebar for navigation to the About page.

### Phase 4: About Page
- Created `viz/about.html` with a reader selection interface offering three personas: **Curious**, **cocktail nerd**, and **data nerd**.
- Content loaded from markdown files (`About-CURIOUS.md`, `About-COCKTAIL_NERD.md`, `About-DATA_NERD.md`, `About-COCKTAIL_DATA_NERD.md`) and rendered client-side via **marked.js**.
- Reader selection state persisted in the URL hash (e.g., `about.html#curious`, `about.html#cocktail`, `about.html#data`).
- Styled with Art Deco theme consistent with the main visualization (gold, cream, charcoal palette).

### Data Path Note
- Data path references use `../data/` for local development and `./data/` for production deployment.