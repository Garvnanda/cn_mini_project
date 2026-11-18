---
name: NetArchitect
description: Network planning, explained.
colors:
  primary: "#126b61"
  background: "#eef3f3"
  panel: "#ffffff"
  foreground: "#183b3b"
  muted: "#536c6c"
  border: "#d4e1df"
  success: "#1a7f37"
  error: "#cf222e"
  warning: "#9a6700"
  copper: "#8c959f"
  multimode: "#bf3989"
  singlemode: "#e3b341"
  wan: "#0969da"
  path: "#2da44e"
  code-background: "#f0f3f6"
  header: "#153e3c"
  dark-background: "#0d1117"
  dark-panel: "#161b22"
  dark-foreground: "#e6edf3"
  dark-muted: "#9198a1"
  dark-border: "#30363d"
  dark-accent: "#4493f8"
  dark-button: "#245f9f"
  dark-success: "#3fb950"
  dark-error: "#f85149"
  dark-warning: "#d29922"
  dark-code-background: "#1f242c"
typography:
  display:
    fontFamily: '"Segoe UI", system-ui, sans-serif'
    fontSize: "clamp(30px, 3.4vw, 48px)"
    fontWeight: 650
    lineHeight: 1.13
    letterSpacing: "-.035em"
  headline:
    fontFamily: '"Segoe UI", system-ui, sans-serif'
    fontSize: "28px"
    lineHeight: 1.25
    letterSpacing: "-.025em"
  body:
    fontFamily: '"Segoe UI", system-ui, sans-serif'
    fontSize: "14px"
    lineHeight: 1.6
  lead:
    fontSize: "17px"
    lineHeight: 1.7
  code:
    fontFamily: 'ui-monospace, "Cascadia Code", Consolas, monospace'
    fontSize: "12.5px"
rounded:
  control: "6px"
  grouped-control: "8px"
  pill: "10px"
  result: "12px"
  panel: "14px"
spacing:
  compact: "4px"
  control-gap: "8px"
  toolbar: "16px"
  input-panel: "18px"
  panel: "22px"
  workspace: "28px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "6px 10px"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.control}"
    padding: "6px 10px"
  input:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.control}"
    padding: "6px 10px"
  panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.panel}"
    padding: "22px"
---

# Design System: NetArchitect

## Overview

**Creative North Star: "Network planning, explained."**

The implemented interface is a calm, readable workspace for learning and inspecting network plans. It pairs plain-language introductions with progressively revealed technical material. This captures the existing UI, not a new visual identity: PRODUCT.md leaves visual choices as provisional implementation judgment.

The light theme uses cool pale surfaces and a deep green header. The dark theme switches the workspace to charcoal and blue accents while retaining the header. Generous section spacing supports the dense tables, configuration text, and network diagrams.

**Key Characteristics:**

- Plain-language headings with detailed evidence available on demand.
- Flat bordered surfaces and restrained semantic color.
- Native controls, visible keyboard focus, and scrollable technical content.

Source: frontend/src/styles.css, App.tsx, InputPanel.tsx, Topology.tsx and panels.tsx, inspected 2026-11-18. This is implementation documentation, not accessibility certification or external network validation.

## Colors

### Primary

Deep teal identifies light-theme actions and selected controls. Dark mode separates bright blue accent/focus from the darker blue filled-button surface, preserving white button text.

### Secondary

Success green, error red, and warning amber communicate result states alongside text. The topology uses separate copper gray, multimode magenta, singlemode gold, WAN blue, and path green tokens. Dashed strokes distinguish trunks, underlay, and failed links.

### Neutral

Pale cool background, white panels, dark teal text, muted teal text, and pale borders establish the light theme. Charcoal equivalents establish dark mode. Code blocks have a distinct background in both themes. The header remains deep green.

Theme selection supports Auto, Light, and Dark. Auto follows prefers-color-scheme; an explicit choice is persisted in browser localStorage when available.

## Typography

The system uses the local Segoe UI/system sans-serif stack for display and body text; code uses the local monospace stack. No downloaded display font is required. Exact extracted roles are in the frontmatter.

Welcome text uses the responsive display role. View headings use the headline role; leads are larger and limited to 65ch. View descriptions are limited to 72ch, and guide list items to 75ch. Data tables use 13px text, 12px headers, and tabular numerals. Navigation uses 12px labels. The brand uses 21px, weight 700, and -.02em tracking, with an 11px subtitle.

## Layout

The desktop main grid has a 290px input column and a flexible minmax(0, 1fr) workspace, a 28px gap and padding, and a 1700px maximum width. Panels use a minimum width of zero so long content can scroll inside them. Workspace padding is 28px and minimum height is 72vh.

At 1100px and below, the sidebar becomes 260px and the main spacing and workspace padding become 20px. An earlier 900px single-column rule is overridden by that later 1100px rule: the effective single-column breakpoint is 800px. At 800px, main padding is 16px, the brand takes a full row, sidebar helper text hides, tabs scroll horizontally without wrapping, the glossary becomes one column, and workspace minimum height becomes automatic. At 460px, the three-step introduction stacks, toolbar fields fill their row, the header API link hides, and view headings become 24px.

Tables scroll horizontally. The network map lives in a focusable, labelled scroll region with an SVG minimum width of 780px and maximum height of 70vh. Print styles hide controls marked no-print, remove workspace borders, expand configuration text, and release map width/height limits.

## Elevation & Depth

The stylesheet defines no box shadows. Borders, background changes, whitespace, and typography separate levels. Verification banners mix the success or error token at 7% with the panel surface; failed topology nodes mix error at 15% with the panel surface.

## Shapes

Rounded rectangles define controls and containers, with the extracted radius scale in frontmatter. Decisions are flat rows separated by bottom borders rather than independently elevated cards. Summary chips use 12px rounding; compact rule pills use the pill radius. Topology strokes carry media and state information alongside labels and a legend.

## Components

### Buttons

Buttons are compact and explicit: weight 600, minimum height 38px, and base padding from frontmatter. Primary input-panel actions expand to full width with 12px padding. Secondary hover changes background to the page surface and border to accent. Primary hover mixes button background at 85% with black. Disabled buttons use opacity .5 and a default cursor. Background and border transitions last .18s with ease timing.

### Inputs / Fields

Native inputs, selects, and textareas share panel fill, a 1px border, and control rounding. Textareas fill available width and resize vertically. Placeholder text uses the muted token at full opacity; the caret uses accent. Labels use weight 600. Global focus-visible is a 3px solid accent outline offset by 3px.

### Navigation

Result navigation is a labelled nav of native buttons with aria-pressed, not an ARIA tablist. Active buttons have the filled primary treatment; other buttons have transparent backgrounds and muted text. Input-method buttons use a labelled group and aria-pressed. The mobile horizontal scroll behavior preserves the labels.

### Chips

Summary chips use a 1px border, 2px 10px padding, and 12.5px text. Rule pills use muted 11.5px text and 0 6px padding. These communicate metadata rather than acting as unimplemented filters.

### Cards / Containers

Panels use white or dark panel fill with a 1px border and panel rounding. Decision rows have 16px vertical padding. Results use result rounding, 18px padding and margin, and semantic left-border coloring while keeping body text in the normal foreground.

### Network map

Links are SVG lines; nodes are labelled SVG groups. Interactive links and eligible nodes expose button roles, keyboard focus, and Enter/Space activation. Hover increases link stroke width from 3px to 7px. Failed links use a dashed red stroke; selected paths use a thicker green stroke. The map includes a textual legend. Accessibility behavior is implemented, but comprehensive assistive-technology validation is not established by source inspection.

### Status and disclosure

Server state and copy feedback use role=status; design failures use role=alert. Native details/summary hides advanced material until requested. Reduced-motion preference disables animations, transitions and smooth scrolling globally.

## Do's and Don'ts

### Do:

- **Do** preserve plain-language orientation before dense technical evidence.
- **Do** use existing semantic tokens and retain dark-theme overrides.
- **Do** preserve visible focus, labelled controls, keyboard map interaction, and reduced-motion support.
- **Do** keep long tables, maps and code scrollable within their containers.

### Don't:

- **Don't** present simulator success as real-device certification.
- **Don't** replace text status and topology legends with color alone.
- **Don't** describe provisional visual choices as a user-approved permanent brand identity.
