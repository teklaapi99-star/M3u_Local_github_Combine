#!/usr/bin/env python3
"""
Fixed M3U Merger:
- Local channels are now properly included
- All remote Tamil channels get group-title="TV"
- Better handling of headers and empty lines
"""

import sys
import requests
from pathlib import Path

LOCAL_M3U = "Local_channels.m3u"          # ← Make sure this file exists in your repo root
REMOTE_URL = "https://iptv-org.github.io/iptv/languages/tam.m3u"
OUTPUT_M3U = "combined-tam.m3u"
REMOTE_GROUP = "TV"

def clean_lines(content: str):
    """Split content into lines and remove empty ones + duplicate #EXTM3U"""
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    # Remove any #EXTM3U header (we'll add our own)
    if lines and lines[0].upper().startswith("#EXTM3U"):
        lines = lines[1:]
    return lines

def add_or_update_group_title(extinf_line: str, group: str) -> str:
    """Add or update group-title in #EXTINF line"""
    if not extinf_line.startswith("#EXTINF:"):
        return extinf_line

    import re
    # If group-title already exists, replace it
    if 'group-title=' in extinf_line:
        extinf_line = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', extinf_line)
    else:
        # Add group-title before the comma (channel name)
        if "," in extinf_line:
            attr_part, name = extinf_line.split(",", 1)
            attr_part = attr_part.rstrip() + f', group-title="{group}"'
            extinf_line = f"{attr_part},{name.strip()}"
        else:
            extinf_line += f', group-title="{group}"'

    return extinf_line

def main():
    print("🔄 Starting M3U merge (Fixed version)...")

    # === Load Local File ===
    local_path = Path(LOCAL_M3U)
    local_lines = []
    if local_path.exists() and local_path.stat().st_size > 0:
        local_content = local_path.read_text(encoding="utf-8")
        local_lines = clean_lines(local_content)
        local_channel_count = sum(1 for line in local_lines if line.startswith("#EXTINF:"))
        print(f"✅ Loaded local playlist: {local_channel_count} channels")
    else:
        print(f"⚠️  Local file '{LOCAL_M3U}' not found or empty. Only remote channels will be used.")

    # === Download Remote File ===
    print(f"📥 Downloading remote Tamil playlist from iptv-org...")
    try:
        response = requests.get(REMOTE_URL, timeout=30)
        response.raise_for_status()
        remote_lines = clean_lines(response.text)
        print(f"✅ Downloaded remote playlist: {len(remote_lines)} lines")
    except Exception as e:
        print(f"❌ Failed to download remote playlist: {e}")
        sys.exit(1)

    # === Build Combined Playlist ===
    combined = ["#EXTM3U"]

    # Add local channels (unchanged)
    combined.extend(local_lines)

    # Add remote channels with group-title="TV"
    remote_channel_count = 0
    i = 0
    while i < len(remote_lines):
        line = remote_lines[i]
        if line.startswith("#EXTINF:"):
            modified_line = add_or_update_group_title(line, REMOTE_GROUP)
            combined.append(modified_line)
            remote_channel_count += 1

            # Add the URL line that follows
            i += 1
            if i < len(remote_lines):
                combined.append(remote_lines[i])
        else:
            combined.append(line)
        i += 1

    # Simple deduplication (remove exact duplicate lines)
    seen = set()
    unique_lines = []
    for line in combined[1:]:   # skip the first #EXTM3U we added
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    # Write output
    final_content = "#EXTM3U\n" + "\n".join(unique_lines) + "\n"
    Path(OUTPUT_M3U).write_text(final_content, encoding="utf-8")

    final_channel_count = sum(1 for line in unique_lines if line.startswith("#EXTINF:"))

    print(f"🎉 Merge completed successfully!")
    print(f"   Local channels   : {sum(1 for l in local_lines if l.startswith('#EXTINF:'))}")
    print(f"   Remote channels  : {remote_channel_count} (group-title=\"{REMOTE_GROUP}\")")
    print(f"   Final channels   : {final_channel_count}")
    print(f"   Output saved as  : {OUTPUT_M3U}")

if __name__ == "__main__":
    main()