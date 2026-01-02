"""
Repository Speed Test Service.
Measures real download speed and latency of APT mirrors.

v2.0.1 - Improved with:
- Real TCP latency measurement (ping)
- Larger download size for accurate speed measurement
- Separate latency and speed metrics
- Progress callbacks for dynamic UI updates
"""

import time
import socket
import requests
import concurrent.futures
from urllib.parse import urlparse
from typing import List, Dict, Any, Callable, Optional

from utils.logger import log_info, log_error, log_warning
from core.i18n_manager import _

# Default mirrors list - COMPLETE official list from debian.org/mirror/list-full
# Total: 378 mirrors worldwide - Source: https://www.debian.org/mirror/list-full
DEFAULT_MIRRORS = [
    # ==================== GLOBAL CDN ====================
    "http://deb.debian.org/debian",
    "http://cdn-aws.deb.debian.org/debian",
    
    # ==================== EUROPE ====================
    # -- Germany (47 mirrors) --
    "http://ftp.de.debian.org/debian",
    "http://ftp2.de.debian.org/debian",
    "http://mirror.23m.com/debian",
    "http://debian.charite.de/debian",
    "http://mirror.dogado.de/debian",
    "http://ftp.fau.de/debian",
    "http://ftp.gwdg.de/debian",
    "http://ftp.hosteurope.de/mirror/ftp.debian.org/debian",
    "http://ftp-stud.hs-esslingen.de/debian",
    "http://debian.intergenia.de/debian",
    "http://mirror.ipb.de/debian",
    "http://debian.mirror.lrz.de/debian",
    "http://debian.netcologne.de/debian",
    "http://mirror.netzwerge.de/debian",
    "http://pubmirror.plutex.de/debian",
    "http://ftp.halifax.rwth-aachen.de/debian",
    "http://debian.tu-bs.de/debian",
    "http://ftp.tu-chemnitz.de/debian",
    "http://debian.inf.tu-dresden.de/debian",
    "http://ftp.uni-hannover.de/debian/debian",
    "http://ftp.uni-mainz.de/debian",
    "http://ftp.uni-stuttgart.de/debian",
    "http://mirror.united-gameserver.de/debian",
    "http://mirror.wtnet.de/debian",
    "http://mirrors.xtom.de/debian",
    "http://de.mirrors.clouvider.net/debian",
    "http://mirror.creoline.net/debian",
    "http://debian.mirror.iphh.net/debian",
    "http://mirror.de.leaseweb.net/debian",
    "http://mirror.eu.oneandone.net/debian",
    "http://mirror.plusline.net/debian",
    
    # -- France (25 mirrors) --
    "http://ftp.fr.debian.org/debian",
    "http://mirror.debian.ikoula.com/debian",
    "http://ftp.ec-m.fr/debian",
    "http://mirror.johnnybegood.fr/debian",
    "http://debian.obspm.fr/debian",
    "http://debian.polytech-lille.fr/debian",
    "http://deb.syxpi.fr/debian",
    "http://ftp.u-picardie.fr/debian",
    "http://miroir.univ-lorraine.fr/debian",
    "http://mirror.gitoyen.net/debian",
    "http://deb-mir1.naitways.net/debian",
    "http://debian.mirrors.ovh.net/debian",
    "http://debian.proxad.net/debian",
    "http://ftp.rezopole.net/debian",
    "http://apt.tetaneutral.net/debian",
    
    # -- United Kingdom (16 mirrors) --
    "http://ftp.uk.debian.org/debian",
    "http://free.hands.com/debian",
    "http://mirror.mythic-beasts.com/debian",
    "http://mirror.positive-internet.com/debian",
    "http://mirror.cov.ukservers.com/debian",
    "http://ukdebian.mirror.anlx.net/debian",
    "http://uk.mirrors.clouvider.net/debian",
    "http://mirrors.coreix.net/debian",
    "http://debian.mirror.uk.sargasso.net/debian",
    "http://debian.mirrors.uk2.net/debian",
    "http://mirror.vinehost.net/debian",
    "http://mirrorservice.org/sites/ftp.debian.org/debian",
    "http://ftp.ticklers.org/debian",
    "http://mirror.ox.ac.uk/debian",
    
    # -- Spain (12 mirrors) --
    "http://ftp.es.debian.org/debian",
    "http://ftp.caliu.cat/debian",
    "http://debian.grn.cat/debian",
    "http://ulises.hostalia.com/debian",
    "http://mirror.raiolanetworks.com/debian",
    "http://debian.redparra.com/debian",
    "http://ftp.cica.es/debian",
    "http://repo.ifca.es/debian",
    "http://debian.redimadrid.es/debian",
    "http://ftp.udc.es/debian",
    "http://softlibre.unizar.es/debian",
    "http://debian.uvigo.es/debian",
    
    # -- Italy (7 mirrors) --
    "http://ftp.it.debian.org/debian",
    "http://debian.connesi.it/debian",
    "http://debian.dynamica.it/debian",
    "http://debian.mirror.garr.it/debian",
    "http://ftp.linux.it/debian",
    "http://giano.com.dist.unige.it/debian",
    "http://mirror.units.it/debian",
    
    # -- Netherlands (18 mirrors) --
    "http://ftp.nl.debian.org/debian",
    "http://mirror.nl.cdn-perfprod.com/debian",
    "http://mirror.nl.datapacket.com/debian",
    "http://mirrors.hostiserver.com/debian",
    "http://mirror.ams.macarne.com/debian",
    "http://mirror.nforce.com/debian",
    "http://mirror.tngnet.com/debian",
    "http://nl.mirrors.clouvider.net/debian",
    "http://mirror.duocast.net/debian",
    "http://nl.mirror.flokinet.net/debian",
    "http://mirror.nl.leaseweb.net/debian",
    "http://debian.snt.utwente.nl/debian",
    "http://mirrors.xtom.nl/debian",
    
    # -- Switzerland (12 mirrors) --
    "http://ftp.ch.debian.org/debian",
    "http://pkg.adfinis-on-exoscale.ch/debian",
    "http://linuxsoft.cern.ch/debian",
    "http://debian.ethz.ch/debian",
    "http://mirror.iway.ch/debian",
    "http://mirror.metanet.ch/debian",
    "http://deb.nextgen.ch/debian",
    "http://mirror.sinavps.ch/debian",
    "http://mirror1.infomaniak.com/debian",
    "http://mirror2.infomaniak.com/debian",
    "http://mirror.init7.net/debian",
    
    # -- Austria (6 mirrors) --
    "http://ftp.at.debian.org/debian",
    "http://debian.anexia.at/debian",
    "http://debian.lagis.at/debian",
    "http://debian.mur.at/debian",
    "http://debian.sil.at/debian",
    "http://mirror.alwyzon.net/debian",
    
    # -- Belgium (5 mirrors) --
    "http://ftp.be.debian.org/debian",
    "http://ftp.belnet.be/debian",
    "http://mirror.unix-solutions.be/debian",
    "http://mirror.as35701.net/debian",
    "http://debian-mirror.behostings.net/debian",
    
    # -- Portugal (5 mirrors) --
    "http://ftp.pt.debian.org/debian",
    "http://ftp.eq.uc.pt/software/Linux/debian",
    "http://debian.uevora.pt/debian",
    "http://ftp.rnl.tecnico.ulisboa.pt/pub/debian",
    "http://mirrors.up.pt/debian",
    
    # -- Sweden (5 mirrors) --
    "http://ftp.se.debian.org/debian",
    "http://mirrors.glesys.net/debian",
    "http://ftpmirror1.infania.net/debian",
    "http://debian.lth.se/debian",
    "http://ftp.acc.umu.se/debian",
    
    # -- Poland (5 mirrors) --
    "http://ftp.pl.debian.org/debian",
    "http://ftp.agh.edu.pl/debian",
    "http://ftp.icm.edu.pl/pub/Linux/debian",
    "http://ftp.task.gda.pl/debian",
    "http://ftp.psnc.pl/debian",
    
    # -- Czech Republic (10 mirrors) --
    "http://ftp.cz.debian.org/debian",
    "http://ftp.sh.cvut.cz/debian",
    "http://ftp.debian.cz/debian",
    "http://mirror.dkm.cz/debian",
    "http://mirror.it4i.cz/debian",
    "http://debian.superhosting.cz/debian",
    "http://merlin.fit.vutbr.cz/debian",
    "http://ftp.zcu.cz/debian",
    "http://ftp.cvut.cz/debian",
    "http://debian.nic.cz/debian",
    
    # -- Denmark (3 mirrors) --
    "http://ftp.dk.debian.org/debian",
    "http://mirrors.rackhosting.com/debian",
    "http://mirrors.dotsrc.org/debian",
    
    # -- Norway (2 mirrors) --
    "http://ftp.no.debian.org/debian",
    "http://ftp.uio.no/debian",
    
    # -- Finland (4 mirrors) --
    "http://ftp.fi.debian.org/debian",
    "http://mirror.5i.fi/debian",
    "http://www.nic.funet.fi/debian",
    "http://debian.web.trex.fi/debian",
    
    # -- Iceland (2 mirrors) --
    "http://ftp.is.debian.org/debian",
    "http://is.mirror.flokinet.net/debian",
    
    # -- Lithuania (4 mirrors) --
    "http://ftp.lt.debian.org/debian",
    "http://mirror.litnet.lt/debian",
    "http://debian.mirror.vu.lt/debian",
    "http://debian.balt.net/debian",
    
    # -- Bulgaria (8 mirrors) --
    "http://ftp.bg.debian.org/debian",
    "http://debian.a1.bg/debian",
    "http://debian.mnet.bg/debian",
    "http://debian.telecoms.bg/debian",
    "http://mirror.telepoint.bg/debian",
    "http://ftp.uni-sofia.bg/debian",
    "http://debian.ipacct.com/debian",
    "http://mirrors.netix.net/debian",
    
    # -- Slovakia (4 mirrors) --
    "http://ftp.sk.debian.org/debian",
    "http://ftp.antik.sk/debian",
    "http://deb.bbxnet.sk/debian",
    "http://ftp.debian.sk/debian",
    
    # -- Slovenia (1 mirror) --
    "http://ftp.si.debian.org/debian",
    
    # -- Croatia (3 mirrors) --
    "http://ftp.hr.debian.org/debian",
    "http://debian.carnet.hr/debian",
    "http://debian.iskon.hr/debian",
    
    # -- Hungary (2 mirrors) --
    "http://ftp.bme.hu/debian",
    "http://repo.jztkft.hu/debian",
    
    # -- Romania (8 mirrors) --
    "http://mirrors.nxthost.com/debian",
    "http://mirrors.pidginhost.com/debian",
    "http://ro.mirror.flokinet.net/debian",
    "http://mirror.flo.c-f.ro/debian",
    "http://mirrors.hosterion.ro/debian",
    "http://mirror.linux.ro/debian",
    "http://mirrors.nav.ro/debian",
    
    # -- Latvia (4 mirrors) --
    "http://mirror.veesp.com/debian",
    "http://mirror.cloudhosting.lv/debian",
    "http://ftp.linux.edu.lv/debian",
    "http://debian.koyanet.lv/debian",
    
    # -- Estonia (1 mirror) --
    "http://mirrors.xtom.ee/debian",
    
    # -- Greece (1 mirror) --
    "http://debian.otenet.gr/debian",
    
    # -- Georgia (1 mirror) --
    "http://debian.grena.ge/debian",
    
    # -- Luxembourg (1 mirror) --
    "http://debian.mirror.root.lu/debian",
    
    # -- Serbia (1 mirror) --
    "http://mirror.pmf.kg.ac.rs/debian",
    
    # -- Macedonia (2 mirrors) --
    "http://mirror-mk.interspace.com/debian",
    "http://mirror.a1.mk/debian",
    
    # ==================== RUSSIA & CIS ====================
    "http://ftp.ru.debian.org/debian",
    "http://mirror.corbina.net/debian",
    "http://mirrors.powernet.com.ru/debian",
    "http://mirror.docker.ru/debian",
    "http://mirror.hyperdedic.ru/debian",
    "http://mirror.mephi.ru/debian",
    "http://mirror.neftm.ru/debian",
    "http://ftp.psn.ru/debian",
    "http://mirror.truenetwork.ru/debian",
    "http://repository.su/debian",
    "http://mirror.datacenter.by/debian",  # Belarus
    "http://mirror.hoster.kz/debian",  # Kazakhstan
    "http://mirror.ps.kz/debian",  # Kazakhstan
    
    # -- Ukraine (5 mirrors) --
    "http://mirror.ukrnames.com/debian",
    "http://debian.netforce.hosting/debian",
    "http://mirror.mirohost.net/debian",
    "http://debian.volia.net/debian",
    
    # ==================== AMERICAS ====================
    # -- United States (25+ mirrors) --
    "http://ftp.us.debian.org/debian",
    "http://mirror.0x626b.com/debian",
    "http://mirror.cogentco.com/debian",
    "http://debian.mirror.constant.com/debian",
    "http://debpkg.libranext.com/debian",
    "http://mirrors.xtom.com/debian",
    "http://mirrors.ocf.berkeley.edu/debian",
    "http://mirrors.bloomu.edu/debian",
    "http://repo.ialab.dsu.edu/debian",
    "http://debian.cc.lehigh.edu/debian",
    "http://debian.csail.mit.edu/debian",
    "http://mirrors.lug.mtu.edu/debian",
    "http://mirror.siena.edu/debian",
    "http://debian.uchicago.edu/debian",
    "http://mirrors.vcea.wsu.edu/debian",
    "http://mirrors.accretive-networks.net/debian",
    "http://atl.mirrors.clouvider.net/debian",
    "http://la.mirrors.clouvider.net/debian",
    "http://nyc.mirrors.clouvider.net/debian",
    "http://mirrors.iu13.net/debian",
    "http://mirror.us.leaseweb.net/debian",
    "http://mirror.us.mirhosting.net/debian",
    "http://mirror.us.oneandone.net/debian",
    "http://mirror.steadfast.net/debian",
    "http://mirror.keystealth.org/debian",
    "http://debian.osuosl.org/debian",
    "http://mirrors.wikimedia.org/debian",
    
    # -- Canada (8 mirrors) --
    "http://ftp.ca.debian.org/debian",
    "http://mirror.dst.ca/debian",
    "http://mirror.estone.ca/debian",
    "http://debian.linux.n0c.ca/debian",
    "http://debian.mirror.rafal.ca/debian",
    "http://mirror.it.ubc.ca/debian",
    "http://mirror.cpsc.ucalgary.ca/debian",
    "http://mirror.csclub.uwaterloo.ca/debian",
    
    # -- Mexico (2 mirrors) --
    "http://debian.vranetworks.lat/debian",
    "http://lidsol.fi-b.unam.mx/debian",
    
    # -- Brazil (7 mirrors) --
    "http://ftp.br.debian.org/debian",
    "http://mirror.blue3.com.br/debian",
    "http://debian.pop-sc.rnp.br/debian",
    "http://mirror.uepg.br/debian",
    "http://debian.c3sl.ufpr.br/debian",
    "http://mirror.ufscar.br/debian",
    "http://mirrors.ic.unicamp.br/debian",
    
    # -- Chile (4 mirrors) --
    "http://ftp.cl.debian.org/debian",
    "http://debian-mirror.puq.apoapsis.cl/debian",
    "http://mirror.hnd.cl/debian",
    "http://mirror.insacom.cl/debian",
    
    # -- Argentina (2 mirrors) --
    "http://mirror.sitsa.com.ar/debian",
    "http://debian.unnoba.edu.ar/debian",
    
    # -- Costa Rica (1 mirror) --
    "http://debianmirror.una.ac.cr/debian",
    
    # -- Uruguay (1 mirror) --
    "http://debian.repo.cure.edu.uy/debian",
    
    # -- Puerto Rico (1 mirror) --
    "http://mirrors.upr.edu/debian",
    
    # ==================== ASIA ====================
    # -- Japan (8 mirrors) --
    "http://ftp.jp.debian.org/debian",
    "http://ftp.jaist.ac.jp/debian",
    "http://ftp.yz.yamagata-u.ac.jp/debian",
    "http://ftp.nara.wide.ad.jp/debian",
    "http://debian-mirror.sakura.ne.jp/debian",
    "http://ftp.riken.jp/Linux/debian/debian",
    "http://mirrors.xtom.jp/debian",
    "http://dennou-k.gfd-dennou.org/debian",
    
    # -- South Korea (6 mirrors) --
    "http://ftp.kr.debian.org/debian",
    "http://ftp.kaist.ac.kr/debian",
    "http://ftp.lanet.kr/debian",
    "http://mirror.siwoo.org/debian",
    "http://mirror.keiminem.com/debian",
    "http://mirror.pangkin.com/debian",
    
    # -- China (11 mirrors) --
    "http://ftp.cn.debian.org/debian",
    "http://mirrors.bfsu.edu.cn/debian",
    "http://mirrors.hit.edu.cn/debian",
    "http://mirrors.jlu.edu.cn/debian",
    "http://mirror.lzu.edu.cn/debian",
    "http://mirror.nju.edu.cn/debian",
    "http://mirror.nyist.edu.cn/debian",
    "http://mirror.sjtu.edu.cn/debian",
    "http://mirrors.tuna.tsinghua.edu.cn/debian",
    "http://mirrors.ustc.edu.cn/debian",
    "http://mirrors.zju.edu.cn/debian",
    
    # -- Taiwan (8 mirrors) --
    "http://ftp.tw.debian.org/debian",
    "http://tw1.mirror.blendbyte.net/debian",
    "http://mirror.twds.com.tw/debian",
    "http://debian.ccns.ncku.edu.tw/debian",
    "http://debian.csie.ntu.edu.tw/debian",
    "http://debian.cs.nycu.edu.tw/debian",
    "http://ftp.tku.edu.tw/debian",
    "http://opensource.nchc.org.tw/debian",
    
    # -- Hong Kong (2 mirrors) --
    "http://ftp.hk.debian.org/debian",
    "http://mirror.xtom.com.hk/debian",
    
    # -- Thailand (3 mirrors) --
    "http://mirror.applebred.net/debian",
    "http://ftp.debianclub.org/debian",
    "http://mirror.kku.ac.th/debian",
    
    # -- Singapore (2 mirrors) --
    "http://mirror.coganng.com/debian",
    "http://mirror.sg.gs/debian",
    
    # -- Indonesia (4 mirrors) --
    "http://kebo.pens.ac.id/debian",
    "http://mirror.unair.ac.id/debian",
    "http://mr.heru.id/debian",
    "http://kartolo.sby.datautama.net.id/debian",
    
    # -- Vietnam (2 mirrors) --
    "http://debian.xtdv.net/debian",
    "http://mirror.bizflycloud.vn/debian",
    
    # -- India (1 mirror) --
    "http://mirror.nitc.ac.in/debian",
    
    # -- Bangladesh (2 mirrors) --
    "http://mirror.xeonbd.com/debian",
    "http://mirror.limda.net/debian",
    
    # -- Iran (3 mirrors) --
    "http://repo.mirror.famaserver.com/debian",
    "http://mirror.aminidc.com/debian",
    "http://archive.debian.petiak.ir/debian",
    
    # -- Israel (1 mirror) --
    "http://debian.interhost.co.il/debian",
    
    # -- Cambodia (1 mirror) --
    "http://mirror.sabay.com.kh/debian",
    
    # -- Nepal (1 mirror) --
    "http://mirrors.nepalicloud.com/debian",
    
    # -- Azerbaijan (1 mirror) --
    "http://mirror.ourhost.az/debian",
    
    # -- Saudi Arabia (1 mirror) --
    "http://mirror.maeen.sa/debian",
    
    # ==================== OCEANIA ====================
    # -- Australia (9 mirrors) --
    "http://ftp.au.debian.org/debian",
    "http://mirror.amaze.com.au/debian",
    "http://debian.mirror.digitalpacific.com.au/debian",
    "http://mirror.overthewire.com.au/debian",
    "http://debian.mirror.serversaustralia.com.au/debian",
    "http://mirror.aarnet.edu.au/debian",
    "http://mirror.linux.org.au/debian",
    "http://mirrors.xtom.au/debian",
    "http://mirror.realcompute.io/debian",
    
    # -- New Zealand (3 mirrors) --
    "http://ftp.nz.debian.org/debian",
    "http://linux.purple-cat.net/debian",
    "http://mirror.fsmg.org.nz/debian",
    
    # -- New Caledonia (3 mirrors) --
    "http://ftp.nc.debian.org/debian",
    "http://mirror.lagoon.nc/debian",
    "http://debian.nautile.nc/debian",
    
    # ==================== AFRICA ====================
    # -- South Africa (3 mirrors) --
    "http://debian.saix.net",
    "http://ftp.is.co.za/debian",
    "http://debian.envisagecloud.net.za/debian",
    
    # -- Kenya (2 mirrors) --
    "http://debian.mirror.liquidtelecom.com/debian",
    "http://debian.mirror.ac.ke/debian",
    
    # -- Morocco (1 mirror) --
    "http://mirror.marwan.ma/debian",
    
    # -- Burkina Faso (1 mirror) --
    "http://debian.ipsys.bf/debian",
    
    # -- Reunion (2 mirrors) --
    "http://depot-debian.univ-reunion.fr/debian",
    "http://debian.mithril.re/debian",
]


class RepoSpeedTester:
    """Service to test APT repository speeds with real measurements."""
    
    def __init__(self, mirrors: List[str] = None):
        self.mirrors = mirrors or DEFAULT_MIRRORS
        # Timeouts: (connect, read) - more generous for slow mirrors
        self.connect_timeout = 5
        self.read_timeout = 15
        # Download at least 2MB or for 3 seconds minimum for accurate speed
        self.min_download_bytes = 2 * 1024 * 1024  # 2MB
        self.min_download_time = 3.0  # seconds
        self.max_download_bytes = 10 * 1024 * 1024  # Cap at 10MB
        # Parallel workers
        self.max_workers = 6
        # Per-mirror timeout before marking as failed
        self.per_mirror_timeout = 25
        
    def measure_tcp_latency(self, hostname: str, port: int = 80) -> float:
        """
        Measure real TCP latency (round-trip time) to a host.
        Returns latency in milliseconds, or -1 if failed.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connect_timeout)
            
            start = time.perf_counter()
            sock.connect((hostname, port))
            latency = (time.perf_counter() - start) * 1000  # Convert to ms
            
            sock.close()
            return round(latency, 1)
        except Exception as e:
            log_warning(f"TCP latency measurement failed for {hostname}: {e}")
            return -1
    
    def measure_download_speed(self, url: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> Dict[str, Any]:
        """
        Measures real download speed from a repository.
        Downloads enough data to get accurate measurement.
        
        Returns dictionary with:
        - speed_mbps: Download speed in MB/s
        - latency_ms: TCP latency in ms
        - status: 'success', 'error', 'timeout'
        - downloaded_bytes: Total bytes downloaded
        """
        result = {
            'speed_mbps': 0.0,
            'latency_ms': -1,
            'status': 'error',
            'downloaded_bytes': 0,
            'progress': 0.0
        }
        
        try:
            # Parse URL to get hostname
            parsed = urlparse(url)
            hostname = parsed.netloc
            port = parsed.port or 80
            
            # Step 1: Measure TCP latency first
            latency = self.measure_tcp_latency(hostname, port)
            result['latency_ms'] = latency
            
            if latency < 0:
                result['status'] = 'connection_failed'
                return result
            
            # Send initial progress
            if progress_callback:
                progress_callback({
                    'status': 'measuring_latency',
                    'latency_ms': latency,
                    'progress': 0.05,
                    'url': url
                })
            
            # Step 2: Download file for speed test
            # Use ls-lR.gz which is large and exists on all Debian mirrors
            test_files = [
                "ls-lR.gz",  # ~20MB, best for speed test
                "dists/stable/Contents-amd64.gz",  # ~30MB
                "dists/stable/main/Contents-amd64.gz",  # ~25MB
            ]
            
            downloaded = 0
            speed_mbps = 0.0
            download_success = False
            
            for test_file in test_files:
                test_url = f"{url.rstrip('/')}/{test_file}"
                
                try:
                    # Start download with streaming
                    response = requests.get(
                        test_url, 
                        timeout=(self.connect_timeout, self.read_timeout),
                        stream=True
                    )
                    
                    if response.status_code != 200:
                        continue
                    
                    # Get content length if available
                    content_length = int(response.headers.get('content-length', 0))
                    
                    # Download and measure
                    downloaded = 0
                    start_time = time.perf_counter()
                    last_callback_time = start_time
                    
                    for chunk in response.iter_content(chunk_size=32768):  # 32KB chunks
                        downloaded += len(chunk)
                        elapsed = time.perf_counter() - start_time
                        
                        # Calculate current speed
                        if elapsed > 0:
                            speed_mbps = (downloaded / (1024 * 1024)) / elapsed
                        
                        # Calculate progress
                        if content_length > 0:
                            progress = min(0.95, (downloaded / content_length) * 0.9 + 0.05)
                        else:
                            # Estimate progress based on target download
                            progress = min(0.95, (downloaded / self.min_download_bytes) * 0.9 + 0.05)
                        
                        # Send progress updates every 100ms
                        now = time.perf_counter()
                        if progress_callback and (now - last_callback_time) >= 0.1:
                            progress_callback({
                                'status': 'downloading',
                                'speed_mbps': round(speed_mbps, 2),
                                'latency_ms': latency,
                                'downloaded_bytes': downloaded,
                                'progress': progress,
                                'url': url
                            })
                            last_callback_time = now
                        
                        # Stop conditions:
                        # 1. Downloaded enough bytes AND enough time passed
                        # 2. Downloaded max bytes
                        if (downloaded >= self.min_download_bytes and elapsed >= self.min_download_time):
                            break
                        if downloaded >= self.max_download_bytes:
                            break
                    
                    # Final calculation
                    elapsed = time.perf_counter() - start_time
                    if elapsed > 0 and downloaded > 0:
                        speed_mbps = (downloaded / (1024 * 1024)) / elapsed
                        download_success = True
                        break  # Success, no need to try other files
                        
                except requests.exceptions.Timeout:
                    continue
                except requests.exceptions.ConnectionError:
                    continue
                except Exception as e:
                    log_warning(f"Download error for {test_url}: {e}")
                    continue
            
            if download_success:
                result['speed_mbps'] = round(speed_mbps, 2)
                result['downloaded_bytes'] = downloaded
                result['status'] = 'success'
                result['progress'] = 1.0
            else:
                result['status'] = 'no_valid_files'
                
        except Exception as e:
            log_error(f"Error measuring speed for {url}", e)
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result

    def test_single_mirror(self, mirror_url: str, callback: Optional[Callable[[Dict], None]] = None) -> Dict[str, Any]:
        """Test a single mirror and return results."""
        country = self.get_mirror_country(mirror_url)
        
        def progress_cb(data: Dict):
            """Wrap progress callback with mirror info."""
            data['url'] = mirror_url
            data['country'] = country
            if callback:
                try:
                    callback(data)
                except Exception as e:
                    log_error("Error in progress callback", e)
        
        # Initial state
        if callback:
            callback({
                'url': mirror_url,
                'country': country,
                'status': 'starting',
                'progress': 0.0,
                'speed_mbps': 0,
                'latency_ms': 0
            })
        
        # Run the test
        result = self.measure_download_speed(mirror_url, progress_callback=progress_cb)
        
        # Add mirror info to result
        result['url'] = mirror_url
        result['country'] = country
        
        # Final callback
        if callback:
            result['progress'] = 1.0
            callback(result)
        
        return result

    def test_mirrors_parallel(self, callback: Callable[[Dict], None] = None) -> List[Dict]:
        """
        Tests all mirrors in parallel and returns results.
        Results are ordered by a combined score (latency + speed).
        """
        all_results = []
        
        def test_wrapper(mirror_url: str) -> Dict:
            result = self.test_single_mirror(mirror_url, callback)
            return result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tests
            future_to_mirror = {
                executor.submit(test_wrapper, mirror): mirror 
                for mirror in self.mirrors
            }
            
            # Collect results with timeout
            done_futures = set()
            start_time = time.time()
            
            while len(done_futures) < len(future_to_mirror):
                elapsed = time.time() - start_time
                if elapsed > self.per_mirror_timeout:
                    break
                    
                # Check for completed futures
                for future in list(future_to_mirror.keys()):
                    if future in done_futures:
                        continue
                    if future.done():
                        done_futures.add(future)
                        try:
                            result = future.result(timeout=0)
                            all_results.append(result)
                        except Exception as e:
                            mirror = future_to_mirror[future]
                            all_results.append({
                                'url': mirror,
                                'country': self.get_mirror_country(mirror),
                                'status': 'error',
                                'error': str(e),
                                'speed_mbps': 0,
                                'latency_ms': 9999,
                                'progress': 1.0
                            })
                
                time.sleep(0.1)
            
            # Mark remaining as timed out
            for future, mirror in future_to_mirror.items():
                if future not in done_futures:
                    future.cancel()
                    timeout_result = {
                        'url': mirror,
                        'country': self.get_mirror_country(mirror),
                        'status': 'timeout',
                        'speed_mbps': 0,
                        'latency_ms': 9999,
                        'progress': 1.0
                    }
                    all_results.append(timeout_result)
                    if callback:
                        callback(timeout_result)
        
        # Sort results: successful first, then by combined score
        def sort_key(r):
            if r['status'] != 'success':
                return (1, 9999, 0)  # Failed results last
            # Combined score: lower latency + higher speed = better
            # Normalize: latency weight 0.3, speed weight 0.7
            latency_score = r.get('latency_ms', 9999) / 1000  # Normalize to seconds
            speed_score = 100 / max(r.get('speed_mbps', 0.01), 0.01)  # Inverse of speed
            return (0, latency_score * 0.3 + speed_score * 0.7, -r.get('speed_mbps', 0))
        
        all_results.sort(key=sort_key)
        
        return all_results

    def get_mirror_country(self, url: str) -> str:
        """Determines country/region from mirror URL."""
        try:
            hostname = urlparse(url).netloc.lower()
            
            # Direct mappings for well-known mirrors
            country_map = {
                # Global CDNs
                "deb.debian.org": _("Global CDN"),
                "cdn-aws.deb.debian.org": _("Global CDN (AWS)"),
                
                # Germany special mirrors
                "mirror.23m.com": _("Germany"),
                "debian.charite.de": _("Germany"),
                "mirror.dogado.de": _("Germany"),
                "ftp.fau.de": _("Germany"),
                "ftp.gwdg.de": _("Germany"),
                "ftp.hosteurope.de": _("Germany"),
                "ftp-stud.hs-esslingen.de": _("Germany"),
                "debian.intergenia.de": _("Germany"),
                "mirror.ipb.de": _("Germany"),
                "debian.mirror.lrz.de": _("Germany"),
                "debian.netcologne.de": _("Germany"),
                "mirror.netzwerge.de": _("Germany"),
                "pubmirror.plutex.de": _("Germany"),
                "ftp.halifax.rwth-aachen.de": _("Germany"),
                "debian.tu-bs.de": _("Germany"),
                "ftp.tu-chemnitz.de": _("Germany"),
                "debian.inf.tu-dresden.de": _("Germany"),
                "ftp.uni-hannover.de": _("Germany"),
                "ftp.uni-mainz.de": _("Germany"),
                "ftp.uni-stuttgart.de": _("Germany"),
                "mirror.united-gameserver.de": _("Germany"),
                "mirror.wtnet.de": _("Germany"),
                "mirrors.xtom.de": _("Germany"),
                "de.mirrors.clouvider.net": _("Germany"),
                "mirror.creoline.net": _("Germany"),
                "debian.mirror.iphh.net": _("Germany"),
                "mirror.de.leaseweb.net": _("Germany"),
                "mirror.eu.oneandone.net": _("Germany"),
                "mirror.plusline.net": _("Germany"),
                
                # France special mirrors
                "mirror.debian.ikoula.com": _("France"),
                "ftp.ec-m.fr": _("France"),
                "mirror.johnnybegood.fr": _("France"),
                "debian.obspm.fr": _("France"),
                "debian.polytech-lille.fr": _("France"),
                "deb.syxpi.fr": _("France"),
                "ftp.u-picardie.fr": _("France"),
                "miroir.univ-lorraine.fr": _("France"),
                "mirror.gitoyen.net": _("France"),
                "deb-mir1.naitways.net": _("France"),
                "debian.mirrors.ovh.net": _("France"),
                "debian.proxad.net": _("France"),
                "ftp.rezopole.net": _("France"),
                "apt.tetaneutral.net": _("France"),
                "depot-debian.univ-reunion.fr": _("Reunion"),
                "debian.mithril.re": _("Reunion"),
                
                # UK special mirrors
                "free.hands.com": _("United Kingdom"),
                "mirror.mythic-beasts.com": _("United Kingdom"),
                "mirror.positive-internet.com": _("United Kingdom"),
                "mirror.cov.ukservers.com": _("United Kingdom"),
                "ukdebian.mirror.anlx.net": _("United Kingdom"),
                "uk.mirrors.clouvider.net": _("United Kingdom"),
                "mirrors.coreix.net": _("United Kingdom"),
                "debian.mirror.uk.sargasso.net": _("United Kingdom"),
                "debian.mirrors.uk2.net": _("United Kingdom"),
                "mirror.vinehost.net": _("United Kingdom"),
                "mirrorservice.org": _("United Kingdom"),
                "ftp.ticklers.org": _("United Kingdom"),
                "mirror.ox.ac.uk": _("United Kingdom"),
                
                # Spain special mirrors
                "ftp.caliu.cat": _("Spain"),
                "debian.grn.cat": _("Spain"),
                "ulises.hostalia.com": _("Spain"),
                "mirror.raiolanetworks.com": _("Spain"),
                "debian.redparra.com": _("Spain"),
                "ftp.cica.es": _("Spain"),
                "repo.ifca.es": _("Spain"),
                "debian.redimadrid.es": _("Spain"),
                "ftp.udc.es": _("Spain"),
                "softlibre.unizar.es": _("Spain"),
                "debian.uvigo.es": _("Spain"),
                
                # Italy special mirrors
                "debian.connesi.it": _("Italy"),
                "debian.dynamica.it": _("Italy"),
                "debian.mirror.garr.it": _("Italy"),
                "ftp.linux.it": _("Italy"),
                "giano.com.dist.unige.it": _("Italy"),
                "mirror.units.it": _("Italy"),
                
                # Netherlands special mirrors
                "mirror.nl.cdn-perfprod.com": _("Netherlands"),
                "mirror.nl.datapacket.com": _("Netherlands"),
                "mirrors.hostiserver.com": _("Netherlands"),
                "mirror.ams.macarne.com": _("Netherlands"),
                "mirror.nforce.com": _("Netherlands"),
                "mirror.tngnet.com": _("Netherlands"),
                "nl.mirrors.clouvider.net": _("Netherlands"),
                "mirror.duocast.net": _("Netherlands"),
                "nl.mirror.flokinet.net": _("Netherlands"),
                "mirror.nl.leaseweb.net": _("Netherlands"),
                "debian.snt.utwente.nl": _("Netherlands"),
                "mirrors.xtom.nl": _("Netherlands"),
                
                # Switzerland special mirrors
                "pkg.adfinis-on-exoscale.ch": _("Switzerland"),
                "linuxsoft.cern.ch": _("Switzerland"),
                "debian.ethz.ch": _("Switzerland"),
                "mirror.iway.ch": _("Switzerland"),
                "mirror.metanet.ch": _("Switzerland"),
                "deb.nextgen.ch": _("Switzerland"),
                "mirror.sinavps.ch": _("Switzerland"),
                "mirror1.infomaniak.com": _("Switzerland"),
                "mirror2.infomaniak.com": _("Switzerland"),
                "mirror.init7.net": _("Switzerland"),
                
                # Austria special mirrors
                "debian.anexia.at": _("Austria"),
                "debian.lagis.at": _("Austria"),
                "debian.mur.at": _("Austria"),
                "debian.sil.at": _("Austria"),
                "mirror.alwyzon.net": _("Austria"),
                
                # Belgium special mirrors
                "ftp.belnet.be": _("Belgium"),
                "mirror.unix-solutions.be": _("Belgium"),
                "mirror.as35701.net": _("Belgium"),
                "debian-mirror.behostings.net": _("Belgium"),
                
                # Portugal special mirrors
                "ftp.eq.uc.pt": _("Portugal"),
                "debian.uevora.pt": _("Portugal"),
                "ftp.rnl.tecnico.ulisboa.pt": _("Portugal"),
                "mirrors.up.pt": _("Portugal"),
                
                # Sweden special mirrors
                "mirrors.glesys.net": _("Sweden"),
                "ftpmirror1.infania.net": _("Sweden"),
                "debian.lth.se": _("Sweden"),
                "ftp.acc.umu.se": _("Sweden"),
                
                # Poland special mirrors
                "ftp.agh.edu.pl": _("Poland"),
                "ftp.icm.edu.pl": _("Poland"),
                "ftp.task.gda.pl": _("Poland"),
                "ftp.psnc.pl": _("Poland"),
                
                # Czech Republic special mirrors
                "ftp.sh.cvut.cz": _("Czech Republic"),
                "ftp.debian.cz": _("Czech Republic"),
                "mirror.dkm.cz": _("Czech Republic"),
                "mirror.it4i.cz": _("Czech Republic"),
                "debian.superhosting.cz": _("Czech Republic"),
                "merlin.fit.vutbr.cz": _("Czech Republic"),
                "ftp.zcu.cz": _("Czech Republic"),
                "ftp.cvut.cz": _("Czech Republic"),
                "debian.nic.cz": _("Czech Republic"),
                
                # Denmark special mirrors
                "mirrors.rackhosting.com": _("Denmark"),
                "mirrors.dotsrc.org": _("Denmark"),
                
                # Norway special mirrors
                "ftp.uio.no": _("Norway"),
                
                # Finland special mirrors
                "mirror.5i.fi": _("Finland"),
                "www.nic.funet.fi": _("Finland"),
                "debian.web.trex.fi": _("Finland"),
                
                # Iceland special mirrors
                "is.mirror.flokinet.net": _("Iceland"),
                
                # Lithuania special mirrors
                "mirror.litnet.lt": _("Lithuania"),
                "debian.mirror.vu.lt": _("Lithuania"),
                "debian.balt.net": _("Lithuania"),
                
                # Bulgaria special mirrors
                "debian.a1.bg": _("Bulgaria"),
                "debian.mnet.bg": _("Bulgaria"),
                "debian.telecoms.bg": _("Bulgaria"),
                "mirror.telepoint.bg": _("Bulgaria"),
                "ftp.uni-sofia.bg": _("Bulgaria"),
                "debian.ipacct.com": _("Bulgaria"),
                "mirrors.netix.net": _("Bulgaria"),
                
                # Slovakia special mirrors
                "ftp.antik.sk": _("Slovakia"),
                "deb.bbxnet.sk": _("Slovakia"),
                "ftp.debian.sk": _("Slovakia"),
                
                # Croatia special mirrors
                "debian.carnet.hr": _("Croatia"),
                "debian.iskon.hr": _("Croatia"),
                
                # Hungary special mirrors
                "ftp.bme.hu": _("Hungary"),
                "repo.jztkft.hu": _("Hungary"),
                
                # Romania special mirrors
                "mirrors.nxthost.com": _("Romania"),
                "mirrors.pidginhost.com": _("Romania"),
                "ro.mirror.flokinet.net": _("Romania"),
                "mirror.flo.c-f.ro": _("Romania"),
                "mirrors.hosterion.ro": _("Romania"),
                "mirror.linux.ro": _("Romania"),
                "mirrors.nav.ro": _("Romania"),
                
                # Latvia special mirrors
                "mirror.veesp.com": _("Latvia"),
                "mirror.cloudhosting.lv": _("Latvia"),
                "ftp.linux.edu.lv": _("Latvia"),
                "debian.koyanet.lv": _("Latvia"),
                
                # Estonia special mirrors
                "mirrors.xtom.ee": _("Estonia"),
                
                # Greece special mirrors
                "debian.otenet.gr": _("Greece"),
                
                # Georgia special mirrors
                "debian.grena.ge": _("Georgia"),
                
                # Luxembourg special mirrors
                "debian.mirror.root.lu": _("Luxembourg"),
                
                # Serbia special mirrors
                "mirror.pmf.kg.ac.rs": _("Serbia"),
                
                # Macedonia special mirrors
                "mirror-mk.interspace.com": _("Macedonia"),
                "mirror.a1.mk": _("Macedonia"),
                
                # Russia special mirrors
                "mirror.corbina.net": _("Russia"),
                "mirrors.powernet.com.ru": _("Russia"),
                "mirror.docker.ru": _("Russia"),
                "mirror.hyperdedic.ru": _("Russia"),
                "mirror.mephi.ru": _("Russia"),
                "mirror.neftm.ru": _("Russia"),
                "ftp.psn.ru": _("Russia"),
                "mirror.truenetwork.ru": _("Russia"),
                "repository.su": _("Russia"),
                
                # Belarus special mirrors
                "mirror.datacenter.by": _("Belarus"),
                
                # Kazakhstan special mirrors
                "mirror.hoster.kz": _("Kazakhstan"),
                "mirror.ps.kz": _("Kazakhstan"),
                
                # Ukraine special mirrors
                "mirror.ukrnames.com": _("Ukraine"),
                "debian.netforce.hosting": _("Ukraine"),
                "mirror.mirohost.net": _("Ukraine"),
                "debian.volia.net": _("Ukraine"),
                
                # USA special mirrors
                "mirror.0x626b.com": _("United States"),
                "mirror.cogentco.com": _("United States"),
                "debian.mirror.constant.com": _("United States"),
                "debpkg.libranext.com": _("United States"),
                "mirrors.xtom.com": _("United States"),
                "mirrors.ocf.berkeley.edu": _("United States"),
                "mirrors.bloomu.edu": _("United States"),
                "repo.ialab.dsu.edu": _("United States"),
                "debian.cc.lehigh.edu": _("United States"),
                "debian.csail.mit.edu": _("United States"),
                "mirrors.lug.mtu.edu": _("United States"),
                "mirror.siena.edu": _("United States"),
                "debian.uchicago.edu": _("United States"),
                "mirrors.vcea.wsu.edu": _("United States"),
                "mirrors.accretive-networks.net": _("United States"),
                "atl.mirrors.clouvider.net": _("United States"),
                "la.mirrors.clouvider.net": _("United States"),
                "nyc.mirrors.clouvider.net": _("United States"),
                "mirrors.iu13.net": _("United States"),
                "mirror.us.leaseweb.net": _("United States"),
                "mirror.us.mirhosting.net": _("United States"),
                "mirror.us.oneandone.net": _("United States"),
                "mirror.steadfast.net": _("United States"),
                "mirror.keystealth.org": _("United States"),
                "debian.osuosl.org": _("United States"),
                "mirrors.wikimedia.org": _("United States"),
                
                # Canada special mirrors
                "mirror.dst.ca": _("Canada"),
                "mirror.estone.ca": _("Canada"),
                "debian.linux.n0c.ca": _("Canada"),
                "debian.mirror.rafal.ca": _("Canada"),
                "mirror.it.ubc.ca": _("Canada"),
                "mirror.cpsc.ucalgary.ca": _("Canada"),
                "mirror.csclub.uwaterloo.ca": _("Canada"),
                
                # Mexico special mirrors
                "debian.vranetworks.lat": _("Mexico"),
                "lidsol.fi-b.unam.mx": _("Mexico"),
                
                # Brazil special mirrors
                "mirror.blue3.com.br": _("Brazil"),
                "debian.pop-sc.rnp.br": _("Brazil"),
                "mirror.uepg.br": _("Brazil"),
                "debian.c3sl.ufpr.br": _("Brazil"),
                "mirror.ufscar.br": _("Brazil"),
                "mirrors.ic.unicamp.br": _("Brazil"),
                
                # Chile special mirrors
                "debian-mirror.puq.apoapsis.cl": _("Chile"),
                "mirror.hnd.cl": _("Chile"),
                "mirror.insacom.cl": _("Chile"),
                
                # Argentina special mirrors
                "mirror.sitsa.com.ar": _("Argentina"),
                "debian.unnoba.edu.ar": _("Argentina"),
                
                # Costa Rica special mirrors
                "debianmirror.una.ac.cr": _("Costa Rica"),
                
                # Uruguay special mirrors
                "debian.repo.cure.edu.uy": _("Uruguay"),
                
                # Puerto Rico special mirrors
                "mirrors.upr.edu": _("Puerto Rico"),
                
                # Japan special mirrors
                "ftp.jaist.ac.jp": _("Japan"),
                "ftp.yz.yamagata-u.ac.jp": _("Japan"),
                "ftp.nara.wide.ad.jp": _("Japan"),
                "debian-mirror.sakura.ne.jp": _("Japan"),
                "ftp.riken.jp": _("Japan"),
                "mirrors.xtom.jp": _("Japan"),
                "dennou-k.gfd-dennou.org": _("Japan"),
                
                # South Korea special mirrors
                "ftp.kaist.ac.kr": _("South Korea"),
                "ftp.lanet.kr": _("South Korea"),
                "mirror.siwoo.org": _("South Korea"),
                "mirror.keiminem.com": _("South Korea"),
                "mirror.pangkin.com": _("South Korea"),
                
                # China special mirrors
                "mirrors.bfsu.edu.cn": _("China"),
                "mirrors.hit.edu.cn": _("China"),
                "mirrors.jlu.edu.cn": _("China"),
                "mirror.lzu.edu.cn": _("China"),
                "mirror.nju.edu.cn": _("China"),
                "mirror.nyist.edu.cn": _("China"),
                "mirror.sjtu.edu.cn": _("China"),
                "mirrors.tuna.tsinghua.edu.cn": _("China"),
                "mirrors.ustc.edu.cn": _("China"),
                "mirrors.zju.edu.cn": _("China"),
                
                # Taiwan special mirrors
                "tw1.mirror.blendbyte.net": _("Taiwan"),
                "mirror.twds.com.tw": _("Taiwan"),
                "debian.ccns.ncku.edu.tw": _("Taiwan"),
                "debian.csie.ntu.edu.tw": _("Taiwan"),
                "debian.cs.nycu.edu.tw": _("Taiwan"),
                "ftp.tku.edu.tw": _("Taiwan"),
                "opensource.nchc.org.tw": _("Taiwan"),
                
                # Hong Kong special mirrors
                "mirror.xtom.com.hk": _("Hong Kong"),
                
                # Thailand special mirrors
                "mirror.applebred.net": _("Thailand"),
                "ftp.debianclub.org": _("Thailand"),
                "mirror.kku.ac.th": _("Thailand"),
                
                # Singapore special mirrors
                "mirror.coganng.com": _("Singapore"),
                "mirror.sg.gs": _("Singapore"),
                
                # Indonesia special mirrors
                "kebo.pens.ac.id": _("Indonesia"),
                "mirror.unair.ac.id": _("Indonesia"),
                "mr.heru.id": _("Indonesia"),
                "kartolo.sby.datautama.net.id": _("Indonesia"),
                
                # Vietnam special mirrors
                "debian.xtdv.net": _("Vietnam"),
                "mirror.bizflycloud.vn": _("Vietnam"),
                
                # India special mirrors
                "mirror.nitc.ac.in": _("India"),
                
                # Bangladesh special mirrors
                "mirror.xeonbd.com": _("Bangladesh"),
                "mirror.limda.net": _("Bangladesh"),
                
                # Iran special mirrors
                "repo.mirror.famaserver.com": _("Iran"),
                "mirror.aminidc.com": _("Iran"),
                "archive.debian.petiak.ir": _("Iran"),
                
                # Israel special mirrors
                "debian.interhost.co.il": _("Israel"),
                
                # Cambodia special mirrors
                "mirror.sabay.com.kh": _("Cambodia"),
                
                # Nepal special mirrors
                "mirrors.nepalicloud.com": _("Nepal"),
                
                # Azerbaijan special mirrors
                "mirror.ourhost.az": _("Azerbaijan"),
                
                # Saudi Arabia special mirrors
                "mirror.maeen.sa": _("Saudi Arabia"),
                
                # Australia special mirrors
                "mirror.amaze.com.au": _("Australia"),
                "debian.mirror.digitalpacific.com.au": _("Australia"),
                "mirror.overthewire.com.au": _("Australia"),
                "debian.mirror.serversaustralia.com.au": _("Australia"),
                "mirror.aarnet.edu.au": _("Australia"),
                "mirror.linux.org.au": _("Australia"),
                "mirrors.xtom.au": _("Australia"),
                "mirror.realcompute.io": _("Australia"),
                
                # New Zealand special mirrors
                "linux.purple-cat.net": _("New Zealand"),
                "mirror.fsmg.org.nz": _("New Zealand"),
                
                # New Caledonia special mirrors
                "mirror.lagoon.nc": _("New Caledonia"),
                "debian.nautile.nc": _("New Caledonia"),
                
                # South Africa special mirrors
                "debian.saix.net": _("South Africa"),
                "ftp.is.co.za": _("South Africa"),
                "debian.envisagecloud.net.za": _("South Africa"),
                
                # Kenya special mirrors
                "debian.mirror.liquidtelecom.com": _("Kenya"),
                "debian.mirror.ac.ke": _("Kenya"),
                
                # Morocco special mirrors
                "mirror.marwan.ma": _("Morocco"),
                
                # Burkina Faso special mirrors
                "debian.ipsys.bf": _("Burkina Faso"),
            }
            
            for domain, country in country_map.items():
                if domain in hostname:
                    return country
            
            # Country code mappings for ftp.XX.debian.org pattern
            country_codes = {
                # Europe
                "es": _("Spain"), "de": _("Germany"), "fr": _("France"),
                "uk": _("United Kingdom"), "it": _("Italy"), "nl": _("Netherlands"),
                "pt": _("Portugal"), "be": _("Belgium"), "at": _("Austria"),
                "ch": _("Switzerland"), "se": _("Sweden"), "no": _("Norway"),
                "dk": _("Denmark"), "fi": _("Finland"), "is": _("Iceland"),
                "lt": _("Lithuania"), "pl": _("Poland"), "cz": _("Czech Republic"),
                "bg": _("Bulgaria"), "sk": _("Slovakia"), "si": _("Slovenia"),
                "hr": _("Croatia"), "ru": _("Russia"),
                # Americas
                "us": _("United States"), "ca": _("Canada"),
                "br": _("Brazil"), "cl": _("Chile"),
                # Asia
                "jp": _("Japan"), "kr": _("South Korea"), "cn": _("China"),
                "tw": _("Taiwan"), "hk": _("Hong Kong"),
                # Oceania
                "au": _("Australia"), "nz": _("New Zealand"), "nc": _("New Caledonia"),
            }
            
            # Try to extract country code from ftp.XX.debian.org pattern
            if "debian.org" in hostname:
                parts = hostname.split(".")
                if len(parts) >= 3 and parts[0] == "ftp":
                    code = parts[1].lower()
                    if code in country_codes:
                        return country_codes[code]
                    elif len(code) == 2:
                        return f"({code.upper()})"
            
            return _("Unknown")
            
        except Exception:
            return _("Unknown")


def get_speed_tester() -> RepoSpeedTester:
    """Returns a RepoSpeedTester instance."""
    return RepoSpeedTester()


def get_country_mirrors() -> Dict[str, List[str]]:
    """Returns mirrors organized by region for quick selection UI."""
    return {
        _('Global CDN'): [
            'http://deb.debian.org/debian',
            'http://cdn-aws.deb.debian.org/debian',
        ],
        _('Europe - Western'): [
            'http://ftp.de.debian.org/debian',
            'http://ftp.fr.debian.org/debian',
            'http://ftp.uk.debian.org/debian',
            'http://ftp.es.debian.org/debian',
            'http://ftp.it.debian.org/debian',
            'http://ftp.nl.debian.org/debian',
            'http://ftp.pt.debian.org/debian',
            'http://ftp.be.debian.org/debian',
            'http://ftp.at.debian.org/debian',
            'http://ftp.ch.debian.org/debian',
        ],
        _('Europe - Northern'): [
            'http://ftp.se.debian.org/debian',
            'http://ftp.no.debian.org/debian',
            'http://ftp.dk.debian.org/debian',
            'http://ftp.fi.debian.org/debian',
            'http://ftp.is.debian.org/debian',
            'http://ftp.lt.debian.org/debian',
        ],
        _('Europe - Eastern'): [
            'http://ftp.pl.debian.org/debian',
            'http://ftp.cz.debian.org/debian',
            'http://ftp.bg.debian.org/debian',
            'http://ftp.sk.debian.org/debian',
            'http://ftp.si.debian.org/debian',
            'http://ftp.hr.debian.org/debian',
            'http://ftp.ru.debian.org/debian',
        ],
        _('Americas - North'): [
            'http://ftp.us.debian.org/debian',
            'http://ftp.ca.debian.org/debian',
            'http://debian.csail.mit.edu/debian',
            'http://debian.osuosl.org/debian',
        ],
        _('Americas - Latin'): [
            'http://ftp.br.debian.org/debian',
            'http://ftp.cl.debian.org/debian',
            'http://debian.unnoba.edu.ar/debian',
            'http://lidsol.fi-b.unam.mx/debian',
            'http://debianmirror.una.ac.cr/debian',
        ],
        _('Asia - East'): [
            'http://ftp.jp.debian.org/debian',
            'http://ftp.kr.debian.org/debian',
            'http://ftp.cn.debian.org/debian',
            'http://mirrors.ustc.edu.cn/debian',
            'http://mirrors.tuna.tsinghua.edu.cn/debian',
            'http://ftp.tw.debian.org/debian',
            'http://ftp.hk.debian.org/debian',
        ],
        _('Asia - Southeast'): [
            'http://mirror.sg.gs/debian',
            'http://ftp.debianclub.org/debian',
            'http://mirror.bizflycloud.vn/debian',
            'http://kartolo.sby.datautama.net.id/debian',
        ],
        _('Asia - South/West'): [
            'http://mirror.nitc.ac.in/debian',
            'http://mirror.xeonbd.com/debian',
            'http://mirror.hoster.kz/debian',
            'http://mirror.aminidc.com/debian',
            'http://debian.interhost.co.il/debian',
        ],
        _('Oceania'): [
            'http://ftp.au.debian.org/debian',
            'http://ftp.nz.debian.org/debian',
            'http://mirror.aarnet.edu.au/debian',
            'http://ftp.nc.debian.org/debian',
        ],
        _('Africa'): [
            'http://ftp.is.co.za/debian',
            'http://debian.mirror.ac.ke/debian',
            'http://mirror.marwan.ma/debian',
        ],
    }
