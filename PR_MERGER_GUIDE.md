# PR Merger Guide

A comprehensive tool for managing and merging multiple pull requests efficiently and safely.

## Overview

The PR Merger script (`scripts/pr-merger.sh`) is designed to help maintainers manage and merge multiple pull requests in the repository. It provides automated checks for merge readiness and supports batch operations to streamline the merge process.

## Features

- **List PRs**: View all open pull requests with their status
- **Check Readiness**: Verify if a PR is ready to merge (checks for conflicts, reviews, drafts)
- **Single Merge**: Merge individual PRs with safety checks
- **Batch Merge**: Merge multiple PRs in one operation
- **Auto Merge**: Automatically identify and merge all ready PRs
- **Dry Run Mode**: Test operations without making actual changes
- **Flexible Merge Methods**: Support for squash, merge, and rebase strategies

## Prerequisites

### 1. GitHub CLI (gh)

The script requires the GitHub CLI tool. Install it if you haven't already:

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Debian/Ubuntu
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

**Windows:**
```bash
winget install --id GitHub.cli
```

### 2. Authentication

Authenticate with GitHub:
```bash
gh auth login
```

Follow the prompts to authenticate. You'll need:
- A GitHub account with push access to the repository
- Personal access token or web-based authentication

## Usage

### Basic Commands

#### List All Open PRs
View all open pull requests with their current status:

```bash
./scripts/pr-merger.sh list
```

Output includes:
- PR number and title
- Author
- Draft status
- Mergeable status (conflicts detected)
- Review decision
- Number of status checks

#### Check PR Readiness
Verify if a specific PR is ready to merge:

```bash
./scripts/pr-merger.sh check <PR_NUMBER>
```

Example:
```bash
./scripts/pr-merger.sh check 88
```

The script checks:
- ✓ PR is not a draft
- ✓ No merge conflicts
- ✓ No changes requested in reviews
- ⚠️ Reviews (informational only, doesn't block)

#### Merge a Single PR
Merge a specific pull request:

```bash
./scripts/pr-merger.sh merge <PR_NUMBER>
```

Example:
```bash
./scripts/pr-merger.sh merge 88
```

#### Batch Merge Multiple PRs
Merge several PRs in one operation:

```bash
./scripts/pr-merger.sh batch <PR_NUMBER1> <PR_NUMBER2> <PR_NUMBER3>
```

Example:
```bash
./scripts/pr-merger.sh batch 84 86 87 88
```

The script will:
1. Check each PR for readiness
2. Merge ready PRs sequentially
3. Skip PRs that aren't ready
4. Provide a summary at the end

#### Auto-Merge All Ready PRs
Automatically find and merge all PRs that are ready:

```bash
./scripts/pr-merger.sh auto
```

This will:
1. Scan all open PRs
2. Identify those ready to merge
3. Display the list
4. Ask for confirmation
5. Merge all confirmed PRs

### Advanced Options

#### Dry Run Mode
Test what would happen without actually merging:

```bash
DRY_RUN=true ./scripts/pr-merger.sh auto
```

Or:
```bash
export DRY_RUN=true
./scripts/pr-merger.sh merge 88
```

#### Custom Merge Method
Choose between different merge strategies:

```bash
# Squash merge (default) - combines all commits into one
MERGE_METHOD=squash ./scripts/pr-merger.sh merge 88

# Regular merge - keeps all commits
MERGE_METHOD=merge ./scripts/pr-merger.sh merge 88

# Rebase merge - replays commits on base branch
MERGE_METHOD=rebase ./scripts/pr-merger.sh merge 88
```

#### Custom Repository
Work with a different repository:

```bash
GITHUB_REPO_OWNER=myorg GITHUB_REPO_NAME=myrepo ./scripts/pr-merger.sh list
```

#### Custom Base Branch
Target a different base branch:

```bash
BASE_BRANCH=develop ./scripts/pr-merger.sh auto
```

## Configuration

### Environment Variables

The script can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_REPO_OWNER` | Repository owner | `Garrettc123` |
| `GITHUB_REPO_NAME` | Repository name | `nwu-protocol` |
| `BASE_BRANCH` | Target base branch | `main` |
| `DRY_RUN` | Enable dry run mode | `false` |
| `MERGE_METHOD` | Merge strategy | `squash` |

### Creating a Configuration File

For permanent settings, create a `.pr-merger.env` file:

```bash
# .pr-merger.env
export GITHUB_REPO_OWNER=Garrettc123
export GITHUB_REPO_NAME=nwu-protocol
export BASE_BRANCH=main
export MERGE_METHOD=squash
```

Then source it before running:
```bash
source .pr-merger.env
./scripts/pr-merger.sh auto
```

## Workflows

### Workflow 1: Weekly PR Cleanup

Merge all ready PRs every week:

```bash
# 1. Review what's ready
./scripts/pr-merger.sh list

# 2. Dry run to see what would merge
DRY_RUN=true ./scripts/pr-merger.sh auto

# 3. Merge all ready PRs
./scripts/pr-merger.sh auto
```

### Workflow 2: Selective Batch Merge

Merge specific PRs after review:

```bash
# 1. Check specific PRs
./scripts/pr-merger.sh check 84
./scripts/pr-merger.sh check 86
./scripts/pr-merger.sh check 87

# 2. Merge approved ones
./scripts/pr-merger.sh batch 84 86 87
```

### Workflow 3: Safe Testing

Test merge operations before running:

```bash
# 1. List PRs
./scripts/pr-merger.sh list

# 2. Test with dry run
DRY_RUN=true ./scripts/pr-merger.sh batch 88 89 90

# 3. Actually merge if test looks good
./scripts/pr-merger.sh batch 88 89 90
```

## Merge Readiness Criteria

A PR is considered "ready to merge" when:

### ✅ Required Criteria (Blocking)
- PR is not in draft status
- No merge conflicts with base branch
- No "changes requested" reviews

### ⚠️ Optional Criteria (Non-blocking)
- Review approval (warned but not blocked)
- Passing CI checks (warned but not blocked)

### ❌ Blocking Issues
- Draft PR
- Merge conflicts
- Changes requested

## Safety Features

### 1. Pre-Merge Validation
Every merge attempt includes automatic validation:
- Checks PR status
- Verifies no conflicts
- Confirms review status

### 2. Dry Run Mode
Test operations without making changes:
```bash
DRY_RUN=true ./scripts/pr-merger.sh auto
```

### 3. User Confirmation
Auto-merge requests confirmation before proceeding:
```
Found 3 PRs ready to merge:
  - PR #84
  - PR #86
  - PR #87

Do you want to merge these PRs? (y/N)
```

### 4. Sequential Processing
PRs are merged one at a time with delays to avoid:
- API rate limiting
- Concurrent merge conflicts
- System overload

### 5. Error Handling
Failed merges don't stop the batch:
- Continues to next PR
- Reports failures at end
- Provides summary statistics

## Troubleshooting

### Issue: "GitHub CLI (gh) is not installed"

**Solution:** Install the GitHub CLI following the prerequisites section.

### Issue: "Not authenticated with GitHub CLI"

**Solution:** Run `gh auth login` and follow the authentication prompts.

### Issue: "PR has merge conflicts"

**Solution:**
1. The PR needs to be updated to resolve conflicts
2. Have the PR author rebase or merge the base branch
3. Try again after conflicts are resolved

### Issue: "Changes requested in review"

**Solution:**
1. Address the requested changes
2. Push updates to the PR branch
3. Request re-review
4. Try merging again after approval

### Issue: "Permission denied"

**Solution:**
1. Verify you have push access to the repository
2. Check your GitHub token has the correct scopes
3. Re-authenticate with `gh auth login`

### Issue: "API rate limit exceeded"

**Solution:**
1. Wait for rate limit to reset (usually 1 hour)
2. Reduce batch size
3. Use authenticated requests (automatic with gh CLI)

## Integration with CI/CD

### GitHub Actions Example

Create `.github/workflows/auto-merge.yml`:

```yaml
name: Auto-merge Ready PRs

on:
  schedule:
    # Run daily at 9 AM UTC
    - cron: '0 9 * * *'
  workflow_dispatch: # Manual trigger

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup GitHub CLI
        run: |
          type -p gh >/dev/null || (
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg |
            sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
          )

      - name: Authenticate GitHub CLI
        run: echo "${{ secrets.GITHUB_TOKEN }}" | gh auth login --with-token

      - name: Auto-merge PRs
        run: |
          export GITHUB_REPO_OWNER="${{ github.repository_owner }}"
          export GITHUB_REPO_NAME="${{ github.event.repository.name }}"
          ./scripts/pr-merger.sh auto
```

## Best Practices

### 1. Review Before Merging
Always review PR content before batch merging:
```bash
./scripts/pr-merger.sh list
# Review each PR manually
./scripts/pr-merger.sh batch <selected_prs>
```

### 2. Use Dry Run First
Test operations with dry run:
```bash
DRY_RUN=true ./scripts/pr-merger.sh auto
```

### 3. Prefer Squash Merges
For cleaner history:
```bash
MERGE_METHOD=squash ./scripts/pr-merger.sh auto
```

### 4. Monitor CI Status
Check CI before merging:
```bash
./scripts/pr-merger.sh list
# Look at "Status Checks" count
```

### 5. Handle Conflicts Promptly
Don't merge PRs with conflicts:
- Address conflicts first
- Rebase or merge base branch
- Then retry merge

## Examples

### Example 1: Basic Weekly Cleanup

```bash
# Monday morning PR cleanup
./scripts/pr-merger.sh list
./scripts/pr-merger.sh auto
```

### Example 2: Careful Batch Merge

```bash
# Check each PR individually
for pr in 84 86 87 88; do
    echo "Checking PR #$pr"
    ./scripts/pr-merger.sh check $pr
done

# Merge the ready ones
./scripts/pr-merger.sh batch 84 86 87
```

### Example 3: Production Release

```bash
# Use merge commits for release
MERGE_METHOD=merge BASE_BRANCH=production ./scripts/pr-merger.sh batch 90 91 92
```

## Contributing

To improve the PR merger script:

1. Edit `scripts/pr-merger.sh`
2. Test with `DRY_RUN=true`
3. Update this documentation
4. Submit PR with changes

## Support

For issues or questions:
- Create an issue in the repository
- Tag maintainers for urgent matters
- Check GitHub CLI docs: https://cli.github.com/

## See Also

- [PR Automation Guide](PR_AUTOMATION.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [GitHub CLI Manual](https://cli.github.com/manual/)
