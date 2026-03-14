# PR Automation Guide

This document describes the automated PR workflows implemented in the NWU Protocol repository.

## Overview

The repository includes comprehensive PR automation to streamline the development process, reduce manual overhead, and ensure consistent quality standards.

## Automated Features

### 1. Auto-Labeling (`pr-automation.yml`)

**Trigger**: When a PR is opened or synchronized

**What it does**:
- Automatically adds labels based on changed files (using `.github/labeler.yml`)
- Labels include: `area: backend`, `area: frontend`, `area: contracts`, `area: documentation`, etc.

**Configuration**: Edit `.github/labeler.yml` to customize labeling rules

---

### 2. PR Size Labeling (`pr-automation.yml`)

**Trigger**: When a PR is opened or updated

**What it does**:
- Calculates total lines changed (additions + deletions)
- Assigns size labels:
  - `size: XS` - Less than 10 changes
  - `size: S` - 10-99 changes
  - `size: M` - 100-499 changes
  - `size: L` - 500-999 changes
  - `size: XL` - 1000+ changes
- Posts a warning comment for PRs with 1000+ changes

**Why it matters**: Large PRs are harder to review and more error-prone

---

### 3. Auto-Assign Reviewers (`pr-automation.yml`)

**Trigger**: When a PR is opened

**What it does**:
- Reads `.github/CODEOWNERS` file
- Matches changed files to code owners
- Automatically requests reviews from relevant owners
- Skips the PR author
- Maximum 15 reviewers per GitHub API limits

**Configuration**: Edit `.github/CODEOWNERS` to define code ownership

---

### 4. Merge Conflict Detection (`pr-automation.yml`)

**Trigger**: When a PR is opened or updated

**What it does**:
- Detects merge conflicts with base branch
- Adds `status: conflict` label
- Posts instructions on how to resolve conflicts
- Removes label when conflicts are resolved

---

### 5. First-Time Contributor Welcome (`pr-automation.yml`)

**Trigger**: When a PR is opened

**What it does**:
- Detects if this is the user's first PR to the repository
- Posts a friendly welcome message with:
  - Overview of the review process
  - Links to contributing guidelines
  - Encouragement and support
- Adds `first-time contributor` label

---

### 6. PR Summary Generation (`pr-automation.yml`)

**Trigger**: When a PR is opened or synchronized

**What it does**:
- Analyzes all changed files
- Categorizes changes (backend, frontend, contracts, tests, docs, config)
- Posts a summary comment with:
  - Total files changed
  - Lines added/deleted
  - Breakdown by category
- Updates the comment on subsequent pushes

---

### 7. Auto-Approval (`auto-merge.yml`)

**Trigger**: When a PR is opened

**What it does**:
- Automatically approves PRs that meet safety criteria:
  - From `dependabot[bot]`
  - Documentation-only changes (less than 10 lines)
  - Minor config changes (less than 10 lines)
- Posts approval with reason

**Why it's safe**: Only applies to low-risk changes that don't affect functionality

---

### 8. Auto-Merge (`auto-merge.yml`)

**Trigger**: When a PR is approved, updated, or CI completes

**What it does**:
- Checks if PR meets merge criteria:
  - Not a draft
  - No `no-auto-merge` label
  - Has `auto-merge` label OR is from dependabot
  - At least 1 approval
  - No changes requested
  - All CI checks pass
  - No merge conflicts
- Enables auto-merge with squash method
- Falls back to direct merge if auto-merge fails

**How to use**:
- Add `auto-merge` label to any PR you want to auto-merge
- For dependabot PRs, auto-merge happens automatically after approval

**How to prevent**:
- Add `no-auto-merge` label to any PR

---

### 9. Stale PR Detection (`stale-pr-management.yml`)

**Trigger**: Daily at 00:00 UTC, or manual trigger

**What it does**:
- Checks all open PRs for inactivity
- After 14 days of inactivity:
  - Adds `status: stale` label
  - Posts notice with 16-day warning before closure
- After 30 days total inactivity:
  - Posts closure notice
  - Closes the PR
- Removes stale label if PR becomes active again
- Skips draft PRs and PRs with `no-stale` label

**How to prevent**:
- Add `no-stale` label to important PRs
- Add any comment or push to refresh the timer

---

### 10. Waiting-on-Author Tracking (`stale-pr-management.yml`)

**Trigger**: Daily at 00:00 UTC

**What it does**:
- Detects PRs with "changes requested" reviews
- Adds `status: waiting-on-author` label
- After 7 days, sends reminder to PR author
- Helps ensure PRs don't get forgotten

---

### 11. Automated PR Creation (`auto-pr.yml`)

**Trigger**: 
- Manual trigger with workflow_dispatch
- Weekly schedule (Monday 9:00 AM UTC)

**Types of automated PRs**:

#### a) Dependency Updates
- Checks for outdated npm packages
- Creates PR with updates
- Adds `dependencies`, `auto-merge`, `automated` labels

#### b) Weekly Maintenance Report
- Scans for TODO/FIXME comments
- Creates maintenance issue (not PR)
- Lists recommended actions
- Adds `maintenance`, `automated` labels

#### c) Security Vulnerability Check
- Runs `npm audit`
- Creates issue if vulnerabilities found
- Adds `security`, `high-priority`, `automated` labels

---

## Labels Used

### Status Labels
- `status: stale` - PR inactive for 14+ days
- `status: conflict` - PR has merge conflicts
- `status: waiting-on-author` - Changes requested by reviewer

### Size Labels
- `size: XS`, `size: S`, `size: M`, `size: L`, `size: XL`

### Area Labels
- `area: backend`, `area: frontend`, `area: contracts`, `area: ai-agents`
- `area: infrastructure`, `area: database`, `area: documentation`
- `area: tests`, `area: configuration`

### Other Labels
- `auto-merge` - Enable auto-merge for this PR
- `no-auto-merge` - Prevent auto-merge
- `no-stale` - Prevent stale detection
- `first-time contributor` - First PR from this user
- `dependencies` - Dependency updates
- `security` - Security-related
- `automated` - Created by automation

---

## Usage Examples

### Enable Auto-Merge for a PR
```
1. Ensure PR has all required approvals
2. Add the `auto-merge` label
3. PR will merge automatically when all checks pass
```

### Prevent a PR from Going Stale
```
1. Add the `no-stale` label
2. PR will never be marked as stale or auto-closed
```

### Manually Trigger Dependency Update
```
1. Go to Actions tab
2. Select "Auto PR Creation" workflow
3. Click "Run workflow"
4. Select "dependency-update"
5. Click "Run workflow"
```

### Request Auto-Approval for Safe Changes
```
Auto-approval happens automatically for:
- Dependabot PRs
- Documentation-only PRs (<10 lines)
- Minor config PRs (<10 lines)

No action needed from you!
```

---

## Configuration Files

- **`.github/workflows/pr-automation.yml`** - Main PR automation
- **`.github/workflows/auto-merge.yml`** - Auto-approval and merging
- **`.github/workflows/stale-pr-management.yml`** - Stale PR handling
- **`.github/workflows/auto-pr.yml`** - Automated PR creation
- **`.github/labeler.yml`** - File-based labeling rules
- **`.github/CODEOWNERS`** - Code ownership for reviewer assignment

---

## Customization

### Adjust Stale Timeframes

Edit `.github/workflows/stale-pr-management.yml`:
```yaml
const STALE_DAYS = 14;  # Days before marking stale
const CLOSE_DAYS = 30;  # Days before auto-closing
```

### Adjust PR Size Thresholds

Edit `.github/workflows/pr-automation.yml`:
```yaml
if (totalChanges < 10) {        # XS
} else if (totalChanges < 100) { # S
} else if (totalChanges < 500) { # M
} else if (totalChanges < 1000) { # L
} else {                         # XL
```

### Add Custom Labels

Edit `.github/labeler.yml`:
```yaml
'my-custom-label':
  - path/to/files/**/*
```

---

## Best Practices

1. **Use conventional branch names**: `feat/`, `fix/`, `docs/`, etc. (required by standards-enforcement.yml)

2. **Fill out PR template**: Automated checks verify template sections

3. **Keep PRs focused**: Smaller PRs get the `size: S` or `size: XS` label and are easier to review

4. **Add `auto-merge` for routine updates**: Let automation handle low-risk merges

5. **Use `no-stale` sparingly**: Only for long-running feature branches

6. **Watch for bot comments**: Automated messages provide helpful guidance

---

## Troubleshooting

**Q: Why wasn't my PR auto-labeled?**
- Check that `.github/labeler.yml` has rules matching your file paths
- Workflow must have `pull-requests: write` permission

**Q: Why didn't auto-merge work?**
- Verify all CI checks passed
- Ensure at least 1 approval exists
- Check for `no-auto-merge` label
- Confirm no merge conflicts

**Q: How do I stop a PR from being marked stale?**
- Add the `no-stale` label
- Or add a comment to reset the inactivity timer

**Q: Can I customize the automation?**
- Yes! Edit the workflow files in `.github/workflows/`
- PRs with workflow changes are welcome

---

## Support

For issues or questions about PR automation:
1. Check this guide
2. Review workflow logs in the Actions tab
3. Open an issue with the `automation` label
4. Contact maintainers

---

**Last Updated**: 2026-02-14
**Workflows Version**: 1.0.0
