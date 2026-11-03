---
version: alpha
name: Pré-filtro de renda
description: Visual identity of the Streamlit demo of the AI pre-screening for Brazilian proof-of-income documents. A calm, light financial tool where ink blue means action and green, red and amber mean only status.
colors:
  primary: "#1D4F91"
  on-primary: "#FFFFFF"
  primary-container: "#E8EFF8"
  surface: "#FFFFFF"
  surface-subtle: "#F2F5F8"
  on-surface: "#17222B"
  on-surface-muted: "#55636E"
  outline: "#DDE2E6"
  success: "#17703F"
  success-container: "#E4F3EA"
  error: "#B42318"
  error-container: "#FBE9E7"
  warning: "#8A5A00"
  warning-container: "#FDF1D8"
  neutral: "#5F6B74"
  neutral-container: "#ECEFF1"
typography:
  headline-display:
    fontFamily: IBM Plex Sans
    fontSize: 2.4rem
    fontWeight: 700
    lineHeight: 1.15
  headline-display-mobile:
    fontFamily: IBM Plex Sans
    fontSize: 1.8rem
    fontWeight: 700
    lineHeight: 1.15
  kpi-lg:
    fontFamily: IBM Plex Sans
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1.15
    fontFeature: '"tnum"'
  kpi-md:
    fontFamily: IBM Plex Sans
    fontSize: 1.5rem
    fontWeight: 700
    lineHeight: 1.2
    fontFeature: '"tnum"'
  body-lg:
    fontFamily: IBM Plex Sans
    fontSize: 1.2rem
    fontWeight: 400
    lineHeight: 1.5
  headline-sm:
    fontFamily: IBM Plex Sans
    fontSize: 1.05rem
    fontWeight: 700
    lineHeight: 1.3
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: IBM Plex Sans
    fontSize: 0.9rem
    fontWeight: 400
    lineHeight: 1.45
  caption:
    fontFamily: IBM Plex Sans
    fontSize: 0.86rem
    fontWeight: 400
    lineHeight: 1.45
  label-caps:
    fontFamily: IBM Plex Sans
    fontSize: 0.76rem
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.06em
  label-chip:
    fontFamily: IBM Plex Sans
    fontSize: 0.74rem
    fontWeight: 600
    lineHeight: 1.4
rounded:
  bar: 4px
  card: 10px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  bar-height: 8px
  status-stripe: 5px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body-sm}"
  hero-badge:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.primary}"
    typography: "{typography.label-chip}"
    rounded: "{rounded.full}"
    padding: 4px
  step-card:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.card}"
    padding: 16px
  step-number:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
    size: 28px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.card}"
    padding: 16px
  card-caption:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface-muted}"
    typography: "{typography.caption}"
  kpi-tile:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.kpi-lg}"
    rounded: "{rounded.card}"
    padding: 16px
  client-message:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.card}"
    padding: 16px
  meter-track:
    backgroundColor: "{colors.neutral-container}"
    rounded: "{rounded.bar}"
    height: 8px
  meter-fill:
    backgroundColor: "{colors.primary}"
    rounded: "{rounded.bar}"
    height: 8px
  chip-counts-as-income:
    backgroundColor: "{colors.success-container}"
    textColor: "{colors.success}"
    typography: "{typography.label-chip}"
    rounded: "{rounded.full}"
  chip-not-income:
    backgroundColor: "{colors.neutral-container}"
    textColor: "{colors.neutral}"
    typography: "{typography.label-chip}"
    rounded: "{rounded.full}"
  status-pass:
    backgroundColor: "{colors.success-container}"
    textColor: "{colors.success}"
    typography: "{typography.label-chip}"
    rounded: "{rounded.full}"
  status-reject:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
    typography: "{typography.label-chip}"
    rounded: "{rounded.full}"
  status-review:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    typography: "{typography.label-chip}"
    rounded: "{rounded.full}"
  status-not-evaluated:
    backgroundColor: "{colors.neutral-container}"
    textColor: "{colors.neutral}"
    typography: "{typography.label-chip}"
    rounded: "{rounded.full}"
  alert-warning:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    rounded: "{rounded.card}"
    padding: 12px
---

# Pré-filtro de renda

## Overview

A personal AI PM lab shown to three audiences: applicants who send pay stubs, credit analysts who confirm the
decision, and portfolio visitors (recruiters, PMs) who have about ten seconds to understand the product. The look
is a calm, light financial tool: white surfaces like the paper of a pay stub, one ink blue for everything the
reader can act on, and status colors that never decorate. Text is plain Portuguese (or English in the English
mode) and every number answers a question someone without context would ask.

The base theme is fixed to light (`.streamlit/config.toml`, `base = "light"`): Streamlit accepts one palette for
the interface, so the app does not follow the operating system's dark mode.

## Colors

- **Ink blue (`primary`, #1D4F91):** actions, selection, focus, links, the tour progress and the meter fills.
  It never means a result. White text on it reaches 8.14:1. It replaced a petrol blue that sat too close to the
  approval green (ΔE 45 against 77 for ink blue).
- **Text (`on-surface`, #17222B; `on-surface-muted`, #55636E):** body text at 16.15:1 and captions at 6.18:1 on
  white.
- **Surfaces (`surface`, `surface-subtle`, `outline`):** white page and cards, #F2F5F8 for the "how it works"
  steps and the message sent to the applicant, #DDE2E6 for borders.
- **Status (`success`, `error`, `warning`, `neutral`, each with a `-container` background):** pre-approved or
  passed, rejected, human review and not evaluated. Text on its container: 5.34:1, 5.61:1, 5.29:1 and 4.73:1.
  Red and amber are nearly identical for people with deuteranopia (ΔE 2.2), so a status is never told by color
  alone: it always carries its own icon shape and a word.

## Typography

IBM Plex Sans everywhere, loaded from Google Fonts by the theme. It reads as a financial product and has tabular
figures for amounts.

- **headline-display:** the page title in the hero (1.8rem on phones).
- **kpi-lg / kpi-md:** the big numbers in the results tiles and in the proof strip of the hero, with tabular
  figures.
- **body-lg:** the one-sentence value proposition under the title.
- **headline-sm:** titles of the results panels.
- **body-md / body-sm / caption:** running text, rows of the extraction cards and the bars, notes under panels.
- **label-caps:** uppercase group titles of the extraction cards and of the proof strip.
- **label-chip:** badges and chips.

## Layout

Streamlit's wide layout, one column of sections. Grids of cards use a 12px gap and collapse at 760px: the three
"how it works" steps stack, the four result tiles become two columns and the results panels become one. The case
page always reads in the same order: result card, then "1. The AI read", "2. The rules decided" and "3. The
analyst was told". Spacing follows a 4px base (4, 8, 12, 16, 24).

## Elevation & Depth

Flat. Hierarchy comes from borders, the subtle surface and type weight, not shadows. The only inset shadows are
the 5px status stripe on the left of the result card and the 4px stripe on the rule that decided the case; the
open tour card gets a 2px ink-blue ring.

## Shapes

Cards and panels use a 10px radius; badges, chips and the step numbers are fully rounded; meter bars are 8px tall
with 4px rounded ends.

## Components

- **Result card:** bordered card with the status stripe, the decision as a heading with its icon, the main reason,
  the rule count, the "Simulate policy" popover and, beside it, the message sent to the applicant.
- **Extraction cards:** label on the left, value on the right; "Who and when", "Amounts" (net pay emphasized),
  "How the document arrived" and the earnings lines with the "counts as income" chip. A missing value is shown
  in italic neutral text, never as `null`.
- **Rule rows:** each rule is a plain-language question with a one-sentence answer; rules that did not pass come
  first in bordered cards, the deciding one with the stripe; rules that passed are collapsed.
- **KPI tile:** a question, the answer in `kpi-lg` ink blue and one line of context.
- **Meter:** label and "x of y · z%" on one line, the bar below; one hue for one measure.
- **Status badge:** icon and word in the status color on its container. Icons: check circle (pass), cancel
  (reject), warning triangle (review), dash (not evaluated).

## Do's and Don'ts

- Do use ink blue only for what can be clicked, selected or measured as progress.
- Don't put red on a button or a selected state: red only means "rejected".
- Do pair every status color with its icon shape and a word.
- Don't show rule codes (R7), OCR word counts, file names or raw codes (`payslip`, `null`) to the reader.
- Do write every metric as a question with its answer and one line of context.
- Don't show English text in the Portuguese mode.
- Don't introduce a color, font or radius that is not in this file; add it here first, with its reason.
