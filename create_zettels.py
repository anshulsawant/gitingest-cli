#!/usr/bin/env python3
import os
import re
import argparse
import sys

def sanitize_filename(title):
    """
    Sanitizes a string to be used as a valid filename.
    Replaces invalid characters with an underscore.
    Logseq uses the title as the filename, so we must be careful.
    """
    # Replace slashes with a safe character, as they imply directories
    title = title.replace('/', '_or_')
    # Remove other characters that are invalid in most filesystems
    sanitized_title = re.sub(r'[<>:"\\|?*]', '', title)
    return f"{sanitized_title}.md"

def parse_and_create_zettels(input_content, output_dir):
    """
    Parses the Zettel text and creates Markdown files in the output directory.
    """
    print(f"Checking and creating output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Split the entire content by the '**Title:**' delimiter.
    # The [1:] slice discards any text before the first title.
    zettel_blocks = input_content.split('**Title:**')[1:]
    
    if not zettel_blocks:
        print("Error: No Zettels found in the input file. Make sure it starts with '**Title:**'.")
        sys.exit(1)
        
    print(f"Found {len(zettel_blocks)} Zettels to process...")

    for i, block in enumerate(zettel_blocks):
        try:
            # Each block is split into a title part and a content part
            # by the '**Content:**' delimiter.
            title_part, content_part = block.split('**Content:**', 1)
            
            title = title_part.strip()
            content = content_part.strip()
            
            if not title:
                print(f"Warning: Skipping Zettel #{i+1} due to missing title.")
                continue

            filename = sanitize_filename(title)
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  (+) Created: {filename}")

        except ValueError:
            print(f"Warning: Skipping malformed Zettel block #{i+1}. Could not find '**Content:**'.")
        except Exception as e:
            print(f"An error occurred while processing Zettel block #{i+1}: {e}")

    print("\nProcess complete.")


def main():
    parser = argparse.ArgumentParser(
        description="A script to parse a Zettelkasten text file and create individual Markdown files for Logseq.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'input_file', 
        type=str,
        help="The path to the input text file containing the Zettels."
    )
    parser.add_argument(
        'output_dir', 
        type=str,
        help="The path to your Logseq graph's 'pages' directory where the .md files will be saved."
    )
    
    args = parser.parse_args()

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_content = f.read()
        parse_and_create_zettels(input_content, args.output_dir)
    except FileNotFoundError:
        print(f"Error: The input file was not found at '{args.input_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"A critical error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
