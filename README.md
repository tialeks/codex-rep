# Figma SP Operations

AI workspace for optimizing Figma design operations.

## Purpose

This project is designed to work with Figma files through MCP and automate design workflows:

- design system audits
- component analysis
- conflict detection
- UX scenario reviews
- Figma file creation and modification
- design process optimization

## Structure

- `AGENTS.md` — project instructions and skill routing
- `skills/` — reusable AI workflows and rules
- `docs/` — project documentation
- `lib/` — imported design-system code and assets

## Workflow

Figma → MCP → AI analysis → GitHub documentation and automation

## Loading instructions

Codex reads `AGENTS.md` when working inside this checkout. Skills remain in the existing `skills/` paths and are routed by `AGENTS.md`; keeping them on GitHub alone does not automatically install them into ChatGPT Work. Load only the relevant skill.
