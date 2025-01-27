#!/usr/bin/python3
import paramiko
import time
import os
import sys

#USERNAME = sys.argv[1]
#HOSTNAME = sys.argv[2]
#PASSWORD = os.environ.get('PASSWORD')
USERNAME = "denis"
HOSTNAME = "10.210.254.240"
PASSWORD = "oZ4fY4jN1p@G4"
PORT = 22

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

#    print(list(ipsec_list));

    # output collected data in prometheuse format
    # ifOperStatus{ifAlias="APM_EXTERNAL VLAN",ifDescr="ae1.13",ifIndex="500010013",ifName="ae1.13"} 1
    print('# HELP ifOperStatus The current operational state of the interface - 1.3.6.1.2.1.2.2.1.8');
    print('# TYPE ifOperStatus gauge');
    for tunnel in ipsec_list:
        print('ifOperStatus{ifAlias="',tunnel[1],'",ifDescr="',tunnel[6],'",ifIndex="',tunnel[0],'",ifName="',tunnel[6],'"}', sep="", end=' ');
        if (tunnel[2]=='active'):
            print('1', sep="");
        elif (tunnel[2]=='inactiv'):
            print('2', sep="");
        else:
            print('3', sep="");

if __name__ == '__main__':
    get_config()
