# Computer Networks Spring 2015
# Programming assignment 1
# Roberto Amorim - rja2139

import argparse
import socket
from threading import Thread

# Configuration variables
TIMEOUT = 60
BUFSIZE = 1024

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


def auth(clientsock, message):
    print "bogus"


def serverthread(clientsock, clientaddr):
    receive = clientsock.recv(BUFSIZE)
    print receive
    command = receive.split(' ',1)
    if command[0] == "AUTH":
        print "bogus"
        #auth(clientsock, command[1])
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
