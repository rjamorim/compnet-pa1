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
BLOCKED = []  # IPs blocked for too many authentication failures
ONLINE = []  # List of connected clients
BLACKLIST = []  # List of clients that blocked other clients


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


# Converts an IP address into an user name, as long as both are in the ONLINE list
def iptoname(clientaddr):
    for entry in ONLINE:
        if entry[0] == clientaddr[0]:
            return entry[1]
    return "oops"


# The opposite
def nametoip(name):
    for entry in ONLINE:
        if entry[1] == name:
            return entry[0]


# Checks if an user is valid - that is, he is in the credentials file
def validateuser(name):
    try:
        for line in open('credentials.txt','r').readlines():
            entry = line.split(' ')
            if entry[0] == name:
                return True
        return False
    except IOError:
        print "Credentials file can not be read! Something is very wrong. Exiting..."
        exit (1)


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
                    ### HERE WE MUST RETRIEVE MESSAGES THAT WERE LEFT OFFLINE AND SEND THEM TO USER
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


def send(clientaddr, data):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((clientaddr[0], 2663))
        client.send(data)
    except:
        print "Error connecting to the remote server. Guess it went offline"
        exit(1)
    client.close()


def heartbeat(clientaddr):
    for entry in ONLINE:
        if entry[0] == clientaddr[0]:
            entry[2] = int(time.time())


# Routine for an user to block another user
def block(clientaddr, data):
    client = iptoname(clientaddr)
    if client == data:
        send(clientaddr, "ERROR: Are you really trying to block yourself??")
        return 0
    if validateuser(data):
        for entry in BLACKLIST:
            if entry[0] == client:
                if entry[1] == data:
                    send(clientaddr, "ERROR: You are already blocking that user")
                    return 0
    else:
        send(clientaddr, "ERROR: you are trying to block an user that doesn't exist")
        return 0
    BLACKLIST.append([client,data])
    send(clientaddr, "You successfully blocked user " + data)


# Routine for an user to unblock another user
def unblock(clientaddr, data):
    client = iptoname(clientaddr)
    for entry in BLACKLIST:
        if entry[0] == client:
            if entry[1] == data:
                BLACKLIST.pop(BLACKLIST.index([client,data]))
                send(clientaddr, "You successfully unblocked user " + data)
                return 0
    send(clientaddr, "ERROR: you are not blocking user " + data)


# Checks if the addressee is blocking the sender
def isblocking(clientaddr, addressee):
    sender = iptoname(clientaddr)
    for entry in BLACKLIST:
        if entry[0] == addressee:
            if entry[1] == sender:
                return True
    return False


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
        block(clientaddr, command[1])
    elif command[0] == "UNBL":
        unblock(clientaddr, command[1])
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
