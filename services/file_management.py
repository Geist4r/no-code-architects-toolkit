# Copyright (c) 2025 Stephen G. Pope
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.



import os
import uuid
import requests
from urllib.parse import urlparse, parse_qs
import mimetypes

def get_extension_from_url(url):
    """Extract file extension from URL or content type.
    
    Args:
        url (str): The URL to extract the extension from
        
    Returns:
        str: The file extension including the dot (e.g., '.jpg')
        
    Raises:
        ValueError: If no valid extension can be determined from the URL or content type
    """
    # First try to get extension from URL
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path:
        ext = os.path.splitext(path)[1].lower()
        if ext:
            return ext

    # If no extension in URL, try to determine from content type
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.head(url, allow_redirects=True, headers=headers)
        content_type = response.headers.get('content-type', '').split(';')[0]
        ext = mimetypes.guess_extension(content_type)
        if ext:
            return ext.lower()
    except:
        pass

    # If we can't determine the extension, raise an error
    raise ValueError(f"Could not determine file extension from URL: {url}")

def download_file(url, storage_path="/tmp/", custom_headers=None):
    """Download a file from URL to local storage with optional custom headers.
    
    Args:
        url (str): The URL to download from
        storage_path (str): Local storage path
        custom_headers (dict): Optional custom headers (e.g., {'Authorization': 'Bearer token'})
        
    Returns:
        str: Path to the downloaded file
    """
    # Create storage directory if it doesn't exist
    os.makedirs(storage_path, exist_ok=True)

    # Rewrite external MinIO link to internal Docker address if needed
    minio_external = os.environ.get("S3_PUBLIC_URL", "http://78.46.146.79:9000")
    minio_internal = os.environ.get("S3_ENDPOINT_URL", "http://minio:9000")
    if url.startswith(minio_external):
        url = url.replace(minio_external, minio_internal, 1)

    file_id = str(uuid.uuid4())
    extension = get_extension_from_url(url)
    local_filename = os.path.join(storage_path, f"{file_id}{extension}")


    import logging
    logger = logging.getLogger(__name__)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Merge custom headers if provided
        if custom_headers:
            headers.update(custom_headers)

        logger.info(f"Downloading file from URL: {url}")
        response = requests.get(url, stream=True, headers=headers)
        logger.info(f"HTTP status: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        response.raise_for_status()

        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"File downloaded successfully: {local_filename}")
        return local_filename
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {e}")
        if os.path.exists(local_filename):
            os.remove(local_filename)
        raise e

