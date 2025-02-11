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
6     IPSEC-XXXXXXX-BANK                                              active  off     234.64.49.14                 XXX.XX.XX.XX                   tunnel.7
7     IPSEC-XXXX-BANK                                                 active  off     234.64.49.14                 XXX.XX.XX.XX                   tunnel.8
```

By unparsing the output of this command we can get the following details for each IPSec tunnel:
"ifAlias","ifDescr", "ifIndex" and "ifName".

## Functionality
The Palo Alto IPSec exporter is determining the state of the configured IPSec tunnels via the following procedure.
1. Starting up the OS envs USERNAME, PASSWORD, HOSTNAME and HTTP_SERVER_PORT is read. 
1. If the `/metrics` endpoint is queried, the exporter connect via SSH to the Palo Alto appliance and run `show vpn flow`. The output is parsed.
    * If the state output contains `active`, we assume that the tunnel is up and running.
    * If the state output contains `inactiv`, we assume that the tunnel is down.
    * in other cases we assume that tunnel is in an unknown state.

## Value Definition
| Metric | Value | Description |
|--------|-------|-------------|
| ifIPsecOperStatus | 1 | The connection is established and tunnel is installed. The tunnel is up and running. |
| ifIPsecOperStatus | 2 | The connection is established, but the tunnel is not up or down. |
| ifIPsecOperStatus | 3 | The tunnel is in an unknown state. |



Denis Chertkov, denis@chertkov.info, 20250210