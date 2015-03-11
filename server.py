# Computer Networks Spring 2015
# Programming assignment 1
# Roberto Amorim - rja2139

import argparse
import socket
import time
import signal
import os
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


# Converts an IP address into an user name, as long as the IP is in the ONLINE list
def iptoname(clientaddr):
    # A special case: the server uses IP address "none" when building the broadcast message calling quits
    if clientaddr[0] == "none":
        return "server"
    for entry in ONLINE:
        if entry[0] == clientaddr[0]:
            return entry[1]


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
        print "ERROR: Credentials file can not be read! Something is very wrong. Exiting..."
        os._exit(0)


# Here we check the outbox to see of the user that just logged in doesn't have any messages waiting
def processoutbox(data):
    addressee = (data[0],2663)
    flag = False
    for entry in OUTBOX:
        if entry[0] == data[1]:
            flag = True
            send(addressee, entry[1])
    # After sending the messages we delete them from the outbox
    if flag:
        for entry in OUTBOX:
            if entry[0] == data[1]:
                OUTBOX.pop(OUTBOX.index(entry))


# If an user ID logs in for the second time, the older login gets kicked out
def kick(user):
    msg = "KICK You will be logged out because another client logged in with your credentials"
    send([nametoip(user),2663],msg)
    ONLINE.pop(ONLINE.index([p for p in ONLINE if p[1] == user][0]))


# Notifies all other users when a new user logs in
def presence(clientaddr):
    name = iptoname(clientaddr)
    for entry in ONLINE:
        if entry[0] == clientaddr[0]:
            continue
        # Here we invert the isblocking parameters inverted, since in this case the blocker doesn't want to
        # tell the blocked user he came online
        if not isblocking(entry[1], name):
            msg = "BCAST MSG FROM SERVER: client " + name + " is now online"
            addressee = (entry[0], 2663)
            send(addressee, msg)


# Checks if a client asking to authenticate is blocked.
# Returns the amount of times it failed logging in the last BLOCK_TIME seconds
def isblocked(clientaddr):
    count = 0
    for entry in BLOCKED:
        if entry[0] == clientaddr[0]:
            # If the time stored is bigger than (current time minus BLOCK_TIME), that block entry is still valid
            if entry[1] >= (time.time() - BLOCK_TIME):
                count += 1
            # Since new items in the list are prepended and not appended, we can be sure the first match was the last
            # failed login. If the last failed login happened more than BLOCK_TIME ago, it doesn't matter anymore
            else:
                BLOCKED.pop(BLOCKED.index(entry))
    return count


# The client authentication function
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
                    # If another user is online with the same credentials, he gets logged out
                    if isonline(entry[0]):
                        kick(entry[0])
                    # The user is added to the online table
                    ONLINE.append([clientaddr[0], entry[0], int(time.time())])
                    # We check if the user didn't have offline messages waiting for him
                    processoutbox([clientaddr[0], entry[0]])
                    # Send a broadcast message informing about who just logged in
                    presence(clientaddr)
                    return 0
        # If the code arrived here, means authentication failed.
        if tries < 2:
            clientsock.send("ANOK")
            BLOCKED.insert(0,[clientaddr[0],int(time.time())])
        else:
            clientsock.send("ABLK")
            BLOCKED.insert(0,[clientaddr[0],int(time.time())])
    except IOError:
        print "ERROR: Credentials file can not be read! Something is very wrong. Exiting..."
        os._exit(0)


# The most important function, that sends messages to clients. Treat it with due respect
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
def send(clientaddr, data):
    try:
        clientsocket.connect((clientaddr[0], 2663))
        clientsocket.send(data)
    except:
        print "Error connecting to the client " + iptoname(clientaddr) + ". Guess it went offline"
        return False
    # Connections must NEVER be persistent!
    clientsocket.close()
    return True


# Refreshes ONLINE list when a client sends a heartbeat
def heartbeat(clientaddr):
    for entry in ONLINE:
        if entry[0] == clientaddr[0]:
            entry[2] = int(time.time())


# Routine for an user to block another user
def block(clientaddr, data):
    client = iptoname(clientaddr)
    # Some people just want to watch the world burn
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
def isblocking(sender, addressee):
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
    if isblocking(iptoname(clientaddr), data[0]):
        send(clientaddr, "ERROR: the user " + data[0] + " is blocking you")
        return 0
    if isonline(data[0]):
        msg = "MSG FROM " + iptoname(clientaddr) + ": " + data[1]
        addressee = (nametoip(data[0]), 2663)
        result = send(addressee, msg)
        # And here you have the guaranteed message delivery functionality! Quite simple and sweet
        if result:
            send(clientaddr, "Message successfully sent to " + data[0])
        else:
            msg = "OFFLINE MSG FROM " + iptoname(clientaddr) + ": " + data[1]
            OUTBOX.append([data[0], msg])
            send(clientaddr, "Client " + data[0] + " went offline! Msg stored for delivery when it comes back online")
            # Since that client is no longer responding, we remove it from the ONLINE list
            ONLINE.pop(ONLINE.index([p for p in ONLINE if p[0] == addressee and p[1] == data[0]][0]))
    else:
        msg = "OFFLINE MSG FROM " + iptoname(clientaddr) + ": " + data[1]
        OUTBOX.append([data[0], msg])
        send(clientaddr, "Message stored for delivery when " + data[0] + " comes back online")


# Sends a broadcast message
def broadcast(clientaddr, data):
    count = 0
    sender = iptoname(clientaddr)
    for entry in ONLINE:
        if entry[0] == clientaddr[0]:
            continue
        if not isblocking(sender, entry[1]):
            msg = "BCAST MSG FROM " + sender + ": " + data
            addressee = (entry[0], 2663)
            send(addressee, msg)
            count += 1
    # The message the server broadcasts when it is interrupted comes with a specially crafted "invalid" clientaddr
    # where the port number is -1. Therefore, in that case, the delivered message is not necessary
    if clientaddr[1] >= 0:
        send(clientaddr, "Message delivered to " + str(count) + " online users")


# Returns the list of online users
def online(clientaddr):
    msg = "Currently online users:"
    for entry in ONLINE:
        msg = msg + "\n" + entry[1]
    send(clientaddr, msg)


# User logs out: gets removed from online list
def logout(clientaddr):
    for entry in ONLINE:
        if entry[0] == clientaddr[0]:
            ONLINE.pop(ONLINE.index(entry))
    send(clientaddr, "You were successfully logged out")


# Function for when client requests anoter client's IP address for P2P communication
def getaddress(clientaddr, name):
    if not isvaliduser(name):
        send(clientaddr, "ERROR: the user which you are requesting the IP does not exist")
        return 0
    if isblocking(iptoname(clientaddr), name):
        send(clientaddr, "ERROR: the user " + name + " is blocking you")
        return 0
    if not isonline(name):
        send(clientaddr, "ERROR: the user " + name + " is not currently online")
        return 0
    clientip = nametoip(name)
    try:
        clientsocket.connect((clientip, 2663))
        clientsocket.send("PERM " + name)
        resp = clientsocket.recv(BUFSIZE)
    except:
        print "Error connecting to the client " + name + ". Guess it went offline"
        return False
    if resp == "y":
        send(clientaddr, "PRIP " + name + " " + clientip)
    else:
        send(clientaddr, "NOPE")
    # Connections must NEVER be persistent!
    clientsocket.close()
    return True


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
        online(clientaddr)
    elif command[0] == "BLCK":
        block(clientaddr, command[1])
    elif command[0] == "UNBL":
        unblock(clientaddr, command[1])
    elif command[0] == "LOGT":
        logout(clientaddr)
    elif command[0] == "GETA":
        getaddress(clientaddr, command[1])


serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
def server():
    try:
        serversocket.bind(("0.0.0.0", port))
    except:
        print "Can't bind. Maybe port is already in use?"
        os._exit(0)
    serversocket.listen(5)
    while True:
        clientsock, clientaddr = serversocket.accept()
        clientthread = Thread(target=serverthread, args=(clientsock, clientaddr))
        clientthread.start()


# Thread that removes clients that haven't been sending heartbeats from the online list. Runs once every 5s
def idlecleanup():
    while True:
        time.sleep(5)
        for entry in ONLINE:
            if entry[2] < (time.time() - BLOCK_TIME):
                ONLINE.pop(ONLINE.index(entry))
                print "Removed idle client " + entry[1]


# Main function, starts the helper threads
def main():
    clientservthread = Thread(target=server)
    clientservthread.start()
    cleanupthread = Thread(target=idlecleanup)
    cleanupthread.start()


# Signal handler that catches Ctrl-C and closes sockets before exiting
def handler(signum, frame):
    print "Quitting: Signal handler called with signal " + str(signum)
    # We send a specially crafted, impossible "clientaddr" to force the broadcast function to do our bidding
    broadcast(["none", -1], "Server is going down!")
    clientsocket.close()
    serversocket.close()
    os._exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    main()
    # If I let the main thread finish, it stops listening for signals
    while True:
        time.sleep(1)
