# Computer Networks Spring 2015
# Programming assignment 1
# Roberto Amorim - rja2139

import argparse
import socket
import thread
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


def serverthread(serversock):
    message = serversock.recv(BUFSIZE)
    print message


def server():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # listen on TCP/IP socket
    serversocket.bind(("localhost", port))                 # serve clients in threads
    serversocket.listen(5)
    while True:
        serversock, serveraddr = serversocket.accept( )
        clientthread = Thread(target=serverthread, args=(serversock,))
        clientthread.start()
        #thread.start_new_thread(serverthread, (serversock,))

clientservthread = Thread(target=server, args=())
clientservthread.start()
