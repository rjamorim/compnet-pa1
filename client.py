# Computer Networks Spring 2015
# Programming assignment 1
# Roberto Amorim - rja2139

import argparse
import socket
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
if args.serverPort.isdigit():
    port = int(args.port)
    if port > 65535:
        print "ERROR: The port number is outside the acceptable range! (0-65535)"
        exit(1)
else:
    print "ERROR: The server port must be a number!"
    exit (1)

## we have the required info, now let's start a server that will receive messages
# def receive():
#     while True:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         try:
#             sock.bind(("localhost", 2663))
#         except:
#             print "Error connecting to the remote server. Is it running? Are the IP and port you provided correct?"
#             exit(1)
#         message = sock.recv(BUFSIZE)
# Thread(target=receive()).start()

def serverthread(serversock):
    message = serversock.recv(BUFSIZE)

def server(host, port):
    server = socket(socket.AF_INET, socket.SOCK_STREAM)     # listen on TCP/IP socket
    server.bind(("localhost", 2663))                 # serve clients in threads
    server.listen(5)
    while True:
        serversock, serveraddr = server.accept( )
        Thread.start_new_thread(serverthread, (serversock,))

Thread(target=server).start()

client = socket(socket.AF_INET, socket.SOCK_STREAM)     # listen on TCP/IP socket
client.bind((args.ip, args.port))
while True:
    data = raw_input('> ')
    if not data: break
    client.send(data)

client.close()

