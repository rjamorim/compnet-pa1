COMPUTER NETWORKS SPRING 2015
PROGRAMMING ASSIGNMENT 1
ROBERTO AMORIM - rja2139

The programs (that is, the server and the client) were designed to take advantage of threads.
In both cases, a thread is created to stay listening to messages. Once a message is received,
it is parsed and analysed so that the program can decide how to proceed.

Also, special threads were created in both the server and the client to take care of the
heartbeat functionality. In the client, the thread sends the LIVE message to the server every
45 seconds. In the server, the thread scans the ONLINE data structure (containing information
about the connected clients) every 60 seconds to check if a client stopped sending heartbeat
messages. In that case, the client is removed from the ONLINE structure

The client starts by requesting login information from the user and sending that information
to the server. If he fails, he can retry three times and then gets blocked by a configurable
amount of time (10 minutes by default). If he succeeds, he is greeted by a welcome message
and a prompt to start typing.

The client works having the user type command at the prompt followed by further instructions
or a message. The program parses the command written by the user and takes the appropriate
action, usually converting it into the protocol (outlined further below) and sending it to
the server.

Once the message arrives at the server, it is analysed and, depending on the protocol header,
the appropriate function is called to process that message. Functions can perform tasks such
as sending a message to a single client, sending a broadcast message to all clients, asking
for a list of connected users, asking for an user's private IP address and asking to log out,
among other requests.

The request for an user's private IP, mentioned earlier, is for an interesting functionality:
once the client has it, he can initiate conversation directly with the other client, without
mediation from the server. This type of communication is called Peer to Peer (P2P) and can
be useful to exchange sensitive information, among other uses.

Another valuable feature is the guaranteed message delivery. With this functionality, if a
client sends a message to an user that is offline, the server takes care of storing it until
that user comes online. And it works even in P2P messages: if a message delivery fails, it
is sent to the server for storage and later delivery.

Broadcast messages are sent when an user logs in and logs out. Also, as an added feature, the
server itself sends a broadcast message when it gets killed through ctrl-c, informing users
that it is going down.

Talking about Ctrl-C, both server and client monitor for usage of these keys and exit
gracefully, closing open sockets and exiting from threads.

Part 1.2 of P2P privacy bonus part has also been implemented: When A requests for B’s IP address,
the message centre checks B’s blacklist preferences. If B’s blacklist includes A, the message
centre does not provide B’s IP address to A.

Besides these, several checks are performed throughout the programs, to check, for instance,
if an user is trying to send a message to a nonexisting user (that is, the user doesn't appear
in the credentials database) or if an user that just connected is not connected already (that
is, two clients using the sema credentials). In that case, the older connection is forced to
disconnect.


*******************************
How to run:
Server:
python server.py --port 1234

Client:
python client.py --server 128.59.15.30 --port 1234
(each client instance must be run on a different machine, since it listens in hardcoded port
2663 to receive messages from the server and from other clients)


*******************************
These are the message headers of the communication protocol:

Messages sent by the client:
MESG: message a single client
BCST: broadcast message
ONLN: ask server who is online
BLCK: block user
UNBL: unblock user
LOGT: logout
GETA: get IP address for P2P communication
LIVE: Heartbeat routine

Messages sent by the server:
AUOK: Authentication OK
ANOK: Authentication failure
ABLK: Authentication blocked
KICK: message forcing an user to log out
PRIP: message containing the private IP requested with getaddress

Data structures stored in the server:
BLOCKED: list of [IP,timestamp] pairs
ONLINE: list of [IP,name,timestamp] lists
BLACKLIST: list of [name,name] pairs. 1st value is who blocked, 2nd is who got blocked
OUTBOX: list of [name,message] pairs

Data structures stored in the client:
PRIVATE: list of [name,ip] pairs for private messaging