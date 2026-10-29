# ADR 0001: No CSS framework in v1
Date: 2026-10-25

## Status

Accepted

## Context

The account UI is a shell and a handful of forms. The subject forbids a dependency that has no PHP standard-library equivalent, and it grades what is in the git directory. A CSS-only stylesheet such as Pico would be legal if the file lived in the repo, because the browser would not fetch it from elsewhere and the app would not import it; a JavaScript framework would not be. The screens are specified in [the design](../../DESIGN.md), and later versions are the place to try frameworks.

## Decision

I will write the CSS myself in `public/app.css`, so v1 takes no CSS framework and no component library.

## Consequences

Every screen is my own layout, so a missing design section shows up as a plain page instead of being hidden by a framework. A v2 that vendors a CSS-only framework reopens this ADR, and a JavaScript UI framework stays out while this subject applies.
