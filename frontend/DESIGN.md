---
name: "PrivaTools — Air and Play"
description: "Two distinct consumer experiences sharing one functional application."
updated: "2026-09-13"
experiences:
  air:
    light: "Morning Mist"
    dark: "Graphite"
    background-light: "#edf3f9"
    background-dark: "#151619"
    action-light: "#285cc7"
    action-dark: "#91b5ff"
    font: "Manrope"
  play:
    light: "Blush"
    dark: "Charcoal"
    background-light: "#fae7eb"
    background-dark: "#181818"
    action-light: "#a32749"
    action-dark: "#ff9677"
    body-font: "Outfit"
    heading-font: "Bricolage Grotesque"
---

# PrivaTools design system

The user selected Air and Play and their four appearance palettes on 13 September 2026. This document describes the shipped local implementation; previous visual directions are superseded.

## Shared behavior

The same stable application owns routing, processing, files, account state and the local password vault. `ExperienceShell` changes navigation presentation without changing the mounted workspace ancestry. Never key the application or processor by experience or appearance. Processor keys use the tool slug only.

`useExperience()` stores Air/Play independently of light/dark/system. It synchronizes same-tab, cross-tab and operating-system changes, supports blocked storage, and coordinates the prepaint theme. Root attributes are `data-experience`, `data-appearance` and `data-theme`.

## Navigation

Both experiences use a sticky top navbar. Air is full-width with a quiet bottom rule; Play is a floating rounded bar. Desktop links expose All tools, Pipeline, Batch, AI Studio, Vault and Dev API, followed by My Stuff. AI Studio, Vault and Dev API remain direct links in a second top row on phones and tablets. Remaining destinations, quick tour and keyboard shortcuts are in the accessible menu. There is no global sidebar or bottom navigation.

## Air

An open studio with content up to 1240px and 40px desktop gutters. Manrope handles headings and body text. Morning Mist is cool and soft; Graphite is neutral with blue actions. Headers reach 58px, reducing to 38px on phones. Panels use 22px radii and fine borders. A compact category index sits beside the tool library. Tool settings sit beside the canvas; Pipeline uses an orderly chain; account and API pages pair focused controls with useful context. The policy reader has a sticky left contents column.

Air enters with a 9px upward fade over 420ms. Progress follows actual work; there are no fake completion timers.

## Play

A personal workshop with Bricolage Grotesque headings and Outfit body text. Blush uses raspberry actions; Charcoal uses warm coral actions. Colored papers carry paired foregrounds, including in dark mode. Headers reach 66px; panels use 24–30px radii, tactile shadows and pill actions.

Layouts change as well as colors: categories become a horizontal shelf and the library uses three columns; tool settings move to a horizontal work shelf; Batch uses job cards; the Vault form moves to the left; AI uses a horizontal studio navigation; API connection and example panels swap positions. Support puts its contact note beside the answer shelf; documents become a broad rounded reading sheet below chapter navigation. Advanced editors preserve their specialized controls inside the new workspace composition.

Play entrances use a small rotation, scale and overshoot over 550ms. Hover details lift or gently rotate paper objects. The same input nodes stay mounted through Air/Play changes.

## Components and accessibility

Self-host fonts. Keep semantic Tailwind tokens as HSL triplets in `tokens.css`; experience surfaces and color pairs live in `experience.css`. Secondary-page and workflow styling are isolated in their own stylesheets.

Use visible keyboard focus, proper labels, real disabled states and accessible progress. Respect reduced motion for all entrances, transitions, connectors and scroll navigation. Top navigation stays accessible on mobile; panels stack and long code/chapters scroll within their own containers. Labels wrap inside narrow provider controls. Native dialogs manage focus and dismissal.

Status, file counts and percentages come from real state. No simulated success, invented uptime or certification claims. Local tools, temporary server processing and user-selected AI providers have different disclosures. A saved password is encrypted locally; a server operation may receive the password needed for that job.

## PWA

One compact install/offline entry opens the PWA controls. Native installation is offered when available; other browsers receive platform instructions. Updates wait for an explicit reload decision. Only static assets enter the app cache; private API/account/file responses are excluded. Production build hashes version the worker. The manifest includes real Air/Play desktop and mobile screenshots.

## Source and verification

- `src/skins/experience/ExperienceShell.tsx` and `ExperienceHome.tsx`
- `src/skins/experience/Studio.tsx`, `ToolWorkspace.tsx`, `ToolStudio.tsx`, `ContentStudio.tsx`, `DocumentStudio.tsx`
- `src/skins/experience/navigation.css`, `studio.css`, `content.css`, `documents.css`, `tool-workspace.css`, `tool-studio.css`, `workflows.css`, `secondary-pages.css`
- `src/lib/experience.ts`
- `src/components/pwa/`, `public/sw.js`, `public/manifest.json`

Keep browser checks, screenshots and backend-output evidence in local release records. Do not publish account-specific audit artifacts.
