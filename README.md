# Libvirt Nova Exporter

Prometheus libvirt exporter for Openstack Nova instances
This is an alternative to the exported I have alrady written in Go here [https://github.com/compendius/libvirt_nova_exporter](https://github.com/compendius/libvirt_nova_exporter)

### What is this?

This is some code I have written in Python that aims to export a very small subset of metrics from libvirt for Openstack Nova instances.
The principal is to get real time usage information, for example how many vcpus are in use.


### Run

For testing you can run as below

```python libvirt_nova.py --port 9200 --log /var/log/libvirt_nova.log &```


Options - 

 * ```--uri``` the libvirt URI to connect to -  default - ```qemu:///system```
 * ```--path``` the scrape target path  - default - ```/metrics```
 * ```--port``` port to listen on  - default - ```9100```
 * ```--log``` log file path  - default - working directory

### Code Mechanics

The code acts as a proxy to collect metrics from libvirt. It creates a custom collector for this purpose using 
[https://github.com/prometheus/client_python](https://github.com/prometheus/client_python) as a guide. It also uses a custom endpoint
 and so makes use of the MetricsHandler class which provides a BaseHTTPRequestHandler.
Each API call for each metric has error trapping which should appear in the log file.
Log files over 3MB will be rotated.
When an instance is removed from Nova (and therefore libvirt) the custom Collector removes the related metric for that instance.

### Metrics

```
# HELP libvirt_nova_instance_cpu_time_total instance vcpu time
# TYPE libvirt_nova_instance_cpu_time_total counter
libvirt_nova_instance_cpu_time_total{libvirtname="instance-0000030f",novaname="cems-testing-0",novaproject="admin"} 2.57646967433e+12
# HELP libvirt_nova_instance_memory_alloc_kb instance memory allocated
# TYPE libvirt_nova_instance_memory_alloc_kb gauge
libvirt_nova_instance_memory_alloc_kb{libvirtname="instance-0000030f",novaname="cems-testing-0",novaproject="admin"} 489084
# HELP libvirt_nova_instance_memory_cache_used_kb instance memory used including buffers/cache
# TYPE libvirt_nova_instance_memory_cache_used_kb gauge
libvirt_nova_instance_memory_cache_used_kb{libvirtname="instance-0000030f",novaname="cems-testing-0",novaproject="admin"} 48980
# HELP libvirt_nova_instance_memory_used_kb instance memory used without buffers/cache
# TYPE libvirt_nova_instance_memory_used_kb gauge
libvirt_nova_instance_memory_used_kb{libvirtname="instance-0000030f",novaname="cems-testing-0",novaproject="admin"} 29436
# HELP libvirt_nova_instance_vcpu_count instance vcpu allocated
# TYPE libvirt_nova_instance_vcpu_count gauge
libvirt_nova_instance_vcpu_count{libvirtname="instance-0000030f",novaname="cems-testing-0",novaproject="admin"} 1
```

### PromQL examples
#### How many vCPUs in use


```irate(libvirt_nova_instance_cpu_time_total{novaname=~"testing.*"}[30s])/1e+9```

Note that the ```scrape interval``` is 15s in this case defined in the Prometheus server config file,  
so here irate is effectively calculating the delta between two 15 second cpu time scrapes which should give you the vCPUs in use

[https://prometheus.io/docs/prometheus/latest/querying/functions/](https://prometheus.io/docs/prometheus/latest/querying/functions/)

"irate()
irate(v range-vector) calculates the per-second instant rate of increase of the time series in the range vector. This is based on the last two data points"


