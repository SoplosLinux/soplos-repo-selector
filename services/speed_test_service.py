"""
Repository Speed Test Service.
Measures download speed and latency of APT mirrors.
"""

import time
import socket
import requests
import concurrent.futures
from urllib.parse import urlparse
from typing import List, Dict, Any, Callable, Optional

from utils.logger import log_info, log_error, log_warning

# Default mirrors list
DEFAULT_MIRRORS = [
    "http://deb.debian.org/debian",
    "http://ftp.us.debian.org/debian",
    "http://ftp.uk.debian.org/debian",
    "http://ftp.de.debian.org/debian",
    "http://ftp.fr.debian.org/debian",
    "http://ftp.es.debian.org/debian",
    "http://ftp.it.debian.org/debian",
    "http://ftp.br.debian.org/debian"
]

class RepoSpeedTester:
    """Service to test APT repository speeds."""
    
    def __init__(self, mirrors: List[str] = None):
        self.mirrors = mirrors or DEFAULT_MIRRORS
        self.timeout = 5
        self.test_file_size = 512 * 1024  # 512KB for quick test
        
    def measure_download_speed(self, url: str) -> Dict[str, Any]:
        """
        Measures real download speed from a repository.
        Returns dictionary with results.
        """
        try:
            test_paths = [
                "dists/stable/Release",
                "dists/bookworm/Release", 
                "ls-lR.gz"
            ]
            
            for test_path in test_paths:
                test_url = f"{url.rstrip('/')}/{test_path}"
                
                try:
                    start_time = time.time()
                    response = requests.get(test_url, timeout=self.timeout, stream=True)
                    
                    if response.status_code == 200:
                        downloaded = 0
                        download_start = time.time()
                        
                        for chunk in response.iter_content(chunk_size=8192):
                            downloaded += len(chunk)
                            if downloaded > self.test_file_size:
                                break
                        
                        elapsed = time.time() - download_start
                        
                        if elapsed > 0:
                            speed_mbps = (downloaded / (1024 * 1024)) / elapsed
                        else:
                            speed_mbps = 0
                        
                        return {
                            'speed_mbps': speed_mbps,
                            'latency_ms': elapsed * 1000,
                            'status': 'success',
                            'downloaded_bytes': downloaded
                        }
                        
                except requests.exceptions.Timeout:
                    continue
                except requests.exceptions.ConnectionError:
                    continue
                except Exception as e:
                    log_error(f"Error testing {test_url}", e)
                    continue
            
            return {'speed_mbps': 0, 'latency_ms': 9999, 'status': 'no_valid_files'}
                
        except Exception as e:
            log_error(f"Error measuring speed for {url}", e)
            return {'speed_mbps': 0, 'latency_ms': 9999, 'status': 'error', 'error': str(e)}

    def test_mirrors_parallel(self, callback: Callable[[Dict], None] = None, max_workers: int = 3) -> List[Dict]:
        """
        Tests mirrors in parallel and returns all results.
        Ordered by speed (descending).
        """
        all_results = []
        
        def test_single_mirror(mirror_url):
            country = self.get_mirror_country(mirror_url)
            speed_result = self.measure_download_speed(mirror_url)
            
            result = {
                'url': mirror_url,
                'country': country,
                **speed_result
            }
            
            all_results.append(result)
            
            if callback:
                try:
                    callback(result)
                except Exception as e:
                    log_error("Error in speed test callback", e)
            
            return result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(test_single_mirror, mirror) for mirror in self.mirrors]
            concurrent.futures.wait(futures)
        
        # Sort results
        successful_results = [r for r in all_results if r['status'] == 'success']
        failed_results = [r for r in all_results if r['status'] != 'success']
        
        successful_results.sort(key=lambda x: x['speed_mbps'], reverse=True)
        # Sort failed by latency (though usually it's maxed out)
        
        return successful_results + failed_results

    def get_mirror_country(self, url: str) -> str:
        """Determines country from URL."""
        try:
            hostname = urlparse(url).netloc
            
            country_map = {
                "deb.debian.org": "Global CDN",
                "ftp.us.debian.org": "United States",
                "ftp.uk.debian.org": "United Kingdom", 
                "ftp.de.debian.org": "Germany",
                "ftp.fr.debian.org": "France",
                "ftp.au.debian.org": "Australia",
                "ftp.jp.debian.org": "Japan",
                "ftp.br.debian.org": "Brazil",
                "ftp.es.debian.org": "Spain",
                "ftp.it.debian.org": "Italy",
                "ftp.cn.debian.org": "China",
                "ftp.ru.debian.org": "Russia",
                "ftp.ca.debian.org": "Canada"
            }
            
            for domain, country in country_map.items():
                if domain in hostname:
                    return country
            
            # Try to guess from ftp.CC.debian.org
            if hostname.endswith(".debian.org"):
                parts = hostname.split(".")
                if parts[0].startswith("ftp.") and len(parts[0]) > 4:
                    code = parts[0][4:].upper()
                    return f"Code: {code}"
            
            return "Unknown"
        except Exception:
            return "Unknown"

def get_country_mirrors() -> Dict[str, List[str]]:
    """Returns mirrors organized by country."""
    return {
        'Global': ['http://deb.debian.org/debian'],
        'United States': ['http://ftp.us.debian.org/debian', 'http://mirrors.kernel.org/debian'],
        'United Kingdom': ['http://ftp.uk.debian.org/debian'],
        'Germany': ['http://ftp.de.debian.org/debian'],
        'France': ['http://ftp.fr.debian.org/debian'],
        'Spain': ['http://ftp.es.debian.org/debian'],
        'Italy': ['http://ftp.it.debian.org/debian'],
        'Brazil': ['http://ftp.br.debian.org/debian'],
        'China': ['http://ftp.cn.debian.org/debian'],
        'Russia': ['http://ftp.ru.debian.org/debian'],
        # Add more as needed
    }
