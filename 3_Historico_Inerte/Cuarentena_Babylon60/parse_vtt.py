# C5-REAL EXERGY CERTIFIED
import re

def parse_vtt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove WebVTT header and styling
    content = re.sub(r'WEBVTT.*?\n\n', '', content, flags=re.DOTALL)

    # Remove timestamp lines
    content = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}.*\n', '', content)

    # Remove HTML/formatting tags
    content = re.sub(r'<[^>]+>', '', content)

    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line: continue
        # VTT from YouTube often duplicates words as they are spoken.
        # A simple deduplication of consecutive identical lines:
        if cleaned_lines and cleaned_lines[-1] == line:
            continue
        # Check if line is a substring of the previous line (rolling captions)
        if cleaned_lines and line in cleaned_lines[-1]:
            continue
        cleaned_lines.append(line)

    text = ' '.join(cleaned_lines)

    # Simple trick to remove word-by-word duplication:
    words = text.split()
    final_words = []
    for w in words:
        if final_words and final_words[-1] == w:
            continue
        final_words.append(w)

    print(' '.join(final_words)[:5000]) # First 5000 chars for a quick look
    print("\n\n--- MIDDLE ---\n\n")
    mid = len(final_words) // 2
    print(' '.join(final_words[mid:mid+800]))
    print("\n\n--- END ---\n\n")
    print(' '.join(final_words[-800:]))

parse_vtt('transcript_inpkgfG5uv4.es.vtt')
