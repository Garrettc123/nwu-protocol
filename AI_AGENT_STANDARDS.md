# AI Agent Branch Standards

## Overview

This document describes the relaxed standards enforcement for AI agent branches in the NWU Protocol repository.

## Purpose

AI agents (Claude, Copilot) often generate descriptive PR descriptions and commit messages that provide valuable context but may not follow strict templates. This policy balances maintaining code quality standards while allowing AI agents the flexibility to contribute effectively.

## Branch Naming

AI agent branches are identified by their prefix:
- `claude/` - Claude AI agent branches
- `copilot/` - GitHub Copilot agent branches

These branches are automatically allowed by the branch naming standards check.

## Relaxed Validation Rules

### PR Description Validation

**Human Branches (feat/, fix/, etc.):**
- Must include all sections from PR template:
  - `## Description`
  - `## Type of Change`
  - `## Definition of Done Checklist`
  - `## Testing Performed`
- Must have checkboxes for Definition of Done items

**AI Agent Branches (claude/, copilot/):**
- Must have at least 100 characters of meaningful content
- No specific template sections required
- Recommended: Include clear description of changes, components affected, and testing approach

### Commit Message Validation

**Human Branches:**
- ALL commits must follow Conventional Commits format
- Format: `type(scope): description`
- Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `security`, `perf`, `ci`, `revert`

**AI Agent Branches:**
- At least ONE commit must follow Conventional Commits format
- Other commits can have descriptive messages without strict format
- Encourages meaningful commit messages while allowing flexibility

### Branch Naming

**Human Branches:**
- Must use standard prefixes: `feat/`, `fix/`, `docs/`, `style/`, `refactor/`, `test/`, `chore/`, `security/`, `perf/`, `ci/`

**AI Agent Branches:**
- `claude/` prefix is automatically allowed
- `copilot/` prefix is automatically allowed

## Examples

### Good AI Agent PR Description

```markdown
Implements an autonomous AI system that manages business operations 24/7 by dynamically creating and coordinating specialized agents for different business functions.

## Core Components

**Business Cooperation Lead Agent** - Autonomous business manager that analyzes tasks...
**Agent Factory** - Dynamic agent creation system supporting 12 specialized types...

## Specialized Agents (12 Types)
- Sales: lead generation, client outreach, deal closing
- Marketing: content creation, campaigns, analytics
...
```

### Good AI Agent Commits

```
feat: Add Business Cooperation Lead Agent system with specialized agents
Add validation scripts for business cooperation agent system
Add README for business-lead agent directory
```

At least one commit (`feat: Add Business...`) follows conventional format, others are descriptive.

## Implementation

The relaxed validation is implemented in `.github/workflows/standards-enforcement.yml`:

1. **PR Checklist Validation** (lines 23-89)
   - Detects AI branch with regex: `/^(claude|copilot)\//`
   - Requires 100+ characters instead of template sections

2. **Branch Naming** (lines 91-117)
   - Includes `claude/` and `copilot/` in valid prefixes list

3. **Commit Message Validation** (lines 119-217)
   - Detects AI branch with regex: `^(claude|copilot)/`
   - Checks for at least one conventional commit instead of all commits

## Rationale

1. **AI Context**: AI agents often generate comprehensive, well-structured PR descriptions that don't match templates but provide excellent context
2. **Commit History**: AI agents may make iterative commits with descriptive messages that are valuable for understanding the development process
3. **Quality Maintenance**: Still requires minimum standards (content length, at least one proper commit) to ensure quality
4. **Human Standards**: Maintains strict standards for human contributors to ensure consistency and best practices

## Future Considerations

- Monitor AI-generated PRs for quality and adjust thresholds as needed
- Consider adding AI-specific quality checks (e.g., test coverage requirements)
- May expand to other AI agent systems as they emerge

## Related Files

- `.github/workflows/standards-enforcement.yml` - Standards enforcement workflow
- `.github/PULL_REQUEST_TEMPLATE.md` - PR template for human contributors
- `DEFINITION_OF_DONE.md` - Overall quality standards
- `CHANGELOG.md` - Project changelog

---

**Version**: 1.0  
**Last Updated**: 2026-02-18  
**Owner**: Tiger Team
