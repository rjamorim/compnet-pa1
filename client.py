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
BUFSIZE = 1024
PRIVATE = []
user = ""

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
    exit(1)


## We have the required info, now let's authenticate with the server
while True:
    try:
        user = raw_input('Username: ')
        pwd = raw_input('Password: ')
    except KeyboardInterrupt:
        exit(0)
    message = "AUTH " + user + " " + pwd
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((args.ip, port))
    except:
        print "Error connecting to the remote server. Is it running? Are the IP and port you provided correct?"
        exit(1)
    client.send(message)
    resp = client.recv(BUFSIZE)
    client.close()
    if resp == "AUOK":
        print "Welcome to simple chat server!"
        break
    elif resp == "ANOK":
        print "Invalid password. Please try again"
    elif resp == "ABLK":
        print "Too many authentication failures. You have been blocked. Try again after some time"
        exit(0)


# Checks whether the user has the IP address of a client he's trying to contact
def haveip(name):
    for entry in PRIVATE:
        if entry[0] == name:
            return True
    return False


# Deals with incoming IP addresses for other clients
def gotprivate(data):
    data = data.split(' ', 1)
    PRIVATE.append([data[0],data[1]])
    print "> " + data[0] + " shared his IP address with you. You can now message him directly <\n> "


# Function that sends data to other clients in P2P mode
def private(data):
    message = data.split(' ', 1)
    for entry in PRIVATE:
        if entry[0] == message[0]:
            ip = entry[1]
            privsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                privsock.connect((ip, 2663))
                privsock.send("PRIV MSG from " + user + ": " + message[1])
            except:
                print "> Error connecting to the remote client. Please request its IP address again.  <\n> "
                # And here's a little bit of guaranteed message delivery:
                print "> Your message wil be sent through the server to be deliveded when the user connects again  <\n> "
                send("MESG " + data)
                PRIVATE.pop(PRIVATE.index(entry))
            privsock.close()
            return 0
    else:
        print "> You must request this user's IP address before contacting him directly <\n> "



# Function that sends data to the remote server
def send(data):
    clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientsock.connect((args.ip, port))
        clientsock.send(data)
    except:
        print "Error connecting to the remote server. Guess it went offline"
        os._exit(0)
    # Connections must NEVER be persistent!
    clientsock.close()


def serverthread(serversock):
    data = serversock.recv(BUFSIZE)
    command = data.split(' ', 1)
    if command[0] == "KICK":
        print "> " + command[1] + " <\n> "
        cleanandexit()
    elif command[0] == "PRIP":
        gotprivate(command[1])
    else:
        print("> " + data + " <\n> "),


# Thread that listes for messages from the server or other clients (in P2P mode)
clientserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
def server():
    clientserv.bind(("0.0.0.0", 2663))
    clientserv.listen(5)
    while True:
        serversock, serveraddr = clientserv.accept()
        servthread = Thread(target=serverthread, args=(serversock,))
        servthread.start()
clientservthread = Thread(target=server)
clientservthread.start()


# Thread that sends heartbeats to server every 45s
def heartbeat():
    while True:
        time.sleep(45)
        send("LIVE")
heartbeatthread = Thread(target=heartbeat)
heartbeatthread.start()


# Signal handler that catches Ctrl-C and closes socket before exiting
def cleanandexit():
    clientserv.close()
    # I don't send the logout message to the server when quitting from interrupt because maybe the user
    # is doing this precisely because the server died
    os._exit(0)


# The main program loop
while True:
    try:
        text = raw_input('> ')
    except KeyboardInterrupt:
        print "Caught interrupt. Exiting..."
        cleanandexit()
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
        time.sleep(1)
        cleanandexit()
    elif command[0] == "getaddress":
        send("GETA " + command[1])
    elif command[0] == "private":
        for entry in PRIVATE:
            if entry[0] == command[1]:
                print "You already have the IP address for that user!"
                continue
        private(command[1])
    elif not command[0]:
        continue
    else:
        print "*** I could not understand the command you gave me. Valid commands are: ***"
        print "*** message, broadcast, online, (un)block, logout, getaddress, private  ***"


