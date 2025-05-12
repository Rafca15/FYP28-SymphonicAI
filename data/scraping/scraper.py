import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Base URL of the main page
MAIN_PAGE_URL = "https://tpgettys.weebly.com/early-music-midi-files.html"

# Directory to save MIDI files
SAVE_DIR = "midi_files"
os.makedirs(SAVE_DIR, exist_ok=True)

def get_subpage_links(url):
    """Fetch the main page and extract links leading to subpages containing MIDI files."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to access {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    subpage_links = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(MAIN_PAGE_URL, href)
        subpage_links.append(full_url)

    return subpage_links

def get_midi_links(subpage_url):
    """Fetch a subpage and extract MIDI file links."""
    response = requests.get(subpage_url)
    if response.status_code != 200:
        print(f"Failed to access {subpage_url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    midi_links = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".mid") or href.endswith(".midi"):  # Look for MIDI file extensions
            full_url = urljoin(subpage_url, href)
            midi_links.append(full_url)

    return midi_links

def download_midi(midi_url):
    """Download a MIDI file and save it locally."""
    file_name = os.path.join(SAVE_DIR, os.path.basename(midi_url))
    
    try:
        response = requests.get(midi_url, stream=True)
        response.raise_for_status()
        
        with open(file_name, "wb") as midi_file:
            for chunk in response.iter_content(chunk_size=1024):
                midi_file.write(chunk)

        print(f"Downloaded: {file_name}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download {midi_url}: {e}")

def main():
    print("Fetching subpage links...")
    subpage_links = get_subpage_links(MAIN_PAGE_URL)

    if not subpage_links:
        print("No subpages found.")
        return

    print(f"Found {len(subpage_links)} subpages. Extracting MIDI files...")

    all_midi_links = []
    for subpage_url in subpage_links:
        midi_links = get_midi_links(subpage_url)
        all_midi_links.extend(midi_links)

    if not all_midi_links:
        print("No MIDI files found.")
        return

    print(f"Found {len(all_midi_links)} MIDI files. Downloading...")

    for midi_url in all_midi_links:
        download_midi(midi_url)

if __name__ == "__main__":
    main()
