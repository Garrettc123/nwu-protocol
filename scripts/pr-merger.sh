#!/bin/bash
# PR Merger Script
# Helps manage and merge multiple pull requests automatically
# Usage: ./scripts/pr-merger.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="${GITHUB_REPO_OWNER:-Garrettc123}"
REPO_NAME="${GITHUB_REPO_NAME:-nwu-protocol}"
BASE_BRANCH="${BASE_BRANCH:-main}"
DRY_RUN="${DRY_RUN:-false}"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gh CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed. Please install it first."
        log_info "Visit: https://cli.github.com/"
        exit 1
    fi

    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        log_error "Not authenticated with GitHub CLI. Please run: gh auth login"
        exit 1
    fi

    log_success "GitHub CLI is installed and authenticated"
}

# List all open PRs
list_open_prs() {
    log_info "Fetching open pull requests..."

    echo ""
    echo "Open Pull Requests:"
    echo "==================="

    gh pr list --repo "$REPO_OWNER/$REPO_NAME" --state open --json number,title,author,mergeable,reviewDecision,statusCheckRollup,isDraft \
        --template '{{range .}}PR #{{.number}} - {{.title}}
  Author: {{.author.login}}
  Draft: {{.isDraft}}
  Mergeable: {{.mergeable}}
  Review Decision: {{.reviewDecision}}
  Status Checks: {{if .statusCheckRollup}}{{len .statusCheckRollup}}{{else}}0{{end}} checks
  ---
{{end}}'
}

# Check PR merge readiness
check_pr_readiness() {
    local pr_number=$1

    log_info "Checking PR #$pr_number readiness..."

    # Get PR details
    local pr_data=$(gh pr view "$pr_number" --repo "$REPO_OWNER/$REPO_NAME" --json number,title,mergeable,reviewDecision,statusCheckRollup,isDraft,mergeable)

    local is_draft=$(echo "$pr_data" | jq -r '.isDraft')
    local mergeable=$(echo "$pr_data" | jq -r '.mergeable')
    local review_decision=$(echo "$pr_data" | jq -r '.reviewDecision')
    local status_checks=$(echo "$pr_data" | jq -r '.statusCheckRollup // [] | length')

    local ready=true
    local reasons=()

    # Check if draft
    if [ "$is_draft" = "true" ]; then
        ready=false
        reasons+=("PR is in draft state")
    fi

    # Check mergeable status
    if [ "$mergeable" = "CONFLICTING" ]; then
        ready=false
        reasons+=("PR has merge conflicts")
    fi

    # Check review decision
    if [ "$review_decision" != "APPROVED" ] && [ "$review_decision" != "null" ] && [ "$review_decision" != "" ]; then
        if [ "$review_decision" = "REVIEW_REQUIRED" ]; then
            log_warning "PR requires review (not blocking auto-merge for now)"
        elif [ "$review_decision" = "CHANGES_REQUESTED" ]; then
            ready=false
            reasons+=("Changes requested in review")
        fi
    fi

    # Return results
    if [ "$ready" = true ]; then
        log_success "PR #$pr_number is ready to merge"
        return 0
    else
        log_warning "PR #$pr_number is NOT ready to merge:"
        for reason in "${reasons[@]}"; do
            echo "  - $reason"
        done
        return 1
    fi
}

# Merge a PR
merge_pr() {
    local pr_number=$1
    local merge_method="${2:-squash}" # squash, merge, or rebase

    log_info "Attempting to merge PR #$pr_number using $merge_method method..."

    if [ "$DRY_RUN" = "true" ]; then
        log_warning "DRY RUN: Would merge PR #$pr_number"
        return 0
    fi

    # Check readiness first
    if ! check_pr_readiness "$pr_number"; then
        log_error "Cannot merge PR #$pr_number - not ready"
        return 1
    fi

    # Attempt merge
    if gh pr merge "$pr_number" --repo "$REPO_OWNER/$REPO_NAME" --"$merge_method" --auto; then
        log_success "Successfully queued PR #$pr_number for merge"
        return 0
    else
        log_error "Failed to merge PR #$pr_number"
        return 1
    fi
}

# Batch merge multiple PRs
batch_merge_prs() {
    local pr_numbers=("$@")
    local merge_method="${MERGE_METHOD:-squash}"

    log_info "Starting batch merge of ${#pr_numbers[@]} PRs..."

    local success_count=0
    local fail_count=0

    for pr_number in "${pr_numbers[@]}"; do
        echo ""
        if merge_pr "$pr_number" "$merge_method"; then
            ((success_count++))
        else
            ((fail_count++))
        fi

        # Wait a bit between merges to avoid rate limiting
        sleep 2
    done

    echo ""
    echo "==============================="
    log_info "Batch merge complete!"
    log_success "Successfully merged: $success_count"
    if [ $fail_count -gt 0 ]; then
        log_error "Failed to merge: $fail_count"
    fi
    echo "==============================="
}

# Get ready PRs
get_ready_prs() {
    log_info "Finding PRs ready to merge..."

    local ready_prs=()

    # Get all open PRs
    local all_prs=$(gh pr list --repo "$REPO_OWNER/$REPO_NAME" --state open --json number --jq '.[].number')

    for pr in $all_prs; do
        if check_pr_readiness "$pr" &> /dev/null; then
            ready_prs+=("$pr")
        fi
    done

    if [ ${#ready_prs[@]} -eq 0 ]; then
        log_warning "No PRs are currently ready to merge"
        return 1
    fi

    echo ""
    log_success "Found ${#ready_prs[@]} PRs ready to merge:"
    for pr in "${ready_prs[@]}"; do
        echo "  - PR #$pr"
    done

    # Return the list
    echo "${ready_prs[@]}"
}

# Show usage
show_usage() {
    cat << EOF
PR Merger Script - Manage and merge multiple pull requests

Usage: ./scripts/pr-merger.sh [command] [options]

Commands:
  list                List all open pull requests
  check <PR#>        Check if a PR is ready to merge
  merge <PR#>        Merge a specific PR
  batch <PR#s...>    Merge multiple PRs (space-separated)
  auto               Automatically merge all ready PRs
  help               Show this help message

Options:
  --dry-run          Show what would be done without actually merging
  --method <type>    Merge method: squash (default), merge, or rebase
  --base <branch>    Base branch (default: main)

Environment Variables:
  GITHUB_REPO_OWNER  Repository owner (default: Garrettc123)
  GITHUB_REPO_NAME   Repository name (default: nwu-protocol)
  BASE_BRANCH        Base branch (default: main)
  DRY_RUN            Set to 'true' for dry run (default: false)
  MERGE_METHOD       Merge method (default: squash)

Examples:
  # List all open PRs
  ./scripts/pr-merger.sh list

  # Check if PR #88 is ready
  ./scripts/pr-merger.sh check 88

  # Merge PR #88
  ./scripts/pr-merger.sh merge 88

  # Merge multiple PRs
  ./scripts/pr-merger.sh batch 84 86 87 88

  # Auto-merge all ready PRs (dry run)
  DRY_RUN=true ./scripts/pr-merger.sh auto

  # Auto-merge all ready PRs
  ./scripts/pr-merger.sh auto

EOF
}

# Main command handler
main() {
    # Check prerequisites
    check_gh_cli

    # Parse command
    local command="${1:-help}"
    shift || true

    case "$command" in
        list)
            list_open_prs
            ;;
        check)
            if [ -z "$1" ]; then
                log_error "Please provide a PR number"
                exit 1
            fi
            check_pr_readiness "$1"
            ;;
        merge)
            if [ -z "$1" ]; then
                log_error "Please provide a PR number"
                exit 1
            fi
            merge_pr "$1" "${MERGE_METHOD:-squash}"
            ;;
        batch)
            if [ $# -eq 0 ]; then
                log_error "Please provide at least one PR number"
                exit 1
            fi
            batch_merge_prs "$@"
            ;;
        auto)
            local ready_prs=$(get_ready_prs)
            if [ -n "$ready_prs" ]; then
                echo ""
                if [ "$DRY_RUN" = "true" ]; then
                    log_warning "DRY RUN mode - no PRs will be merged"
                else
                    read -p "Do you want to merge these PRs? (y/N) " -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                        log_info "Merge cancelled by user"
                        exit 0
                    fi
                fi
                batch_merge_prs $ready_prs
            fi
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main
main "$@"
