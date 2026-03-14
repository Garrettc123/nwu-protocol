# Automated Release Notes System

This document describes the automated release notes (RN) generation system for the NWU Protocol.

## Overview

The automated RN system generates structured, categorized release notes from git commit history using conventional commit format. It provides:

- **Automatic changelog generation** from git commits
- **Conventional commit parsing** for proper categorization
- **CHANGELOG.md maintenance** with version history
- **GitHub Release notes** with rich formatting
- **Manual and automatic workflows** for flexibility

## Conventional Commit Format

We use the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type       | Description                                      | Emoji |
|------------|--------------------------------------------------|-------|
| `feat`     | A new feature                                    | ✨    |
| `fix`      | A bug fix                                        | 🐛    |
| `docs`     | Documentation only changes                       | 📚    |
| `style`    | Changes that don't affect code meaning           | 💎    |
| `refactor` | Code change that neither fixes a bug nor adds a feature | ♻️ |
| `perf`     | Performance improvement                          | ⚡    |
| `test`     | Adding or correcting tests                       | ✅    |
| `build`    | Changes to build system or dependencies          | 🔨    |
| `ci`       | Changes to CI configuration                      | 👷    |
| `chore`    | Other changes that don't modify src or test files| 🔧    |
| `revert`   | Reverts a previous commit                        | ⏪    |
| `security` | Security improvements                            | 🔒    |

### Breaking Changes

To mark a commit as a breaking change:

1. Add `!` after the type: `feat!: remove deprecated API`
2. Or include `BREAKING CHANGE:` in the commit body

### Examples

```bash
# Feature with scope
feat(auth): add JWT token refresh mechanism

# Bug fix
fix: resolve memory leak in verification engine

# Breaking change
feat!: migrate to new API version

# Feature with body
feat(contributions): add file size validation

Add validation for uploaded files to ensure they don't exceed
the 100MB limit. Reject files that are too large with appropriate
error message.

# Breaking change with footer
feat(api): update response format

BREAKING CHANGE: API responses now use camelCase instead of snake_case
```

## Files

### Core Files

- **`CHANGELOG.md`** - Main changelog file tracking all releases
- **`scripts/generate-release-notes.js`** - Node.js script for generating release notes
- **`scripts/release-notes-helper.sh`** - Bash helper script for manual operations
- **`.github/workflows/release.yml`** - Automated release workflow

## Usage

### Manual Release Notes Generation

#### Preview Release Notes

```bash
# Preview release notes without making changes
./scripts/release-notes-helper.sh --preview

# Preview with specific version
./scripts/release-notes-helper.sh --version 1.2.0 --preview
```

#### Generate Compact Changelog

```bash
# Generate a compact summary of changes
./scripts/release-notes-helper.sh --compact
```

#### Update CHANGELOG.md

```bash
# Update CHANGELOG.md with new version
./scripts/release-notes-helper.sh --version 1.2.0 --update
```

### Using the Node.js Script Directly

```bash
# Generate release notes for preview
node scripts/generate-release-notes.js generate 1.2.0

# Update CHANGELOG.md
node scripts/generate-release-notes.js update 1.2.0

# Generate compact changelog
node scripts/generate-release-notes.js compact
```

### Automated Release Workflow

The automated release workflow runs when:

1. **Manual trigger** via GitHub Actions UI (workflow_dispatch)
2. **Automatic trigger** when package.json files are updated on main branch

#### Manual Trigger

1. Go to Actions → "📄 Automated Release"
2. Click "Run workflow"
3. Enter version (e.g., `1.2.0`)
4. Select component (`all`, `backend`, `frontend`, or `contracts`)
5. Click "Run workflow"

The workflow will:
- Generate version number (or use provided version)
- Generate compact and full release notes
- Update CHANGELOG.md
- Build and test components
- Publish to npm (if configured)
- Create GitHub release with full notes
- Notify via Discord/Slack

## Release Process

### Step-by-Step Release

1. **Ensure clean state**
   ```bash
   git status
   git pull origin main
   ```

2. **Review commits since last release**
   ```bash
   ./scripts/release-notes-helper.sh --preview
   ```

3. **Determine version number**
   - Follow [Semantic Versioning](https://semver.org/)
   - `MAJOR.MINOR.PATCH`
   - Breaking changes → MAJOR
   - New features → MINOR
   - Bug fixes → PATCH

4. **Update CHANGELOG.md**
   ```bash
   ./scripts/release-notes-helper.sh --version 1.2.0 --update
   ```

5. **Review and commit**
   ```bash
   git add CHANGELOG.md
   git commit -m "docs: Update CHANGELOG.md for v1.2.0"
   git push origin main
   ```

6. **Trigger release workflow**
   - Via GitHub Actions UI, or
   - By creating and pushing a tag:
     ```bash
     git tag -a v1.2.0 -m "Release v1.2.0"
     git push origin v1.2.0
     ```

### Automated Process

The workflow handles:
- Version management
- Changelog generation
- Component building and testing
- npm publishing
- Docker image building and pushing
- GitHub release creation
- Notifications

## CHANGELOG.md Structure

The CHANGELOG.md follows the [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements

## [1.2.0] - 2026-03-14

### ✨ Features
- Feature 1
- Feature 2

### 🐛 Bug Fixes
- Fix 1
- Fix 2

...

[Unreleased]: https://github.com/Garrettc123/nwu-protocol/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/Garrettc123/nwu-protocol/releases/tag/v1.2.0
```

## GitHub Release Notes

Release notes on GitHub include:

- **Version and date**
- **Commit count**
- **Categorized changes** (Breaking, Features, Fixes, etc.)
- **Commit links** for traceability
- **Contributors list**

Example:

```markdown
# Release 1.2.0

**Release Date:** 2026-03-14

**Commits:** 25

### 💥 BREAKING CHANGES

- auth: migrate to new API version ([a1b2c3d])

### ✨ Features

- **contributions**: add file size validation ([b2c3d4e])
- **api**: add rate limiting middleware ([c3d4e5f])

### 🐛 Bug Fixes

- resolve memory leak in verification engine ([d4e5f6g])
- **ui**: fix button alignment on mobile ([e5f6g7h])

### 👥 Contributors

- Garrett W. Carrol
- github-actions[bot]
```

## Best Practices

### Writing Good Commit Messages

1. **Use conventional format** - Follow the type(scope): subject pattern
2. **Be descriptive** - Explain what and why, not how
3. **Use imperative mood** - "add feature" not "added feature"
4. **Reference issues** - Include issue numbers when applicable
5. **Keep subject short** - 50 characters or less
6. **Add body for context** - Explain motivation and implementation

### Examples

✅ **Good:**
```
feat(auth): add OAuth2 support for Google login

Implements OAuth2 flow for Google authentication to provide
users with a convenient sign-in option. Includes token refresh
and profile fetching.

Closes #123
```

❌ **Bad:**
```
update stuff
```

### Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0 → 2.0.0)
  - Breaking changes
  - Incompatible API changes

- **MINOR** version (1.0.0 → 1.1.0)
  - New features
  - Backward compatible

- **PATCH** version (1.0.0 → 1.0.1)
  - Bug fixes
  - Backward compatible

### Pre-release Versions

- **Alpha**: `1.0.0-alpha.1`
- **Beta**: `1.0.0-beta.1`
- **Release Candidate**: `1.0.0-rc.1`

## Troubleshooting

### No commits found

**Issue**: "No changes since last release"

**Solution**:
- Check if you're on the correct branch
- Verify the last tag with `git tag -l`
- Ensure commits exist: `git log --oneline`

### Script not executable

**Issue**: Permission denied when running scripts

**Solution**:
```bash
chmod +x scripts/generate-release-notes.js
chmod +x scripts/release-notes-helper.sh
```

### Node.js not found

**Issue**: "Node.js is not installed or not in PATH"

**Solution**:
- Install Node.js 18 or later
- Verify with `node --version`

### Git tag issues

**Issue**: Can't create or push tags

**Solution**:
```bash
# Check existing tags
git tag -l

# Delete local tag
git tag -d v1.2.0

# Delete remote tag
git push origin :refs/tags/v1.2.0

# Create new tag
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

## Integration with CI/CD

The automated RN system integrates seamlessly with:

- **GitHub Actions** - Automated releases
- **npm** - Package publishing
- **Docker** - Image tagging
- **Discord/Slack** - Notifications

### GitHub Actions Workflow

The release workflow (`release.yml`) includes:

1. **prepare-release** job
   - Generates version
   - Creates compact and full release notes
   - Updates CHANGELOG.md
   - Commits changes

2. **component-release** jobs
   - Build and test
   - Update version in package.json
   - Publish to npm
   - Build and push Docker images

3. **create-release** job
   - Creates GitHub release
   - Uses full generated notes

4. **notify-release** job
   - Posts to Discord
   - Sends Slack message

## Future Enhancements

Potential improvements to the automated RN system:

- [ ] Support for monorepo independent versioning
- [ ] Automatic version bump detection from commits
- [ ] Release notes templates per component
- [ ] Integration with JIRA/Linear for issue linking
- [ ] Automatic migration guide generation for breaking changes
- [ ] Release candidate workflow
- [ ] Hotfix release workflow
- [ ] Multi-language release notes
- [ ] Release metrics and analytics

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)

## Support

For issues or questions:
- Open an issue on GitHub
- Review existing release notes for examples
- Check the troubleshooting section above
