# This is a prometheus compatibe exporter for the Palo Alto IPSEC tunnel state
# This exporter returned state of the IPSEC tunnels:
# 1 - active (established)
# 2 - inactive
# 3 - other state
#
# Denis Cehrtkov, denis@chertkov.info, 20250208

from prometheus_client import start_http_server, Gauge
import time
import paramiko
import time
import os

USERNAME = "denis"
PASSWORD = os.environ.get('PASSWORD')
HOSTNAME = os.environ.get('HOSTNAME')
HTTP_SERVER_PORT = int(os.environ.get('HTTP_SERVER_PORT'))
PORT = 22

IPSEC_Status_gauge = Gauge('ifIPSECOperStatus','The current operational state of the interface - 1.3.6.1.2.1.2.2.1.8',
                                    ["ifAlias","ifDescr", "ifIndex", "ifName",   ])

def send_get_output(chan, command):
    chan.send(command + '\n')
    buff = ''
    while not (buff.endswith('> ') or buff.endswith('# ')):
        time.sleep(1)
        resp = chan.recv(9999)
        if len(resp) == 0:
            break
        buff += str(resp, 'UTF-8')

    return buff;

def get_config(username=USERNAME, password=PASSWORD, hostname=HOSTNAME, port=PORT):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(hostname, port, username, password)
    chan = client.invoke_shell()
    send_get_output(chan, 'set cli pager off')
    status=send_get_output(chan, 'show vpn flow')                               # get the IPSEC tunnels status output
    send_get_output(chan, 'exit')
    client.close()

    # show vpn flow command output parsing
    ipsec_list=[]
    flag = False;
    for line in status.split('\r\n'):
        if (flag == True):
            if len(line)>3:
#                print(line);
                ipsec_list.append(line.split());
            else:
                break;
        if line.startswith('--    --------------'):
            flag = True;

    # output collected data in prometheuse format
#    print('# HELP ifIPSECOperStatus The current operational state of the interface - 1.3.6.1.2.1.2.2.1.8');
#    print('# TYPE ifIPSECOperStatus gauge');
    for tunnel in ipsec_list:
#        print('ifIPSECOperStatus{ifAlias="',tunnel[1],'",ifDescr="',tunnel[6],'",ifIndex="',tunnel[0],'",ifName="',tunnel[6],'"}', sep="", end=' ');
        if (tunnel[2]=='active'):
#            print('1', sep="");
            ifStatus=1;
        elif (tunnel[2]=='inactiv'):
#            print('2', sep="");
            ifStatus=2;
        else:
#            print('3', sep="");
            ifStatus=3;

        IPSEC_Status_gauge.labels(ifAlias=tunnel[1],
                                  ifDescr=tunnel[6],
                                  ifIndex=tunnel[0],
                                  ifName=tunnel[6]
                                  ).set(ifStatus);

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(HTTP_SERVER_PORT)
    print("Exporter running at http://localhost:", HTTP_SERVER_PORT, sep="")

    # Refresh the metrics every 30 seconds
    while True:
        get_config()
        time.sleep(30)
