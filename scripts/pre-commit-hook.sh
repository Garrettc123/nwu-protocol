#!/bin/bash

################################################################################
# NWU Protocol - Enhanced Pre-Commit Hook
# Auto-repair and quality checks
# Install with: cp scripts/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🤖 Running pre-commit auto-repairs and checks...${NC}"
echo ""

FAILED=0

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    echo -e "${YELLOW}No files staged for commit${NC}"
    exit 0
fi

# Fix formatting for staged JS/TS/JSON/CSS/MD files
echo -e "${BLUE}[1/7]${NC} Formatting code..."
JS_FILES=$(echo "$STAGED_FILES" | grep -E '\.(js|jsx|ts|tsx|json|css|md)$' || true)
if [ -n "$JS_FILES" ]; then
    if command -v npx > /dev/null 2>&1; then
        echo "$JS_FILES" | xargs npx prettier --write 2>/dev/null || true
        echo "$JS_FILES" | xargs git add
        echo -e "${GREEN}✓${NC} Formatted JavaScript/TypeScript files"
    else
        echo -e "${YELLOW}⚠${NC} Node.js not available, skipping JS formatting"
    fi
else
    echo -e "${GREEN}✓${NC} No JS/TS files to format"
fi

# Fix Python formatting
echo -e "${BLUE}[2/7]${NC} Formatting Python code..."
PY_FILES=$(echo "$STAGED_FILES" | grep -E '\.py$' || true)
if [ -n "$PY_FILES" ]; then
    if command -v black > /dev/null 2>&1; then
        echo "$PY_FILES" | xargs black --line-length 100 2>/dev/null || true
        echo "$PY_FILES" | xargs git add
        echo -e "${GREEN}✓${NC} Formatted Python files"
    else
        echo -e "${YELLOW}⚠${NC} black not installed, skipping Python formatting"
    fi
else
    echo -e "${GREEN}✓${NC} No Python files to format"
fi

# Check for hardcoded secrets
echo -e "${BLUE}[3/7]${NC} Checking for secrets..."
SECRET_PATTERNS="AKIA|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|glpat-[a-zA-Z0-9]{20}"
if echo "$STAGED_FILES" | xargs git diff --cached | grep -iE "$SECRET_PATTERNS" > /dev/null 2>&1; then
    echo -e "${RED}✗ Hardcoded secrets detected!${NC}"
    echo -e "${YELLOW}Please remove sensitive data before committing${NC}"
    FAILED=1
else
    echo -e "${GREEN}✓${NC} No secrets detected"
fi

# Check for placeholder values in code files
echo -e "${BLUE}[4/7]${NC} Checking for placeholders..."
FOUND_PLACEHOLDER=false
for file in $STAGED_FILES; do
    if [[ -f "$file" && ! "$file" =~ \.(md|txt|example)$ ]]; then
        if git diff --cached "$file" | grep -E "REPLACE[-_]WITH|sk-REPLACE" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠${NC} Placeholder found in $file"
            FOUND_PLACEHOLDER=true
        fi
    fi
done
if [ "$FOUND_PLACEHOLDER" = false ]; then
    echo -e "${GREEN}✓${NC} No placeholders in code files"
fi

# Check for debug statements
echo -e "${BLUE}[5/7]${NC} Checking for debug statements..."
DEBUG_PATTERNS="console\.log|debugger|pdb\.set_trace|import pdb"
FOUND_DEBUG=false
for file in $STAGED_FILES; do
    if [[ -f "$file" && "$file" =~ \.(js|jsx|ts|tsx|py)$ ]]; then
        if git diff --cached "$file" | grep -E "^\+.*($DEBUG_PATTERNS)" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠${NC} Debug statement found in $file"
            FOUND_DEBUG=true
        fi
    fi
done
if [ "$FOUND_DEBUG" = false ]; then
    echo -e "${GREEN}✓${NC} No debug statements"
fi

# Check file sizes
echo -e "${BLUE}[6/7]${NC} Checking file sizes..."
MAX_SIZE=$((10 * 1024 * 1024))  # 10MB
FOUND_LARGE=false
for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        SIZE=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        if [ "$SIZE" -gt "$MAX_SIZE" ]; then
            echo -e "${YELLOW}⚠${NC} Large file: $file ($(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "$SIZE bytes"))"
            FOUND_LARGE=true
        fi
    fi
done
if [ "$FOUND_LARGE" = false ]; then
    echo -e "${GREEN}✓${NC} No large files"
fi

# Verify commit message format (if available)
echo -e "${BLUE}[7/7]${NC} Commit message format..."
if [ -f ".git/COMMIT_EDITMSG" ]; then
    COMMIT_MSG=$(cat ".git/COMMIT_EDITMSG")
    if echo "$COMMIT_MSG" | grep -Eq '^(feat|fix|docs|style|refactor|test|chore|security|perf|ci|copilot)(\(.+\))?: .+'; then
        echo -e "${GREEN}✓${NC} Commit message format is valid"
    else
        echo -e "${YELLOW}⚠${NC} Commit message should follow format: type(scope): description"
    fi
else
    echo -e "${YELLOW}⚠${NC} Commit message not yet available"
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Pre-commit checks complete${NC}"
    exit 0
else
    echo -e "${RED}❌ Pre-commit checks failed${NC}"
    echo -e "${YELLOW}Fix issues or use 'git commit --no-verify' to bypass${NC}"
    exit 1
fi
