# Computer Networks Spring 2015
# Programming assignment 1
# Roberto Amorim - rja2139

import argparse
import socket
import time
from threading import Thread

# Configuration variables
BUFSIZE = 1024


# Here I take care of the command line arguments
parser = argparse.ArgumentParser(description='This is the messaging client', add_help=True)
parser.add_argument('--server', dest = 'ip', required = True, help = 'Server IP Address')
parser.add_argument('--port', dest = 'port', required = True, help='Server Port')
args = parser.parse_args()

# Here I validate the IP address
try:
    socket.inet_aton(args.ip)
except socket.error:
    print "ERROR: The IP address you provided (" + args.serverIP + ") doesn't seem to be valid!"
    exit(1)

# Here I validate the server port
if args.port.isdigit():
    port = int(args.port)
    if port > 65535:
        print "ERROR: The port number is outside the acceptable range! (0-65535)"
        exit(1)
else:
    print "ERROR: The server port must be a number!"
    exit (1)

## we have the required info, now let's authenticate with the server
while True:
    user = raw_input('Username: ')
    pwd = raw_input('Password: ')
    message = "AUTH " + user + " " + pwd
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((args.ip, port))
    except:
        print "Error connecting to the remote server. Is it running? Are the IP and port you provided correct?"
        exit(1)
    client.send(message)
    resp = client.recv(BUFSIZE)
    if resp == "AUOK":
        print "Welcome to simple chat server!"
        client.close()
        break
    elif resp == "ANOK":
        print "Invalid password. Please try again"
        client.close()
    elif resp == "ABLK":
        print "Too many authentication failures. You have been blocked. Try again after some time"
        client.close()
        exit(1)


def private(data):
    print "Placeholder: " + data


def send(data):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((args.ip, port))
        client.send(data)
    except:
        print "Error connecting to the remote server. Guess it went offline"
        exit(1)
    client.close()


def serverthread(serversock):
    message = serversock.recv(BUFSIZE)
    print("> " + message + " <\n> "),


def server():
    clientserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # listen on TCP/IP socket
    clientserv.bind(("localhost", 2663))                 # serve clients in threads
    clientserv.listen(5)
    while True:
        serversock, serveraddr = clientserv.accept()
        servthread = Thread(target=serverthread, args=(serversock,))
        servthread.start()
clientservthread = Thread(target=server)
clientservthread.start()


def heartbeat():
    while True:
        time.sleep(45)
        send("LIVE")
heartbeatthread = Thread(target=heartbeat)
heartbeatthread.start()

while True:
    text = raw_input('> ')
    text = text.lstrip()
    command = text.split(' ', 1)

    if command[0] == "message":
        send("MESG " + command[1])
    elif command[0] == "broadcast":
        send("BCST " + command[1])
    elif command[0] == "online":
        send("ONLN")
    elif command[0] == "block":
        send("BLCK " + command[1])
    elif command[0] == "unblock":
        send("UNBL " + command[1])
    elif command[0] == "logout":
        send("LOGT")
        exit(0)
    elif command[0] == "getaddress":
        send("GETA " + command[1])
    elif command[0] == "private":
        private(command[1])
    elif not command[0]:
        continue
    else:
        print "I could not understand the command you gave me. Valid commands are:"
        print "message, broadcast, online, (un)block, logout, getaddress, private"


