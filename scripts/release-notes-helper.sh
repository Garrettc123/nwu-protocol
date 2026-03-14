#!/bin/bash

# Manual Release Notes Generator
# This script helps maintainers generate release notes manually

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   NWU Protocol Release Notes Generator      ║${NC}"
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo ""

# Function to display help
show_help() {
    echo "Usage: ./scripts/release-notes-helper.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -v, --version VERSION    Specify the release version (e.g., 1.2.0)"
    echo "  -c, --compact           Generate compact changelog"
    echo "  -u, --update            Update CHANGELOG.md with new release"
    echo "  -p, --preview           Preview release notes without updating files"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/release-notes-helper.sh --preview"
    echo "  ./scripts/release-notes-helper.sh --version 1.2.0 --update"
    echo "  ./scripts/release-notes-helper.sh --compact"
}

# Parse arguments
VERSION=""
COMPACT=false
UPDATE=false
PREVIEW=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -c|--compact)
            COMPACT=true
            shift
            ;;
        -u|--update)
            UPDATE=true
            shift
            ;;
        -p|--preview)
            PREVIEW=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed or not in PATH${NC}"
    exit 1
fi

# Get current information
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
CURRENT_BRANCH=$(git branch --show-current)
COMMITS_COUNT=$(git log ${LATEST_TAG}..HEAD --oneline 2>/dev/null | wc -l || echo "0")

echo -e "${GREEN}Current Status:${NC}"
echo "  Branch: $CURRENT_BRANCH"
echo "  Latest Tag: $LATEST_TAG"
echo "  Commits since last tag: $COMMITS_COUNT"
echo ""

if [ "$COMMITS_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}No commits since last release. Nothing to generate.${NC}"
    exit 0
fi

# Generate compact changelog
if [ "$COMPACT" = true ]; then
    echo -e "${BLUE}Generating compact changelog...${NC}"
    echo ""
    node scripts/generate-release-notes.js compact
    exit 0
fi

# Generate preview
if [ "$PREVIEW" = true ] || [ -z "$VERSION" ]; then
    if [ -z "$VERSION" ]; then
        VERSION="preview"
    fi
    echo -e "${BLUE}Generating preview for version $VERSION...${NC}"
    echo ""
    node scripts/generate-release-notes.js generate "$VERSION"
    exit 0
fi

# Update changelog
if [ "$UPDATE" = true ]; then
    if [ -z "$VERSION" ]; then
        echo -e "${RED}Error: Version required for update. Use -v or --version${NC}"
        exit 1
    fi

    echo -e "${BLUE}Updating CHANGELOG.md for version $VERSION...${NC}"
    node scripts/generate-release-notes.js update "$VERSION"

    echo ""
    echo -e "${GREEN}✅ CHANGELOG.md updated successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Review the changes in CHANGELOG.md"
    echo "  2. Commit the updated changelog:"
    echo "     git add CHANGELOG.md"
    echo "     git commit -m \"docs: Update CHANGELOG.md for v$VERSION\""
    echo "  3. Create a git tag:"
    echo "     git tag -a v$VERSION -m \"Release v$VERSION\""
    echo "  4. Push the tag:"
    echo "     git push origin v$VERSION"
    exit 0
fi

# Default: show preview
echo -e "${BLUE}Generating preview...${NC}"
echo ""
node scripts/generate-release-notes.js generate "preview"
echo ""
echo -e "${YELLOW}Tip: Use --help to see all available options${NC}"
