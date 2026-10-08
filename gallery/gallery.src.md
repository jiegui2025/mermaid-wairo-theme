# Wairo theme gallery

Every diagram below uses the same theme, generated from one palette file. Colour only carries meaning, and every diagram carries a legend.

## Flowchart: workspace and packages (top to bottom)

```mermaid
flowchart TD
  tok[packages/tokens]:::ours --> lib[lib/ CSS and JSON]:::gen
  lib --> react[packages/react]:::ours
  react --> dist[dist/ build]:::gen
  react --> ladle[Ladle stories]
  dist --> app[Consumer app]:::ext
  ladle -.-> site[Designer preview site]:::new
  %% legend: gen = Generated output, never edited
```

## Flowchart: release critical path (left to right)

```mermaid
flowchart LR
  A[Tokens]:::ok --> B[Button]:::warn
  B --> C[Table]:::block
  B --> D[Pagination]:::warn
  C --> E[Pilot launch]:::risk
  D --> E
  %% legend: ok = Ready
  %% legend: warn = Planned this sprint
  %% legend: block = Blocked
  %% legend: risk = Date at risk
```

## Sequence: consumer install

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant Feed as Package registry
  participant App as Consumer app
  Dev->>Feed: publish @acme/ui
  Feed-->>Dev: version 0.4.0
  App->>Feed: pnpm add @acme/ui
  loop each dependency
    Feed-->>App: tarball
  end
  Note over App: smoke build runs here
```

## Gantt: release timeline

```mermaid
gantt
  dateFormat YYYY-MM-DD
  axisFormat %b %d
  section Sprint 5
  Tokens                :done, t1, 2026-10-14, 5d
  Button                :active, t2, 2026-10-16, 8d
  Table                 :crit, t3, 2026-10-20, 7d
  section Sprint 6
  Pagination            :t4, 2026-10-28, 6d
  Pilot                 :milestone, m1, 2026-11-09, 0d
  Sprint 6 ends         :t5, 2026-11-09, 2d
```

## Pie: test time by area

```mermaid
pie title Vitest time by area (s)
  "Components" : 41
  "Traits" : 18
  "Tokens" : 9
  "Setup" : 6
```

## Quadrant: value and effort

```mermaid
quadrantChart
  title Audit findings by value and effort
  x-axis Low effort --> High effort
  y-axis Low value --> High value
  quadrant-1 Plan
  quadrant-2 Do first
  quadrant-3 Later
  quadrant-4 Avoid
  CI cache: [0.25, 0.85]
  Ladle preview: [0.6, 0.75]
  Visual diff: [0.7, 0.55]
  Lint rule: [0.2, 0.3]
  %% legend: text = each point is one finding, placed by value (up) and effort (right)
```

## XY chart: CI step time

```mermaid
xychart-beta
  title "CI step time (s)"
  x-axis [install, lint, typecheck, test, build]
  y-axis "Seconds" 0 --> 140
  bar "Before" [96, 31, 44, 118, 63]
  line "After" [38, 27, 40, 72, 51]
```

## Mindmap: architecture

```mermaid
mindmap
  root((Design system))
    Tokens
      core
      brand colours
      palettes
    React
      components
      traits
      styles
    Tooling
      Biome
      Vitest
      Ladle
```

## State: pull request

```mermaid
stateDiagram-v2
  [*] --> Draft
  Draft --> Review: ready
  Review --> Changes: comments
  Changes --> Review: pushed
  Review --> Merged: approved
  Merged --> [*]
  class Merged ok
  class Changes warn
  %% legend: ok = Finished
  %% legend: warn = Waiting on the author
```

## Class: tokens model

```mermaid
classDiagram
  class Token {
    +string name
    +string value
    +resolve()
  }
  class Theme {
    +Token[] tokens
    +brand
  }
  class Palette {
    +scheme
  }
  Theme "1" --> "*" Token
  Palette --> Token
  %% legend: text = boxes are types; arrows point to what a type holds
```

## Entity relationship: releases

```mermaid
erDiagram
  PACKAGE ||--o{ VERSION : publishes
  VERSION ||--o{ CHANGESET : includes
  VERSION }o--|| FEED : "lives in"
  %% legend: text = crow's feet mark the many side
```

## Git graph: release branch flow

```mermaid
gitGraph
  commit id: "feat"
  branch feature
  commit id: "work"
  commit id: "test"
  checkout main
  merge feature
  commit id: "version" tag: "v0.4.0"
  %% legend: text = each branch has its own colour, named on its line
```
