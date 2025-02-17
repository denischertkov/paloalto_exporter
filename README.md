# Palo Alto IPsec Exporter 
Prometheus exporter for actual Palo Alto firewall IPSEC tunnel state, written in Python.

## Description
As is well known, in Palo Alto firewalls it is not possible to get the actual status of an IPSEC tunnel using SNMP: even if the tunnel is set to down on the other side and the tunnel is not established, but the administrative status is UP, SNMP will return the UP status.
From the CLI with "show vpn flow" command we can see the actual picture:

```
user@PA-PRI(active)> show vpn flow

total tunnels configured:                                     7
filter - type IPSec, state any

total IPSec tunnel configured:                                6
total IPSec tunnel shown:                                     6

id    name                                                            state   monitor local-ip                      peer-ip                       tunnel-i/f
--    --------------                                                  -----   ------- --------                      -------                       ----------  
2     IPSEC-XXX-BANK                                                  inactiv off     234.64.49.14                 XXX.XX.XX.XX                   tunnel.3
3     IPSEC-XXXXXX                                                    active  off     234.64.49.14                 XXX.XX.XX.XX                   tunnel.4
4     IPSEC-XXXXXX                                                    active  off     234.64.49.14                 XXX.XX.XX.XX                   tunnel.5
5     IPSEC-XXXXXX                                                    inactiv off     234.64.49.14                 XXX.XX.XX.XX                   tunnel.6
```

By parsing the output of this command we can get the following details for each IPSec tunnel:
"ifAlias","ifDescr", "ifIndex" and "ifName".

## Functionality
The Palo Alto IPSec exporter is determining the state of the configured IPSec tunnels via the following procedure.
1. Starting up the OS envs PE_USERNAME, PE_PASSWORD, PE_HOSTNAME and PE_HTTP_SERVER_PORT is read, therefore, they must be explicitly specified before launching. 
1. If the `/metrics` endpoint is queried, the exporter connect via SSH to the Palo Alto appliance and run `show vpn flow`. The output is parsed.
    * If the state output contains `active`, we assume that the tunnel is up and running.
    * If the state output contains `inactiv`, we assume that the tunnel is down.
    * in other cases we assume that tunnel is in an unknown state.

## Value Definition
| Metric | Value | Description |
|--------|-------|-------------|
| ifIPsecOperStatus | 1 | The connection is established and tunnel is installed. The tunnel is up and running. |
| ifIPsecOperStatus | 2 | The tunnel is not up or down. |
| ifIPsecOperStatus | 3 | The tunnel is in an unknown state. |

## How to use
Python3 and pip should be installed on your system!

Clone the current git repo: 
```
git clone git@github.com:denischertkov/paloalto_exporter.git
```
Copy file to the /opt/monitoring/pa_ipsec/ folder:
```
sudo mkdir /opt/monitoring/pa_ipsec/
sudo cp ./pa_ipsec_status.py /opt/monitoring/pa_ipsec/
```
Install the required libraries:
```
pip install -r requirements.txt
```
The OS envs PE_USERNAME, PE_PASSWORD, PE_HOSTNAME and PE_HTTP_SERVER_PORT must be explicitly specified before launching:
```
PE_USERNAME="monitoring_user" PE_PASSWORD="SECRET_PASSWORD" PE_HOSTNAME="10.10.10.240" PE_HTTP_SERVER_PORT=9098 python3 /opt/monitoring/pa_ipsec/pa_ipsec_status.py
```
If you want to run the exporter as a systemd service, you need to create the systemd service file pa_ipsec.service with the following contents:
```
[Unit]
Description=pa_ipsec
After=network.target

[Service]
Environment=PE_USERNAME="monitoring_user" PE_PASSWORD="SECRET_PASSWORD" PE_HOSTNAME="10.10.10.240" PE_HTTP_SERVER_PORT=9098
ExecStart=/bin/python3 /opt/monitoring/pa_ipsec/pa_ipsec_status.py
Restart=always
RestartSec=3
StartLimitBurst=5
StartLimitInterval=30s

[Install]
WantedBy=multi-user.target
```
Now you can test the exporter:
```
$curl localhost:9098/metrics

# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 4413.0
```
[OUTPUT CUTTED]
```
# HELP ifIPSECOperStatus The current operational state of the interface - 1.3.6.1.2.1.2.2.1.8
# TYPE ifIPSECOperStatus gauge
ifIPSECOperStatus{ifAlias="IPSEC-TUN1",ifDescr="tunnel.3",ifIndex="2",ifName="tunnel.3"} 2.0
ifIPSECOperStatus{ifAlias="IPSEC-TUN2",ifDescr="tunnel.4",ifIndex="3",ifName="tunnel.4"} 1.0
ifIPSECOperStatus{ifAlias="IPSEC-TUN3",ifDescr="tunnel.5",ifIndex="4",ifName="tunnel.5"} 1.0
ifIPSECOperStatus{ifAlias="IPSEC-TUN4",ifDescr="tunnel.6",ifIndex="5",ifName="tunnel.6"} 2.0
```
The last strings will show you metrics for all IPSEC tunnels.
Now we can add the metrics to the prometheus: you need  to add new section to the `prometheus.yml` file:
```
  - job_name: paloalto-a.dc01
    scrape_interval: 30s
    static_configs:
    - targets: 
      - XXX.XXX.XXX.XXX:9098      # <- host IP or FQDN where Palo Alto IPSEC exporter is running
```
And restart the Prometheus. Now we will see the target and metrics on the Prometheus WebUI: Query -> add "ifIPSECOperStatus{job="paloalto-a.dc01"}" -> Execute:
```
ifIPSECOperStatus{ifAlias="IPSEC-TUN1", ifDescr="tunnel.3", ifIndex="2", ifName="tunnel.3", instance="XXXXX", job="paloalto-a.dc01"}	2
ifIPSECOperStatus{ifAlias="IPSEC-TUN2", ifDescr="tunnel.4", ifIndex="3", ifName="tunnel.4", instance="XXXXX", job="paloalto-a.dc01"}	1
ifIPSECOperStatus{ifAlias="IPSEC-TUN3", ifDescr="tunnel.5", ifIndex="4", ifName="tunnel.5", instance="XXXXX", job="paloalto-a.dc01"}	1
ifIPSECOperStatus{ifAlias="IPSEC-TUN4", ifDescr="tunnel.6", ifIndex="5", ifName="tunnel.6", instance="XXXXX", job="paloalto-a.dc01"}	2
```
And now the best tume to add the new panel wit alerts to the Grafana.

Denis Chertkov, denis@chertkov.info, 20250217