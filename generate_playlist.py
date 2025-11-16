import os
import requests
import re
from datetime import datetime

OUTFILE = "playlist.m3u"

# --- Fixed Promo Channel ---
PROMO_CHANNEL = {
    "name": "HOME CHANNEL",
    "tvg-logo": "https://i.postimg.cc/Kvzz5Pt4/joinus.png",
    "group-title": "JOIN TELEGRAM",
    "url": "https://raw.githubusercontent.com/unosottor/unosottor.github.io/refs/heads/main/notice/index.m3u8"
}


# --- Helper Functions ---
def is_url(s):
    return isinstance(s, str) and s.startswith(("http://", "https://"))


def read_m3u(source):
    """Read .m3u content from URL or file"""
    if not source:
        return []

    try:
        if is_url(source):
            resp = requests.get(source, timeout=12)
            resp.raise_for_status()
            content = resp.text
            print(f"Loaded playlist: {source}")
        else:
            with open(source, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                print(f"Loaded local file: {source}")
    except Exception as e:
        print(f" Skipped broken playlist: {source} ({e})")
        return []

    lines = content.strip().splitlines()
    channels = []
    current_info = {}

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            logo = re.search(r'tvg-logo="([^"]+)"', line)
            group = re.search(r'group-title="([^"]+)"', line)
            name = line.split(",")[-1].strip() if "," in line else "Unknown"
            current_info = {
                "name": name,
                "tvg-logo": logo.group(1) if logo else "",
                "group-title": group.group(1) if group else "",
            }
        elif line and not line.startswith("#"):
            if current_info:
                current_info["url"] = line
                channels.append(current_info)
                current_info = {}
    return channels


def combine_playlists(urls):
    """Combine playlists smartly — auto sports logo + skip duplicates"""
    combined = []
    seen_names = {}  # name -> set(urls)

    SPORTS_LOGO = "https://i.postimg.cc/rwbHWYY7/livesports.png"

    SPORTS_KEYWORDS = [
        "sports", "live sports", "sport",
        "football", "footbol", "football", "cricket"
    ]

    for src in urls:
        if not src:
            continue
        playlist = read_m3u(src)
        if not playlist:
            continue

        for ch in playlist:
            original_name = ch["name"].strip()
            name_lower = original_name.lower()
            url = ch["url"].strip()


            if not ch["tvg-logo"] or ch["tvg-logo"].strip() == "":
                if any(word in name_lower for word in SPORTS_KEYWORDS):
                    ch["tvg-logo"] = SPORTS_LOGO

            key = name_lower

            if key in seen_names:
                if url not in seen_names[key]:
                    seen_names[key].add(url)
                    combined.append(ch)
            else:
                seen_names[key] = {url}
                combined.append(ch)

    return combined


def write_playlist(channels, promo, output_file):
    """Write merged playlist"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Auto-updated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # --- Promo always first ---
        f.write(f'#EXTINF:-1 tvg-logo="{promo["tvg-logo"]}" group-title="{promo["group-title"]}",{promo["name"]}\n')
        f.write(f'{promo["url"]}\n')

        for ch in channels:
            f.write(f'#EXTINF:-1 tvg-logo="{ch["tvg-logo"]}" group-title="{ch["group-title"]}",{ch["name"]}\n')
            f.write(f'{ch["url"]}\n')

    print(f" playlist.m3u generated successfully ({len(channels) + 1} channels total)")


def main():
    urls = [
        os.getenv("PLAYLIST_URL_1", "").strip(),
        os.getenv("PLAYLIST_URL_2", "").strip(),
        os.getenv("PLAYLIST_URL_3", "").strip(),
    ]
    urls = [u for u in urls if u]

    if not urls:
        print("")
        return

    merged = combine_playlists(urls)
    if not merged:
        print("")
        return

    write_playlist(merged, PROMO_CHANNEL, OUTFILE)


if __name__ == "__main__":
    main()
