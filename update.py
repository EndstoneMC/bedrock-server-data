import hashlib
import json
import logging
import re
from packaging.version import Version
from pathlib import Path
from tempfile import TemporaryDirectory

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

URL = "https://www.minecraft.net/en-us/download/server/bedrock"
DATAFILE_PATH = Path("bedrock_server_data.json")


def get_download_urls():
    response = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
        },
    )
    soup = BeautifulSoup(response.content, "html.parser")

    windows_link = soup.find("a", {"data-platform": "serverBedrockWindows"}).get("href")
    linux_link = soup.find("a", {"data-platform": "serverBedrockLinux"}).get("href")

    return windows_link, linux_link


def download_file(url, filename):
    response = requests.get(url, stream=True, allow_redirects=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 8192

    with tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True, desc=f"Downloading {filename.name}") as progress:
        with filename.open(mode="wb") as file:
            for data in response.iter_content(block_size):
                progress.update(len(data))
                file.write(data)


def compute_checksum(filename):
    with open(filename, "rb") as f:
        file_data = f.read()

    logging.info("Computing SHA256...")
    sha256 = hashlib.sha256(file_data).hexdigest()

    return sha256


def load_data():
    if DATAFILE_PATH.exists():
        with DATAFILE_PATH.open(mode="r") as f:
            return json.load(f)
    return {"binary": {}}


def save_data(data):
    DATAFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATAFILE_PATH.open(mode="w") as f:
        json.dump(data, f, indent=2)


def update_data(version, windows_url, linux_url, windows_sha256, linux_sha256):
    data = load_data()

    data["binary"][version] = {
        "windows": {
            "url": windows_url,
            "sha256": windows_sha256,
        },
        "linux": {
            "url": linux_url,
            "sha256": linux_sha256,
        },
    }
    save_data(data)


def main():
    logging.basicConfig(level=logging.INFO)

    windows_url, linux_url = get_download_urls()

    version_pattern_modified = r"bedrock-server-(\d+\.\d+(\.\d+){1,2})\.zip"
    windows_version = re.search(version_pattern_modified, windows_url)
    linux_version = re.search(version_pattern_modified, linux_url)
    assert windows_version is not None and linux_version is not None, "Unable to extract version from url"
    windows_version, linux_version = windows_version.group(1), linux_version.group(1)

    version = Version(windows_version).release
    if len(version) == 4:
        version = version[:3]
    elif len(version) == 3:
        version = version[:2]
    else:
        raise ValueError(f"Invalid version: v{version}")

    version = ".".join(map(str, version))
    logging.info(f"Processing version: v{version}")
    data = load_data()

    if version in data:
        logging.info(f"Version v{version} is up to date. Nothing to do.")
        return

    with TemporaryDirectory() as tmp:
        windows_filename = Path(tmp, "windows_server.zip")
        linux_filename = Path(tmp, "linux_server.zip")

        logging.info(f"Processing Bedrock Server for Windows v{version}...")
        download_file(windows_url, windows_filename)
        windows_checksums = compute_checksum(windows_filename)

        logging.info(f"Processing Bedrock Server for Linux v{version}...")
        download_file(linux_url, linux_filename)
        linux_checksums = compute_checksum(linux_filename)

        logging.info("Updating data...")
        update_data(version, windows_url, linux_url, windows_checksums, linux_checksums)

        logging.info(f"Processed version: v{version}")


if __name__ == "__main__":
    main()
