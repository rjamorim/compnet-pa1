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
OUTBOX = []  # Messages waiting for their owners to connect, so that they can be delivered


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


# Checks if an user is online
def isonline(name):
    for entry in ONLINE:
        if entry[1] == name:
            return True
    return False


# Checks if an user is valid - that is, he is in the credentials file
def isvaliduser(name):
    try:
        for line in open('credentials.txt','r').readlines():
            entry = line.split(' ')
            if entry[0] == name:
                return True
        return False
    except IOError:
        print "Credentials file can not be read! Something is very wrong. Exiting..."
        exit (1)


# Here we check the outbox to see of the user that just logged doesn't have any messages waiting
def processoutbox(name):
    addressee = (nametoip(name),2663)
    flag = False
    for entry in OUTBOX:
        if entry[0] == name:
            flag = True
            send(addressee, entry[1])
    if flag:
        for entry in OUTBOX:
            if entry[0] == name:
                OUTBOX.pop(OUTBOX.index(entry))


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
                    clientsock.send("AUOK")
                    ONLINE.append([clientaddr[0],entry[0],int(time.time())])
                    processoutbox(entry[0])
                    return 0
        # If the code arrived here, means authentication failed
        if tries < 2:
            clientsock.send("ANOK")
            BLOCKED.insert(0,[clientaddr[0],int(time.time())])
        else:
            clientsock.send("ABLK")
            BLOCKED.insert(0,[clientaddr[0],int(time.time())])
    except IOError:
        print "Credentials file can not be read! Something is very wrong. Exiting..."
        exit (1)


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
def send(clientaddr, data):
    try:
        client.connect((clientaddr[0], 2663))
        client.send(data)
    except:
        print "Error connecting to the remote client. Guess it went offline"
    client.close()


# Refreshes ONLINE list when a client sends a heartbeat
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
    if isvaliduser(data):
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


# Sends a message to a single client
def message(clientaddr, data):
    data = data.split(' ', 1)
    if not isvaliduser(data[0]):
        send(clientaddr, "ERROR: the user you are sending the message to does not exist")
        return 0
    if isblocking(clientaddr, data[0]):
        send(clientaddr, "ERROR: the user " + data[0] + " is blocking you")
        return 0
    if isonline(data[0]):
        msg = "MSG FROM " + iptoname(clientaddr) + ": " + data[1]
        addressee = (nametoip(data[0]), 2663)
        send(addressee, msg)
        send(clientaddr, "Message successfully sent")
        print "Sent " + msg
    else:
        msg = "OFFLINE MSG FROM " + iptoname(clientaddr) + ": " + data[1]
        OUTBOX.append([data[0], msg])
        send(clientaddr, "Message stored for delivery when " + data[0] + " comes back online")


# Sends a broadcast message
def broadcast(clientaddr, data):
    count = 0
    for entry in ONLINE:
        if not isblocking(clientaddr, entry[1]):
            msg = "BCAST MSG FROM " + iptoname(clientaddr) + ": " + data
            addressee = (entry[0], 2663)
            send(addressee, msg)
            count += 1
    send(clientaddr, "Message delivered to " + count + " online users")


def serverthread(clientsock, clientaddr):
    receive = clientsock.recv(BUFSIZE)
    command = receive.split(' ', 1)
    if command[0] == "AUTH":
        auth(clientsock, clientaddr, command[1])
    elif command[0] == "LIVE":
        heartbeat(clientaddr)
    elif command[0] == "MESG":
        message(clientaddr, command[1])
    elif command[0] == "BCST":
        broadcast(clientaddr, command[1])
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
clientservthread = Thread(target=server)
clientservthread.start()


# Thread that removes clients that haven't been sending heartbeats from the online list. Runs once every 15s
def idlecleanup():
    while True:
        time.sleep(15)
        for entry in ONLINE:
            if entry[2] < (time.time() - BLOCK_TIME):
                ONLINE.pop(ONLINE.index(entry))
                print "Removed idle client " + entry[1]
cleanupthread = Thread(target=idlecleanup)
cleanupthread.start()