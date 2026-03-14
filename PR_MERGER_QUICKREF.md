# PR Merger Tool - Quick Reference

## Installation

The PR Merger tool is already installed in the repository. Just ensure you have:

1. **GitHub CLI (gh)**
   ```bash
   # macOS
   brew install gh

   # Linux
   sudo apt install gh  # or equivalent

   # Windows
   winget install --id GitHub.cli
   ```

2. **Authenticate**
   ```bash
   gh auth login
   ```

## Quick Start

### Option 1: Direct Script Usage

```bash
# List all open PRs
./scripts/pr-merger.sh list

# Check if a PR is ready
./scripts/pr-merger.sh check 88

# Merge a single PR
./scripts/pr-merger.sh merge 88

# Batch merge multiple PRs
./scripts/pr-merger.sh batch 84 86 87 88

# Auto-merge all ready PRs
./scripts/pr-merger.sh auto
```

### Option 2: Using Make Commands

```bash
# List all open PRs
make pr-list

# Check if a PR is ready
make pr-check PR=88

# Merge a single PR
make pr-merge PR=88

# Batch merge multiple PRs
make pr-batch PRS='84 86 87 88'

# Auto-merge all ready PRs
make pr-auto

# Dry run (test without merging)
make pr-auto-dry
```

### Option 3: Using Convenience Symlink

```bash
# The merge-prs.sh symlink provides easy access
./merge-prs.sh list
./merge-prs.sh auto
```

## Common Workflows

### Weekly PR Cleanup
```bash
# 1. See what's open
make pr-list

# 2. Test with dry run
make pr-auto-dry

# 3. Merge all ready PRs
make pr-auto
```

### Selective Merge
```bash
# Check specific PRs
make pr-check PR=84
make pr-check PR=86
make pr-check PR=87

# Merge the ready ones
make pr-batch PRS='84 86 87'
```

### Safe Testing
```bash
# Always test first
DRY_RUN=true ./scripts/pr-merger.sh auto

# Then execute
./scripts/pr-merger.sh auto
```

## Merge Readiness Checks

A PR is ready to merge when:
- ✅ Not a draft
- ✅ No merge conflicts
- ✅ No changes requested in reviews
- ⚠️ Reviews are informational (not blocking)

## Configuration

Environment variables:
```bash
# Custom repository
GITHUB_REPO_OWNER=myorg GITHUB_REPO_NAME=myrepo ./scripts/pr-merger.sh list

# Dry run mode
DRY_RUN=true ./scripts/pr-merger.sh auto

# Change merge method (squash, merge, rebase)
MERGE_METHOD=merge ./scripts/pr-merger.sh merge 88

# Different base branch
BASE_BRANCH=develop ./scripts/pr-merger.sh auto
```

## Getting Help

```bash
# Show full help
./scripts/pr-merger.sh help

# Show make targets
make help

# Show examples
./pr-merger-examples.sh
```

## Full Documentation

For comprehensive documentation, see:
- **[PR_MERGER_GUIDE.md](PR_MERGER_GUIDE.md)** - Complete guide with examples, workflows, and troubleshooting
- **[README.md](README.md)** - Main project documentation

## Files

- `scripts/pr-merger.sh` - Main CLI tool
- `merge-prs.sh` - Convenience symlink
- `pr-merger-examples.sh` - Example commands
- `PR_MERGER_GUIDE.md` - Full documentation
- `Makefile` - Make targets for easy access

## Support

For issues or questions:
- Check the [PR_MERGER_GUIDE.md](PR_MERGER_GUIDE.md)
- Create an issue in the repository
- Consult GitHub CLI docs: https://cli.github.com/
