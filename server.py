# Computer Networks Spring 2015
# Programming assignment 1
# Roberto Amorim - rja2139

import argparse
import socket
import time
from threading import Thread

# Configuration variables
TIMEOUT = 60  # 1 minute
BUFSIZE = 1024
BLOCK_TIME = 600  # 10 minutes
BLOCKED = []
ONLINE = []


# Here I take care of the command line arguments
parser = argparse.ArgumentParser(description='This is the Message Center', add_help=True)
parser.add_argument('--port', dest = 'port', required = True, help='Port to listen for incoming connections')
args = parser.parse_args()

# Here I validate the port
if args.port.isdigit():
    port = int(args.port)
    if port > 65535:
        print "ERROR: The port number is outside the acceptable range! (0-65535)"
        exit(1)
else:
    print "ERROR: The port must be a number!"
    exit(1)


# Checks if a client asking to authenticate is blocked.
# Returns the amount of times it failed logging in the last BLOCK_TIME seconds
def isblocked(clientaddr):
    count = 0
    for i in BLOCKED:
        if i[0] == clientaddr[0]:
            # If the time stored is bigger than (current time minus BLOCK_TIME), that block entry is still valid
            if i[1] >= (time.time() - BLOCK_TIME):
                count += 1
            # Since new items in the list are prepended and not appended, we can be sure the first match was the last
            # failed login. If the last failed login happened more than BLOCK_TIME ago, it doesn't matter anymore
            else:
                BLOCKED.pop(BLOCKED.index(i))
    return count


def auth(clientsock, clientaddr, data):
    values = data.split(' ', 1)
    # First we check if that IP requesting to authenticate is not blocked
    tries = isblocked(clientaddr)
    if tries > 2:
        clientsock.send("ABLK")
        return 0
    try:
        for line in open('credentials.txt','r').readlines():
            line = line.rstrip()
            entry = line.split(' ')
            if entry[0] == values[0]:
                if entry[1] == values[1]:
                    print "User authenticated!"
                    clientsock.send("AUOK")
                    ONLINE.append([clientaddr[0],entry[0],int(time.time())])
                    print ONLINE
                    return 0
        # If the code arrived here, means authentication failed
        if tries < 2:
            print "Wrong password!"
            clientsock.send("ANOK")
            BLOCKED.insert(0,[clientaddr[0],int(time.time())])
        else:
            print "Wrong password - Blocked!"
            clientsock.send("ABLK")
            BLOCKED.insert(0,[clientaddr[0],int(time.time())])
    except IOError:
        print "Credentials file can not be read! Something is very wrong. Exiting..."
        exit (1)


def heartbeat(clientaddr):
    for i in ONLINE:
        if i[0] == clientaddr[0]:
            i[2] = int(time.time())


def serverthread(clientsock, clientaddr):
    receive = clientsock.recv(BUFSIZE)
    command = receive.split(' ', 1)
    if command[0] == "AUTH":
        auth(clientsock, clientaddr, command[1])
    elif command[0] == "LIVE":
        heartbeat(clientaddr)
    elif command[0] == "MESG":
        print "bogus"
        #message(clientaddr, command[1])
    elif command[0] == "BCST":
        print "bogus"
        #broadcast(clientaddr, command[1])
    elif command[0] == "ONLN":
        print "bogus"
        #online(clientaddr)
    elif command[0] == "BLCK":
        print "bogus"
        #block(clientaddr, command[1])
    elif command[0] == "UNBL":
        print "bogus"
        #unblock(clientaddr, command[1])
    elif command[0] == "LOGT":
        print "bogus"
        #logout(clientaddr)
    elif command[0] == "GETA":
        print "bogus"
        #getaddress(clientaddr, command[1])


def server():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # listen on TCP/IP socket
    serversocket.bind(("localhost", port))                 # serve clients in threads
    serversocket.listen(5)
    while True:
        clientsock, clientaddr = serversocket.accept()
        clientthread = Thread(target=serverthread, args=(clientsock, clientaddr))
        clientthread.start()

clientservthread = Thread(target=server, args=())
clientservthread.start()
