#!/bin/bash
# Usage: ./prepare_prompt.sh <include_extensions> [exclude_patterns]
# Example: ./prepare_prompt.sh "*.py *.js" "*.log *.env config/*"
# Outputs to stdout for piping or direct use in LLM prompts

# Handle --help option or missing mandatory inclusion
if [ "$1" = "--help" ] || [ -z "$1" ]; then
  echo "Usage: $(basename "$0") <include_extensions> [exclude_patterns]"
  echo "Inclusion patterns are mandatory."
  echo "Example: $(basename "$0") \"*.py *.js\" \"*.log *.env config/*\""
  echo "Outputs the project structure and code to stdout, formatted for LLM prompts."
  exit 0
fi

# Values (inclusion is mandatory via check above)
INCLUDE_EXTENSIONS="$1"

# Default exclusions (always included)
DEFAULT_EXCLUDES=".git node_modules venv __pycache__ .env"

# User-specified exclusions are added to defaults
EXCLUDE_PATTERNS="$DEFAULT_EXCLUDES $2"

# Function to map file extensions to markdown language identifiers
get_language() {
  case "$1" in
    *.py) echo "python" ;;
    *.js) echo "javascript" ;;
    *.ts) echo "typescript" ;;
    *.sh) echo "bash" ;;
    *.java) echo "java" ;;
    *.c) echo "c" ;;
    *.cpp) echo "cpp" ;;
    *.html) echo "html" ;;
    *.css) echo "css" ;;
    *.json) echo "json" ;;
    *.yml|*.yaml) echo "yaml" ;;
    *.md) echo "markdown" ;;
    *) echo "text" ;; # Default for unknown extensions
  esac
}

# Export the function for use in the subshell created by find -exec
export -f get_language

# --- SCRIPT SETUP ---
# Generate directory structure, respecting inclusion and exclusion patterns
echo "Below is the code from my project. Please analyze it and provide suggestions for improvement. Project structure:"
# Convert space-separated patterns to arrays for tree and find
read -ra include_array <<< "$INCLUDE_EXTENSIONS"
read -ra exclude_array <<< "$EXCLUDE_PATTERNS"
# Join array elements with a | for tree's patterns
include_pattern=$(printf "|%s" "${include_array[@]}")
exclude_pattern=$(printf "|%s" "${exclude_array[@]}")
tree -a -P "${include_pattern#|}" -I "${exclude_pattern#|}" --noreport

echo -e "\nCode files:\n"

# --- FIND AND CONCATENATE FILES (ROBUST METHOD) ---

# Define the script to run on each found file.
# Using "$1" is safer as find will pass the filename as an argument.
# This avoids issues with filenames containing spaces or special characters.
CODE_PRINTER_SCRIPT='
  filepath="$1"
  echo "=== ${filepath} ==="
  lang=$(get_language "${filepath}")
  echo "\`\`\`${lang}"
  cat "${filepath}"
  # Ensure the file ends with a newline before the closing fence
  if [[ $(tail -c1 "${filepath}" | wc -l) -eq 0 ]]; then
    echo
  fi
  echo "\`\`\`"
  echo
'

# Build the find command arguments in an array to avoid eval and quoting issues
find_args=()
find_args+=(".")

# Add exclusion patterns
for pattern in $EXCLUDE_PATTERNS; do
  # Exclude both files and directories matching the pattern
  find_args+=(-not -path "*/${pattern}/*" -and -not -name "${pattern}")
done

# Add inclusion patterns
# We need to group these with \( ... \) for the -o (OR) logic to work correctly
find_args+=(\()
first_include=true
for pattern in $INCLUDE_EXTENSIONS; do
  if ! $first_include; then
    find_args+=(-o)
  fi
  find_args+=(-name "$pattern")
  first_include=false
done
find_args+=(\))

# Add the action to execute the script on each file
find_args+=(-type f -exec bash -c "$CODE_PRINTER_SCRIPT" _ {} \;)

# Execute the find command with the constructed arguments
find "${find_args[@]}"
