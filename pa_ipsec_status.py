# This is a Prometheus compatibe exporter for the Palo Alto IPSec tunnel state
# This exporter returned ifIPSECOperStatus of the IPSec tunnels:
# 1 - active (established)
# 2 - inactive
# 3 - other state
# The "ifAlias", "ifDescr", "ifIndex" and "ifName" fields are supported
#
# ver 1.3.2
# Denis Chertkov, denis@chertkov.info, 20250217

import paramiko
import time
import os
from prometheus_client import start_http_server, Gauge

USERNAME = os.environ.get('PE_USERNAME')
PASSWORD = os.environ.get('PE_PASSWORD')
HOSTNAME = os.environ.get('PE_HOSTNAME')
HTTP_SERVER_PORT = os.environ.get('PE_HTTP_SERVER_PORT')
PORT = 22

IPSEC_Status_gauge = Gauge('ifIPSECOperStatus',
                           'The current operational state of the interface - 1.3.6.1.2.1.2.2.1.8',
                           ["ifAlias", "ifDescr", "ifIndex", "ifName"])


def send_get_output(chan, command):
    chan.send(command + '\n')
    buff = ''
    while not (buff.endswith('> ') or buff.endswith('# ')):
        time.sleep(1)
        resp = chan.recv(9999)
        if len(resp) == 0:
            break
        buff += str(resp, 'UTF-8')

    return buff


def get_config(username=USERNAME, password=PASSWORD, hostname=HOSTNAME, port=PORT):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(hostname, port, username, password)
    chan = client.invoke_shell()
    send_get_output(chan, 'set cli pager off')
    status = send_get_output(chan, 'show vpn flow')                               # get the IPSEC tunnels status output
    send_get_output(chan, 'exit')
    client.close()

    # "show vpn flow" command output parsing
    ipsec_list = []
    flag = False
    for line in status.split('\r\n'):
        if flag is True:
            if len(line) > 3:
                ipsec_list.append(line.split())                                 # parse values for ifAlias, ifDescr, ifIndex and ifName
            else:
                break
        if line.startswith('--    --------------'):
            flag = True

    # parse the tunnel state
    for tunnel in ipsec_list:
        if (tunnel[2] == 'active'):
            ifStatus = 1
        elif (tunnel[2] == 'inactiv'):
            ifStatus = 2
        else:
            ifStatus = 3

        IPSEC_Status_gauge.labels(ifAlias=tunnel[1],
                                  ifDescr=tunnel[6],
                                  ifIndex=tunnel[0],
                                  ifName=tunnel[6]
                                  ).set(ifStatus)


if __name__ == '__main__':
    if None in [USERNAME, PASSWORD, HOSTNAME, HTTP_SERVER_PORT]:
        print("ERROR: Not all necessary environment variables are defined!")
        print("The environment variables USERNAME, PASSWORD, HOSTNAME and HTTP_SERVER_PORT must be defined.")
    else:
        # Start up the server to expose the metrics.
        start_http_server(int(HTTP_SERVER_PORT))
        print("PA IPSEC exporter running at http://localhost:", HTTP_SERVER_PORT, sep="")

        # Refresh the metrics every 30 seconds
        while True:
            get_config()
            time.sleep(30)
