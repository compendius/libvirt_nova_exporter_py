# Written by Charles Short
# 21/12/2020  - first draft
# A libvirt prometheus backend providing metrics for Openstack Nova instances
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
import sys
import time
import xml.etree.ElementTree as ET
import libvirt
import os
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import start_http_server, Summary
from prometheus_client import  MetricsHandler
import argparse
from urllib.parse import urlparse, parse_qs
import logging
from logging.handlers import RotatingFileHandler


## Promtheus custom collector https://github.com/prometheus/client_python

class CustomCollector(object):
    def collect(self):
        
        try:
          conn = libvirt.openReadOnly(luri)
        except Exception:
            logger.exception('error connecting to libvirt')
        try:
          domainID = conn.listDomainsID()
      
          if len(domainID) != 0:
             for domainID in domainID:
               domain = conn.lookupByID(domainID)
               t = getlibvirt(domain)
               d = GaugeMetricFamily('libvirt_nova_instance_memory_used_kb', 'instance memory used without buffers/cache', labels=['novaname','libvirtname','novaproject'])
               e = GaugeMetricFamily('libvirt_nova_instance_memory_cache_used_kb', 'instance memory used including buffers/cache', labels=['novaname','libvirtname','novaproject'])
               f = GaugeMetricFamily('libvirt_nova_instance_memory_alloc_kb', 'instance memory allocated', labels=['novaname','libvirtname','novaproject'])
               g = GaugeMetricFamily('libvirt_nova_instance_total_vcpu', 'intance vcpu allocated', labels=['novaname','libvirtname','novaproject'])
               c = CounterMetricFamily('libvirt_nova_instance_cpu_time_total', 'instance vcpu time', labels=['novaname','libvirtname','novaproject'])
               c.add_metric([str(t.novaname),str(t.libvirtname),str(t.novaproject)], t.vcput)
               d.add_metric([str(t.novaname),str(t.libvirtname),str(t.novaproject)], t.usednocache)
               e.add_metric([str(t.novaname),str(t.libvirtname),str(t.novaproject)], t.usedcache)
               f.add_metric([str(t.novaname),str(t.libvirtname),str(t.novaproject)], t.availm)
               g.add_metric([str(t.novaname),str(t.libvirtname),str(t.novaproject)], t.vcputot)
               yield c
               yield d
               yield e
               yield f
               yield g
        except Exception:
            logger.exception('error getting libvirt domains')
        conn.close()

## Need custom http handler top present custom endpoint of /metrics or user choice

class MetricsHandlerCustom(MetricsHandler):
    def do_GET(self):
        endpoint = urlparse(self.path).path
        if endpoint == lpath:
            return super(MetricsHandlerCustom, self).do_GET()
        else: 
            self.send_header("Content-type", "text/html")
            self.send_response(404)
            self.end_headers()


## Class for collected metrics

class MakeLibvirt: 
    def __init__(self,novaname,libvirtname,novaproject,availm,usednocache,usedcache,vcput,vcputot): 
        self.novaname = novaname
        self.libvirtname = libvirtname
        self.novaproject = novaproject
        self.availm = availm
        self.usedcache = usedcache
        self.usednocache = usednocache
        self.vcput = vcput 
        self.vcputot = vcputot

## Function to talk to libvirt and collect metrics 

def getlibvirt(domain):
 
    usedcache=0
    usednocache=0
## get cpu time    
    try: 
      cPut = domain.getCPUStats(True)
      listCPU = cPut[0]['cpu_time']
    except:
       logger.exception('error getting libvirt cpu stats')
  ## get total cpus
    try:
      vcputot = domain.maxVcpus()
    except:
       logger.exception('error getting libvirt maxcpu stats')
  ## get memory
    try:
      memi = domain.memoryStats()
      availm = memi.get("available")
      unusedm = memi.get("unused")
      usablem = memi.get("usable")
      if (availm is None):
          usedm = "0"
          availm = "0"
          usablem = "0"
      else:
          usedcache = (availm - unusedm)
          usednocache = (availm - usablem)
    except:
       logger.exception('error getting libvirt memory stats')
      
## Parse xml to get nova information
    
    ns = {'oa': 'http://openstack.org/xmlns/libvirt/nova/1.0'}
    try:
      tree = ET.fromstring(domain.XMLDesc())
      libvirt_name = str(tree.find('name').text)
      libvirt_uuid = str(tree.find('uuid').text)
      
      for tree1 in tree.findall('metadata'):
          for char in tree1.findall('oa:instance', ns):
              nova_name = str(char.find('oa:name', ns).text)
              for char1 in char.findall('oa:owner', ns):
                  nova_project = str(char1.find('oa:project', ns).text)
    except:
       logger.exception('error getting libvirt xml dump')
    

    return MakeLibvirt(nova_name,libvirt_name,nova_project,availm,usednocache,usedcache,listCPU,vcputot)

if __name__ == '__main__':
## Grab command line options

    parser = argparse.ArgumentParser(description='Arguments for Openstack Nove prometheus exporter')

    parser.add_argument("--uri", default="qemu:///system", type=str, help="url for libvirt connection")
    parser.add_argument("--path", default="/metrics",  type=str, help="Scrape path")
    parser.add_argument("--port", default="9100", type=int, help="Scrape port")
    parser.add_argument("--log", default="./libvirt_nova.log", type=str, help="log file path")

    args = parser.parse_args()
    luri=args.uri
    lpath=args.path
    lport=args.port
    llog=args.log

## set up logging

    logger = logging.getLogger('libvirt nova exporter logger')

    fh = RotatingFileHandler(llog, maxBytes=3000000, backupCount=4)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.setLevel(logging.ERROR)

    # Start up the webserver to expose the metrics.

    serv_addr = ('', lport)
    REGISTRY.register(CustomCollector())
    HTTPServer(serv_addr, MetricsHandlerCustom).serve_forever()
