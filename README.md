# P2P Messaging System

## Objective
Aim of this project is to build a Gossip protocol over a peer-to-peer network to broadcast messages and check the liveness of connected peers. Here “liveness” means that the peer is up and running, and is able to respond to messages sent to it.

Here we are going to deploy a p2p messaging system using a decentralized protocol to ensure message propagation and peer connectivity. This README offers an outline of the network architecture, protocol specifics, program functionality, input and output formats and Execution method.



## Network Architecture
The network comprises seed and peer nodes:

- **Seed Nodes:** Seed nodes serve as initial entry points to the P2P network. When the seed.py is run it create the sockets for each ip and port stored in cofig.json file. They are responsible for maintaining a list of active peers and facilitating the bootstrap process for new nodes. Seed nodes listen for incoming connections from peer nodes. Once connected, they provide peer lists to new peer nodes and assist in establishing connections. Seed nodes play a crucial role in ensuring the network's stability and connectivity.

- **Peer Nodes:** Peer nodes are the regular participants in the P2P network. They connect to seed nodes to join the network and then communicate with other peer nodes in network. A peer node initially randomly picks n/2+1 seeds from config.json file and after connecting to each selected seed node, a peer node retrieves a list of other peers(union of all other peers to which seeds are connected) and establishes connections with a subset(randomly 4) of them. Peer nodes exchange messages with each other, such as gossip messages for data propagation and liveness messages for monitoring peer livliness. They also send periodic updates to seed nodes to maintain their presence in the network.



## Key Concepts
- **Threading:** Enables multiple nodes to serve as servers and clients concurrently.
- **Socket Programming:** Server and client sockets are made using python socket library
- **Locks:** As threads share the common memory, so to avoid the race condition locks are used


## Input Format
- Here I have created a `config.json` file where I have hardcoded the information of seed's host and port. Currently I am using 4 seed nodes in this assignment.
- When executing `peer.py`, users are prompted to input the peer's unique port number, here I have hardcoded the peer's ip with localhost (127.0.0.1) as the host.



## How to Execute
1. Launch `seed.py` to activate seed nodes.
2. Create multiple instances of peer nodes via the command line, assigning a port for each peer.


## Message Protocol (Note initial number is codeinteger for specific message)
1. Gossip message = <1133> <self.port> <timestamp> <msg_count>
2. Liveliness message  = <1122> <timestamp> <self.port>
3. Reply of Liveliness message = <1144> <timestamp> <sender.port> <self.port>
4. Propagated Gossip message = <1155> <self.port> <timestamp> <msg_count>



## Output Format
- **Seed:** Here I am showing the real-time output on the terminal console and also storing the output in the file named `output_seed.txt`. Each time a seed is connected to peer I am showing it in output

- **Peer:** Here I am showing the real-time output for each peer on different terminals because I am creating different instances of the peers to make different peer nodes. Also I am creating different output files for each peer with file name `output_{port}.txt`.
Here I am showing every message that the peer is receiving also at every 13 seconds I am also showing its peer_list of that peer just for more clarification



## Functionality
- First when we launch `seed.py`, it takes the information of host and port from the config file and set up each seed node to accept connection from the peers.
- Seed nodes than accept incoming connections from peers.
- Peers, upon connecting to a seed node, it register itself to the peer list and retrieve the updated peer lists from all its connected seeds.
- Also if we have `n` seeds than each peer will connect to `[n/2]+1` seeds
- Peers exchange two types of messages: Gossip and liveness messages. Each peer sends 10 gossip messages to neighbors, forwarding new messages. Liveness messages are sent periodically(every 13s) to verify peer status.
- If a peer fails to receive responses to three consecutive liveness messages from a neighbor, it notifies connected seed nodes for removal from the peer list.
- Closing a peer triggers a dead message reported to seed nodes.



## Proof of Correctness
- **Broadcast:** Message origins differ from sender IDs, affirming broadcast functionality.
- **Gossips:** All nodes commence gossip communication upon connection, evident from the output.
- **Liveliness:** Receipt of dead messages by seed nodes validates peer liveliness checks.
- **Dead Nodes:** Closing a peer results in dead message notifications to seed nodes, confirming detection.



## Potential Attacks 
- **Sybil Attack:** Malicious peers create multiple fake identities to manipulate the network.
- **Denial of Service (DoS) Attack:** Overwhelm nodes with high message volumes to disrupt operations.
- **Eclipse Attack:** Attackers isolate a target node by surrounding it with malicious peers.

## Mitigation Strategies
- **Firewall and Filtering:** Detect and block malicious traffic to mitigate DoS attacks.
- **Peer Reputation Systems:** Assess peer behavior to identify and isolate malicious actors.
- **Sybil Resistance:** Implement mechanisms to limit the influence of Sybil nodes.




