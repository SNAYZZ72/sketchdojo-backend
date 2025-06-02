#!/bin/bash
# Auto-fix linting issues in SketchDojo backend

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function for status messages
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

# Helper function for warnings
print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Function to fix line length issues
fix_line_length() {
    print_status "Fixing line length issues..."
    # Use black to auto-format code and fix line lengths
    python -m black --line-length=79 app/ tests/
}

# Function to fix unused variables
fix_unused_variables() {
    print_status "Fixing unused variables..."
    # Find all Python files with unused variables and add _ prefix
    find app/ tests/ -name "*.py" -type f -exec grep -l "local variable '.*' is assigned to but never used" {} \; | while read -r file; do
        # Get the variable names that are unused
        var_names=$(grep -o "local variable '\w\+' is assigned to but never used" "$file" | awk -F"'" '{print $2}' | sort -u)

        for var in $var_names; do
            # Skip if already has _ prefix
            if [[ "$var" == _* ]]; then
                continue
            fi
            # Add _ prefix to unused variables
            sed -i "s/\b$var\b/_${var}/g" "$file"
            print_status "Fixed unused variable: $var -> _${var} in $file"
        done
    done
}

# Function to fix bare except statements
fix_bare_except() {
    print_status "Fixing bare except statements..."
    # Find all bare except statements and replace with specific exception
    find app/ tests/ -name "*.py" -type f -exec grep -l "except:" {} \; | while read -r file; do
        # Replace bare except with specific exception
        sed -i 's/except:/except Exception:/g' "$file"
        print_status "Fixed bare except in $file"
    done
}

# Function to fix whitespace before colon
fix_whitespace_before_colon() {
    print_status "Fixing whitespace before colon..."
    # Remove whitespace before colons
    find app/ tests/ -name "*.py" -type f -exec sed -i 's/\s\+:/:/g' {} \;
}

# Function to fix import ordering
fix_import_ordering() {
    print_status "Fixing import ordering..."
    # Use isort to fix import ordering
    python -m isort app/ tests/
}

# Main function
main() {
    print_status "Starting auto-fix process..."

    # Install required tools if not present
    if ! command -v black &> /dev/null; then
        print_status "Installing black..."
        pip install black
    fi

    if ! command -v isort &> /dev/null; then
        print_status "Installing isort..."
        pip install isort
    fi

    # Run fixes
    fix_line_length
    fix_unused_variables
    fix_bare_except
    fix_whitespace_before_colon
    fix_import_ordering

    print_status "Auto-fix process completed!"
}

# Run the main function
main "$@"

# Check if required tools are installed
command -v isort >/dev/null 2>&1 || { echo -e "${RED}ERROR:${NC} isort is required but not installed. Install with: pip install isort"; exit 1; }
command -v black >/dev/null 2>&1 || { echo -e "${RED}ERROR:${NC} black is required but not installed. Install with: pip install black"; exit 1; }
command -v autoflake >/dev/null 2>&1 || { echo -e "${RED}ERROR:${NC} autoflake is required but not installed. Install with: pip install autoflake"; exit 1; }

# Ensure virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_status "Activating virtual environment..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}ERROR:${NC} Virtual environment not found. Please create and activate it first."
        exit 1
    fi
fi

# Step 1: Remove unused imports with autoflake
print_status "Removing unused imports..."
autoflake --in-place --remove-all-unused-imports --recursive app/ tests/

# Step 2: Fix import order with isort
print_status "Fixing import order..."
isort app/ tests/

# Step 3: Format code with black
print_status "Formatting code with black..."
black app/ tests/

# Step 4: Fix remaining issues that require manual attention
print_warning "Some issues may require manual fixes:"
print_warning "1. Variables assigned but never used (F841) - Consider removing or using them"
print_warning "2. Bare except statements (E722) - Replace with specific exceptions"
print_warning "3. Long lines that black couldn't fix - Consider refactoring"

# Run linting again to see remaining issues
print_status "Running linting to check remaining issues..."
./scripts/lint.sh

print_status "Auto-fix completed! Review remaining issues manually."
