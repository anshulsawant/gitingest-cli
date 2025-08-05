#!/usr/bin/env python3

import os
import re
import argparse
import sys

def sanitize_title(title):
    """
    A robust function to sanitize titles for Logseq filenames and links.
    """
    clean_title = title.strip(" '`\"")
    clean_title = clean_title.replace(':', ' -')
    clean_title = clean_title.replace('/', ' or ')
    clean_title = re.sub(r'[<>\"\\|?*]', '', clean_title)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    return clean_title

def clean_content_block(raw_content):
    """
    Isolates the true Zettel content by removing markdown fences and stopping at separators.
    """
    content_before_separator = raw_content.split('---')[0]
    lines = content_before_separator.split('\n')
    clean_lines = [line for line in lines if not line.strip().startswith('```')]
    return "\n".join(clean_lines).strip()


def parse_and_create_zettels(input_content, output_dir):
    """
    Parses Zettel text, correctly isolating each block before processing,
    and creates perfectly formatted and linked Markdown files for Logseq.
    """
    print(f"Checking and creating output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    # --- PASS 1: Isolate Zettel blocks and build the title map ---
    raw_zettel_blocks = input_content.split('**Title:**')[1:]
    if not raw_zettel_blocks:
        print("Error: No Zettels found. Input must contain '**Title:**' delimiters.")
        sys.exit(1)
        
    print(f"Found {len(raw_zettel_blocks)} Zettels. Cleaning and building title map...")
    
    zettels_data = []
    title_map = {}
    for block in raw_zettel_blocks:
        try:
            title_part, content_part = block.split('**Content:**', 1)
            original_title = title_part.strip()
            
            if not original_title:
                continue

            true_content = clean_content_block(content_part)
            sanitized_title = sanitize_title(original_title)
            title_map[original_title] = sanitized_title
            
            zettels_data.append({
                'original_title': original_title,
                'sanitized_title': sanitized_title, 
                'content': true_content
            })
        except ValueError:
            print(f"Warning: Skipping malformed block. Could not find '**Content:**'.")

    # --- PASS 2: Update wikilinks in all content blocks ---
    print("Synchronizing wikilinks with sanitized titles...")
    
    processed_zettels = []
    for zettel in zettels_data:
        updated_content = zettel['content']
        for original, sanitized in title_map.items():
            updated_content = updated_content.replace(f"[[{original}]]", f"[[{sanitized}]]")
        
        processed_zettels.append({
            'sanitized_title': zettel['sanitized_title'], 
            'content': updated_content
        })

    # --- PASS 3: Write the files with escaping and correct outliner formatting ---
    print("Writing final, correctly formatted Zettel files with tag escaping...")
    for zettel in processed_zettels:
        filename = f"{zettel['sanitized_title']}.md"
        filepath = os.path.join(output_dir, filename)

        escaped_lines = []
        for line in zettel['content'].split('\n'):
            # If the line is the tags property line, leave it alone.
            if line.strip().startswith('tags::'):
                escaped_lines.append(line)
            else:
                # For all other lines, escape the '#' to prevent accidental tags.
                # This regex finds a # followed by one or more non-space characters
                # and prepends a backslash to the #.
                escaped_line = re.sub(r'(#(\S+))', r'\\#\2', line)
                escaped_lines.append(escaped_line)

        final_content_str = "\n".join(escaped_lines)
        indented_content = "\n".join(["  " + ln for ln in final_content_str.split('\n')])
        final_logseq_content = "- \n" + indented_content
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_logseq_content)
        
        print(f"  (+) Created: {filename}")

    print("\nProcess complete. All issues should now be resolved.")

def main():
    parser = argparse.ArgumentParser(
        description="A robust script to parse Zettelkasten text and create linked Markdown files for Logseq.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('input_file', type=str, help="The path to the input text file containing the Zettels.")
    parser.add_argument('output_dir', type=str, help="The path to your Logseq graph's 'pages' directory.")
    args = parser.parse_args()
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_content = f.read()
        parse_and_create_zettels(input_content, args.output_dir)
    except FileNotFoundError:
        print(f"Error: The input file was not found at '{args.input_file}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
