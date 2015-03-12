COMPUTER NETWORKS SPRING 2015
PROGRAMMING ASSIGNMENT 1
ROBERTO AMORIM - rja2139





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