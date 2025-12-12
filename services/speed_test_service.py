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
from core.i18n_manager import _

# Default mirrors list
DEFAULT_MIRRORS = [
    "http://deb.debian.org/debian",
    # CDN variants
    "http://cdn-aws.deb.debian.org/debian",
    "http://cloudfront.debian.net/debian",
    # Official country mirrors
    "http://ftp.us.debian.org/debian",
    "http://ftp.uk.debian.org/debian",
    "http://ftp.de.debian.org/debian",
    "http://ftp.fr.debian.org/debian",
    "http://ftp.es.debian.org/debian",
    "http://ftp.it.debian.org/debian",
    "http://ftp.br.debian.org/debian",
    # Popular mirrors
    "http://mirrors.kernel.org/debian",
    "http://debian.mirrors.ovh.net/debian",
    "http://mirror.bytemark.co.uk/debian",
    "http://mirror.netcologne.de/debian",
    "http://ftp.heanet.ie/mirrors/debian",
    "http://ftp.riken.jp/debian",
    "http://ftp.snt.utwente.nl/debian",
    "http://mirror.init7.net/debian",
    # Chinese mirrors
    "http://mirrors.ustc.edu.cn/debian",
    "http://mirrors.tuna.tsinghua.edu.cn/debian",
    "http://mirrors.aliyun.com/debian",
    "http://mirror.sjtu.edu.cn/debian",
    # Other useful mirrors
    "http://mirror.math.princeton.edu/pub/debian",
    "http://mirror.corenet.jp/debian",
    "http://ftp.uni-kl.de/debian",
    "http://mirror.linux.org.au/debian",
    "http://mirror.ox.ac.uk/debian"
]

class RepoSpeedTester:
    """Service to test APT repository speeds."""
    
    def __init__(self, mirrors: List[str] = None):
        self.mirrors = mirrors or DEFAULT_MIRRORS
        # timeouts for requests: (connect_timeout, read_timeout)
        self.timeout = (3, 5)
        self.test_file_size = 512 * 1024  # 512KB for quick test
        # maximum seconds to wait for all mirrors to complete before marking remaining as timed out
        self.per_mirror_timeout = 12
        
    def measure_download_speed(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> Dict[str, Any]:
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
                        last_update = download_start

                        for chunk in response.iter_content(chunk_size=8192):
                            downloaded += len(chunk)

                            now = time.time()
                            # send intermittent progress updates (throttled)
                            if progress_callback and (now - last_update >= 0.25 or downloaded >= self.test_file_size):
                                elapsed_partial = now - download_start
                                if elapsed_partial > 0:
                                    speed_partial = (downloaded / (1024 * 1024)) / elapsed_partial
                                else:
                                    speed_partial = 0.0

                                try:
                                    progress_callback({
                                        'status': 'in_progress',
                                        'downloaded_bytes': downloaded,
                                        'speed_mbps': speed_partial,
                                        'latency_ms': elapsed_partial * 1000,
                                        'url': url
                                    })
                                except Exception:
                                    pass

                                last_update = now

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
            # Wrap progress updates to include url and country
            def _progress_cb(partial: Dict[str, Any]):
                partial_result = {
                    'url': mirror_url,
                    'country': country,
                    **partial
                }
                # Append/update partial into all_results for visibility
                all_results.append(partial_result)
                if callback:
                    try:
                        callback(partial_result)
                    except Exception as e:
                        log_error("Error in speed test callback (partial)", e)

            speed_result = self.measure_download_speed(mirror_url, progress_callback=_progress_cb)

            result = {
                'url': mirror_url,
                'country': country,
                **speed_result
            }

            # Remove previous partial entries for this URL and append final
            all_results[:] = [r for r in all_results if r.get('url') != mirror_url]
            all_results.append(result)

            if callback:
                try:
                    callback(result)
                except Exception as e:
                    log_error("Error in speed test callback", e)

            return result
        
        # Run tests in a thread pool and avoid indefinite blocking by waiting
        # up to `per_mirror_timeout` seconds for unfinished futures.
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(test_single_mirror, mirror): mirror for mirror in self.mirrors}

            # Wait in short intervals until either all done or timeout
            unfinished = set(futures.keys())
            wait_interval = 0.5
            elapsed = 0.0
            while unfinished and elapsed < self.per_mirror_timeout:
                done, not_done = concurrent.futures.wait(unfinished, timeout=wait_interval, return_when=concurrent.futures.FIRST_COMPLETED)
                unfinished = not_done
                elapsed += wait_interval

            # Any futures still unfinished after timeout -> mark as timed out and try to cancel
            if unfinished:
                for fut in list(unfinished):
                    mirror_url = futures.get(fut)
                    try:
                        fut.cancel()
                    except Exception:
                        pass

                    # append a timeout result for the mirror so UI can update and progress completes
                    timeout_result = {
                        'url': mirror_url,
                        'country': self.get_mirror_country(mirror_url),
                        'speed_mbps': 0,
                        'latency_ms': 9999,
                        'status': 'timeout'
                    }
                    all_results.append(timeout_result)
                    if callback:
                        try:
                            callback(timeout_result)
                        except Exception as e:
                            log_error("Error in speed test callback (timeout)", e)
        
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
                "deb.debian.org": _("Global CDN"),
                "cdn-aws.deb.debian.org": _("Global CDN"),
                "cloudfront.debian.net": _("Global CDN"),
                "mirrors.kernel.org": _("Global Mirror"),
                "ftp.us.debian.org": _("United States"),
                "ftp.uk.debian.org": _("United Kingdom"), 
                "ftp.de.debian.org": _("Germany"),
                "ftp.fr.debian.org": _("France"),
                "ftp.au.debian.org": _("Australia"),
                "ftp.jp.debian.org": _("Japan"),
                "ftp.br.debian.org": _("Brazil"),
                "ftp.es.debian.org": _("Spain"),
                "ftp.it.debian.org": _("Italy"),
                "ftp.cn.debian.org": _("China"),
                "ftp.ru.debian.org": _("Russia"),
                "ftp.ca.debian.org": _("Canada"),
                "debian.mirrors.ovh.net": _("France"),
                "mirror.bytemark.co.uk": _("United Kingdom"),
                "mirror.netcologne.de": _("Germany"),
                "ftp.heanet.ie": _("Ireland"),
                "ftp.riken.jp": _("Japan"),
                "ftp.snt.utwente.nl": _("Netherlands"),
                "mirror.init7.net": _("Switzerland"),
                "mirrors.ustc.edu.cn": _("China"),
                "mirrors.tuna.tsinghua.edu.cn": _("China"),
                "mirrors.aliyun.com": _("China"),
                "mirror.sjtu.edu.cn": _("China"),
                "mirror.math.princeton.edu": _("United States"),
                "mirror.corenet.jp": _("Japan"),
                "ftp.uni-kl.de": _("Germany"),
                "mirror.linux.org.au": _("Australia"),
                "mirror.ox.ac.uk": _("United Kingdom")
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
            
            return _("Unknown")
        except Exception:
            return _("Unknown")

def get_country_mirrors() -> Dict[str, List[str]]:
    """Returns mirrors organized by country."""
    return {
        _('Global'): [
            'http://deb.debian.org/debian',
            'http://cdn-aws.deb.debian.org/debian',
            'http://cloudfront.debian.net/debian',
            'http://mirrors.kernel.org/debian'
        ],
        _('United States'): [
            'http://ftp.us.debian.org/debian',
            'http://mirror.math.princeton.edu/pub/debian'
        ],
        _('United Kingdom'): [
            'http://ftp.uk.debian.org/debian',
            'http://mirror.bytemark.co.uk/debian',
            'http://mirror.ox.ac.uk/debian'
        ],
        _('Germany'): [
            'http://ftp.de.debian.org/debian',
            'http://mirror.netcologne.de/debian',
            'http://ftp.uni-kl.de/debian'
        ],
        _('France'): [
            'http://ftp.fr.debian.org/debian',
            'http://debian.mirrors.ovh.net/debian'
        ],
        _('Spain'): ['http://ftp.es.debian.org/debian'],
        _('Italy'): ['http://ftp.it.debian.org/debian'],
        _('Brazil'): ['http://ftp.br.debian.org/debian'],
        _('China'): [
            'http://mirrors.ustc.edu.cn/debian',
            'http://mirrors.tuna.tsinghua.edu.cn/debian',
            'http://mirrors.aliyun.com/debian',
            'http://mirror.sjtu.edu.cn/debian'
        ],
        _('Japan'): [
            'http://ftp.riken.jp/debian',
            'http://mirror.corenet.jp/debian'
        ],
        _('Netherlands'): ['http://ftp.snt.utwente.nl/debian'],
        _('Ireland'): ['http://ftp.heanet.ie/mirrors/debian'],
        _('Australia'): ['http://mirror.linux.org.au/debian'],
        _('Canada'): ['http://ftp.ca.debian.org/debian'],
        _('Switzerland'): ['http://mirror.init7.net/debian']
    }
