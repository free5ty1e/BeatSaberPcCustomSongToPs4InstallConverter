#!/usr/bin/env python3
import re
import os

def extract_latest(changelog_path):
    with open(changelog_path, 'r') as f:
        content = f.read()
    
    # Matches ## [vX.XX] - ... until the next ## or end of file
    match = re.search(r'(## \[v.*?\] — .*?\n(.*?)(?=\n## \[v|$))', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def update_release_body():
    plugin_log = extract_latest('beat_saber_deluxe/CHANGELOG-PLUGIN.md')
    pipeline_log = extract_latest('beat_saber_deluxe/CHANGELOG-PIPELINE.md')
    
    body = "# Release Notes\n\n"
    if plugin_log:
        body += "## Plugin Changes\n\n" + plugin_log + "\n\n"
    if pipeline_log:
        body += "## Pipeline Changes\n\n" + pipeline_log + "\n"
        
    with open('beat_saber_deluxe/CI_RELEASE.md', 'w') as f:
        f.write(body)

if __name__ == "__main__":
    update_release_body()
