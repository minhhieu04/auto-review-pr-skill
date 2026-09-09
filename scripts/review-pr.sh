#!/bin/bash
# =============================================================================
# Auto-Review PR — Quick CLI Wrapper
# Usage:
#   ./review-pr.sh <pr_number> <repo_type>
#   ./review-pr.sh 916 be          # Review backend PR #916
#   ./review-pr.sh 1460 fe         # Review frontend PR #1460
#   ./review-pr.sh 100 be fe       # Review PR #100 on both repos
# =============================================================================

set -euo pipefail

ORG="deveop-com"
BE_REPO="clickessms_be"
FE_REPO="clickessms_fe"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo -e "${BLUE}Usage:${NC} $0 <pr_number> <repo_type...>"
    echo ""
    echo "  repo_type: be | fe | both"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 916 be        # Review BE PR #916"
    echo "  $0 1460 fe       # Review FE PR #1460"
    echo "  $0 100 be fe     # Review PR #100 on both repos"
    exit 1
}

get_pr_info() {
    local repo=$1
    local pr_number=$2
    echo -e "${BLUE}📋 Fetching PR #${pr_number} from ${repo}...${NC}" >&2
    gh pr view "$pr_number" --repo "${ORG}/${repo}" \
        --json number,title,body,author,headRefName,baseRefName,additions,deletions,changedFiles,commits
}

get_pr_diff() {
    local repo=$1
    local pr_number=$2
    echo -e "${BLUE}📝 Fetching diff for PR #${pr_number}...${NC}" >&2
    gh pr diff "$pr_number" --repo "${ORG}/${repo}"
}

get_existing_reviews() {
    local repo=$1
    local pr_number=$2
    echo -e "${BLUE}🔍 Checking existing reviews...${NC}" >&2
    gh api "repos/${ORG}/${repo}/pulls/${pr_number}/reviews" --jq '.[].body' 2>/dev/null || true
}

classify_files() {
    local diff="$1"
    local has_python=false
    local has_react=false
    local has_css=false
    local has_test=false
    local has_docker=false
    local has_ci=false

    while IFS= read -r line; do
        case "$line" in
            *.py)       has_python=true ;;
            *.jsx|*.tsx) has_react=true ;;
            *.ts)       has_react=true ;;
            *.css|*.scss) has_css=true ;;
            *.test.*|*.spec.*) has_test=true ;;
            Dockerfile*|docker-compose*) has_docker=true ;;
            *.yml|*.yaml) has_ci=true ;;
        esac
    done <<< "$(echo "$diff" | grep '^diff --git' | sed 's/diff --git a\///' | sed 's/ b\/.*//')"

    echo "python=$has_python react=$has_react css=$has_css test=$has_test docker=$has_docker ci=$has_ci"
}

# =============================================================================
# Main
# =============================================================================

if [ $# -lt 2 ]; then
    usage
fi

PR_NUMBER=$1
shift
REPOS=()

for arg in "$@"; do
    case "$arg" in
        be|BE)   REPOS+=("$BE_REPO") ;;
        fe|FE)   REPOS+=("$FE_REPO") ;;
        both)    REPOS+=("$BE_REPO" "$FE_REPO") ;;
        *)       echo -e "${RED}❌ Unknown repo type: $arg${NC}"; usage ;;
    esac
done

echo -e "${GREEN}🤖 Auto-Review PR Pipeline Starting${NC}"
echo -e "   PR: #${PR_NUMBER}"
echo -e "   Repos: ${REPOS[*]}"
echo ""

for REPO in "${REPOS[@]}"; do
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Reviewing: ${REPO} PR #${PR_NUMBER}${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════${NC}"

    # Step 1: Get PR info
    PR_INFO=$(get_pr_info "$REPO" "$PR_NUMBER")
    PR_TITLE=$(echo "$PR_INFO" | jq -r '.title')
    PR_AUTHOR=$(echo "$PR_INFO" | jq -r '.author.login')
    PR_ADDITIONS=$(echo "$PR_INFO" | jq -r '.additions')
    PR_DELETIONS=$(echo "$PR_INFO" | jq -r '.deletions')
    PR_FILES=$(echo "$PR_INFO" | jq -r '.changedFiles')

    echo -e "   Title: ${YELLOW}${PR_TITLE}${NC}"
    echo -e "   Author: ${PR_AUTHOR}"
    echo -e "   Changes: +${GREEN}${PR_ADDITIONS}${NC} / -${RED}${PR_DELETIONS}${NC} (${PR_FILES} files)"

    # Step 2: Get diff
    DIFF=$(get_pr_diff "$REPO" "$PR_NUMBER")

    # Step 3: Classify files
    FILE_CLASSES=$(classify_files "$DIFF")
    echo -e "   ${BLUE}File classification: ${FILE_CLASSES}${NC}"

    # Step 4: Check existing reviews
    EXISTING=$(get_existing_reviews "$REPO" "$PR_NUMBER")
    if echo "$EXISTING" | grep -q "Auto-Review Report"; then
        echo -e "   ${YELLOW}⚠️  Previous auto-review found. Will post updated review.${NC}"
    fi

    # Step 5: Save diff for agent consumption
    DIFF_FILE="/tmp/pr_${PR_NUMBER}_${REPO}.diff"
    echo "$DIFF" > "$DIFF_FILE"
    echo -e "   ${GREEN}✅ Diff saved to ${DIFF_FILE}${NC}"

    echo ""
    echo -e "${BLUE}📤 Ready for Antigravity agent review.${NC}"
    echo -e "${BLUE}   Run in Antigravity:${NC}"
    echo -e "   ${YELLOW}review PR #${PR_NUMBER} on ${REPO}${NC}"
    echo ""
done

echo -e "${GREEN}🎉 Pipeline prep complete!${NC}"
