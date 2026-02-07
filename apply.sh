#!/bin/bash

# NWU Protocol - Apply/Submit Contribution Tool

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8000}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗"
echo -e "║         NWU Protocol - Submit Your Contribution            ║"
echo -e "╚════════════════════════════════════════════════════════════════╝${NC}\n"

# Check if API is running
check_api() {
    if ! curl -s --max-time 2 "$API_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}❌ Error: NWU Protocol API is not running${NC}"
        echo -e "${YELLOW}💡 Please start the services first:${NC}"
        echo -e "   ./setup.sh   # First time setup"
        echo -e "   ./status.sh  # Check service status\n"
        exit 1
    fi
}

# Display contribution types
show_contribution_types() {
    echo -e "${GREEN}📋 Contribution Types:${NC}"
    echo -e "  1. ${YELLOW}Code${NC}        - Source code, libraries, algorithms"
    echo -e "  2. ${YELLOW}Dataset${NC}     - Training data, research datasets"
    echo -e "  3. ${YELLOW}Document${NC}    - Research papers, documentation"
    echo -e "  4. ${YELLOW}Model${NC}       - AI/ML models, pre-trained weights\n"
}

# Show supported file types
show_file_types() {
    echo -e "${GREEN}📄 Supported File Types:${NC}"
    echo -e "  Code:     .js, .py, .sol, .ts, .go, .rs, .java, .cpp"
    echo -e "  Dataset:  .csv, .json, .parquet, .h5, .pkl"
    echo -e "  Document: .pdf, .md, .tex, .docx"
    echo -e "  Model:    .h5, .pt, .pth, .onnx, .pb\n"
}

# Interactive mode
interactive_mode() {
    echo -e "${GREEN}🚀 Interactive Submission Mode${NC}\n"
    
    # Get contribution type
    show_contribution_types
    read -p "Select contribution type (1-4): " type_choice
    
    case $type_choice in
        1) contribution_type="code" ;;
        2) contribution_type="dataset" ;;
        3) contribution_type="document" ;;
        4) contribution_type="model" ;;
        *) 
            echo -e "${RED}Invalid choice. Using 'code' as default.${NC}"
            contribution_type="code"
            ;;
    esac
    
    # Get file path
    echo ""
    read -p "Enter file or directory path: " file_path
    
    if [ ! -e "$file_path" ]; then
        echo -e "${RED}❌ Error: File or directory not found: $file_path${NC}"
        exit 1
    fi
    
    # Get title
    read -p "Enter contribution title: " title
    
    # Get description
    echo "Enter description (press Ctrl+D when done):"
    description=$(cat)
    
    # Confirm submission
    echo -e "\n${YELLOW}📝 Submission Summary:${NC}"
    echo -e "  Type:        $contribution_type"
    echo -e "  File:        $file_path"
    echo -e "  Title:       $title"
    echo -e "  Description: ${description:0:50}...\n"
    
    read -p "Submit this contribution? (y/n): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "${YELLOW}Submission cancelled.${NC}"
        exit 0
    fi
    
    submit_contribution "$contribution_type" "$file_path" "$title" "$description"
}

# Submit contribution
submit_contribution() {
    local type=$1
    local file=$2
    local title=$3
    local description=$4
    
    echo -e "\n${BLUE}📤 Submitting contribution...${NC}"
    
    # Create form data
    response=$(curl -s -X POST "$API_URL/api/v1/contributions" \
        -F "file=@$file" \
        -F "type=$type" \
        -F "title=$title" \
        -F "description=$description")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contribution submitted successfully!${NC}\n"
        echo -e "${YELLOW}Response:${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        echo ""
        echo -e "${BLUE}💡 Next Steps:${NC}"
        echo -e "  1. Your contribution is being verified by AI agents"
        echo -e "  2. Check status at: ${API_URL}/api/v1/contributions/<id>"
        echo -e "  3. View dashboard at: http://localhost:3000/dashboard"
        echo -e "  4. Verification typically takes 2-5 minutes\n"
    else
        echo -e "${RED}❌ Error: Failed to submit contribution${NC}"
        echo -e "${YELLOW}Response:${NC}"
        echo "$response"
        exit 1
    fi
}

# Command-line mode
command_mode() {
    local type=$1
    local file=$2
    local title=$3
    local description=$4
    
    if [ -z "$type" ] || [ -z "$file" ]; then
        echo -e "${RED}❌ Error: Missing required arguments${NC}"
        echo -e "${YELLOW}Usage:${NC}"
        echo -e "  $0 <type> <file> <title> [description]\n"
        show_contribution_types
        exit 1
    fi
    
    if [ ! -e "$file" ]; then
        echo -e "${RED}❌ Error: File not found: $file${NC}"
        exit 1
    fi
    
    title=${title:-"Untitled Contribution"}
    description=${description:-"No description provided"}
    
    submit_contribution "$type" "$file" "$title" "$description"
}

# Show help
show_help() {
    cat << EOF
${GREEN}NWU Protocol - Apply/Submit Contribution Tool${NC}

${YELLOW}USAGE:${NC}
  $0                                    # Interactive mode
  $0 <type> <file> <title> [desc]      # Command-line mode
  $0 --help                             # Show this help

${YELLOW}EXAMPLES:${NC}
  # Interactive mode
  $0

  # Submit code
  $0 code ./my-algorithm.py "ML Algorithm" "Description here"
  
  # Submit dataset
  $0 dataset ./data.csv "Training Data"
  
  # Submit document
  $0 document ./research.pdf "Research Paper"

${YELLOW}CONTRIBUTION TYPES:${NC}
  code      - Source code, libraries, algorithms
  dataset   - Training data, research datasets
  document  - Research papers, documentation
  model     - AI/ML models, pre-trained weights

${YELLOW}ENVIRONMENT VARIABLES:${NC}
  API_URL   - Override API endpoint (default: http://localhost:8000)

${YELLOW}MORE INFO:${NC}
  Documentation: README.md
  Dashboard:     http://localhost:3000
  API Docs:      http://localhost:8000/docs

EOF
}

# Main execution
main() {
    # Check for help flag
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    # Check API availability
    check_api
    
    # Determine mode
    if [ $# -eq 0 ]; then
        # Interactive mode
        interactive_mode
    else
        # Command-line mode
        command_mode "$1" "$2" "$3" "$4"
    fi
}

main "$@"
