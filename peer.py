import socket
import threading
import json
import random
import time
import pickle
import hashlib
import sys

# class for a peer node
class PeerNode:
    # initialization of peer parameters
    def __init__(self, ip, port): 
        self.g=False  
        self.ip = ip
        self.port = port
        self.seed_ips = []
        self.seed_ports = []
        self.peer_list = set()
        self.max_peers = 4
        self.hash_list=[]           # store the hash of messages
        self.selected_seeds=[]
        self.dict_live = {0: 0}         # store the count of live mgs sent to the the peer ndes
        self.lock = threading.Lock()
        self.output_file = f"output_{port}.txt"  # Output file for this peer
        self.output_stream = open(self.output_file, "w")  # Open output file in append mode
        self.original_stdout = sys.stdout  # Save original stdout stream
        sys.stdout = Tee(self.original_stdout, self.output_stream) 


    # hash function to create hash of gossip messages
    def hash_message(self,message):
        hasher = hashlib.sha256()
        hasher.update(message.encode('utf-8'))
        hashed_message = hasher.hexdigest()
        return hashed_message

    # Read data from the JSON config file
    def read_config(self, config_file):
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        return config_data

    # Making our connection with the choosen seed nodes for registration
    def register_with_seeds(self):
        seed_nodes = list(zip(self.seed_ips, self.seed_ports))
        self.selected_seeds = random.sample(seed_nodes, len(seed_nodes) // 2 + 1)
        for seed_ip, seed_port in self.selected_seeds:
            try:
                with socket.create_connection((seed_ip, seed_port), timeout=2) as sock:
                    sock.send(f"REGISTER:{self.port}".encode("utf-8"))
                    response = sock.recv(1024).decode("utf-8")
                    print(response)
            except Exception as e:
                pass

    # Func to reciveing the peer list from seed nodes
    def request_peer_list_from_seeds(self):
        for seed_ip, seed_port in zip(self.seed_ips, self.seed_ports):
            try:
                with socket.create_connection((seed_ip, seed_port), timeout=5) as sock:
                    sock.send("PEERLIST_REQUEST".encode("utf-8"))
                    list = sock.recv(1024)       
                    neigh_list = pickle.loads(list)  # list ko byte from me convert
                    for neigh in neigh_list:
                        self.peer_list.add(neigh)
            except Exception as e:
                print(f"Failed to request peer list from seed {seed_ip}:{seed_port}: {e}")




    def send_gossip(self, client,msg_count):
        timestamp = int(time.time())
        message = f"{1133}:{self.port}:{timestamp}:{msg_count}"
        try:
            client.send(message.encode("utf-8"))
        except Exception as e:
            print(f"Failed to send gossip from {self.port}: {e}")

    # Function to send 10 peer messages at every 5 seconds
    def p2p_send_message(self, peer_port,message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((self.ip, peer_port))
                try:
                    client.send(message.encode("utf-8"))
                except Exception as e:
                    pass
        except:
            pass

    # function to make connection with random 4 neighbour peer in separate threads
    def establish_connections(self):
        msg_count=1
        for i in range(60):
            if i%5==0 and msg_count<=10:

                random_peers=[]
                self.lock.acquire() 
                if len(self.peer_list) < 4:
                    random_peers = self.peer_list
                else:
                    random_peers = random.sample(self.peer_list, 4)
                self.lock.release()

                timestamp = int(time.time())
                message = f"{1133}:{self.port}:{timestamp}:{msg_count}"
                h=self.hash_message(message)   # append msg in hash list
                self.hash_list.append(h)

                print("gossip generated : ",msg_count)
                for peer_port in random_peers:
                    if peer_port != self.port:
                        self.g=True
                        threading.Thread(target=self.p2p_send_message, args=(peer_port,message)).start()
                msg_count += 1
            time.sleep(1) 
            if msg_count>10:
                pass





    # Function that start registration of peer with seed
    def start(self):
        config_data = self.read_config("config.json")
        self.seed_ips = config_data["seed_ips"]
        self.seed_ports = config_data["seed_ports"]
        self.register_with_seeds()
        self.request_peer_list_from_seeds()
        self.peer_list = list(self.peer_list)
        for port in self.peer_list:
            self.dict_live[port]=0





    # Function to propagate the gossip message
    def propagation(self, peer_port,data):
        try:
            self.lock.acquire() 
            print("propagte msg from ",self.port," to ",peer_port)
            self.lock.release() 
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((self.ip, peer_port))
                # data_int= [int(x) for x in data.split(':')]
                # data_int[0]=1155
                # data = ':'.join(str(x) for x in data_int)
                try:
                    client.send(data.encode("utf-8"))  
                except Exception as e:
                    pass
        except:
            pass
    
    # Check the hash of gossip msg and decide to propogate gossip or not 
    def handle_gossip(self, data_int,data):
        received_port = data_int[1]
        if received_port not in self.peer_list:    # to update the peer list 
            self.peer_list.append(int(received_port))
            self.dict_live[received_port]=0        # to initialize the key for newly added peer in dict_live

        h=self.hash_message(data)
        if(h in self.hash_list):
            pass
        else:
            self.hash_list.append(h)
            for peer_port in self.peer_list:
                if peer_port != self.port and peer_port!=received_port:
                    threading.Thread(target=self.propagation, args=(peer_port,data)).start()


    # Function to send reply of the liveliness message
    def reply_liveliness(self, data_int):
        port_tosend=data_int[2]
        timestamp=data_int[1]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip, port_tosend))
                message = f"{1144}:{timestamp}:{port_tosend}:{self.port}"
                s.send(message.encode("utf-8"))
        except:
            pass
    

    # Function to hande the reply msg of liveliness
    def recieve_live_reply(self, data_int):
        self.lock.acquire()     # This lock ensures that the dict_live do not get changed by 2 threads simulatenously
        self.dict_live[data_int[3]]=0
        self.lock.release()

    # Function that differentiate between different messages that a peer recieves and call the corresponding function to handle those messages 
    def receive_peer(self, conn, addr):
        try:
            while True:
                data = conn.recv(500).decode()
                if not data:
                    continue
                data_parts = data.split(':')
                data_int = [int(x) for x in data_parts if x.strip()]
                if data_int[0] == 1133:   # gossip msg 
                    self.lock.acquire()
                    print(f"Gossip mgs recv : ",data)
                    self.lock.release()
                    # if(self.g==False):
                    #     threading.Thread(target=peer.establish_connections).start()
                    self.handle_gossip(data_int,data)

                if data_int[0] == 1122:  # liveliness msg
                    self.lock.acquire()
                    print(f"Liveliness msg recv : ",data)
                    self.lock.release()
                    threading.Thread(target=self.reply_liveliness, args=(data_int,)).start()

                if data_int[0] == 1144:  # reply of liveliness msg
                    self.lock.acquire()
                    print("reply of liveliness msg recv : ",data)
                    self.lock.release()
                    self.recieve_live_reply(data_int)

                # if data_int[0] == 1155:  # propagated msg
                #     self.lock.acquire()
                #     print("propagated msg : ",data)
                #     self.lock.release()
                #     self.handle_gossip(data_int,data)     

        except Exception as e:
           conn.close()
        finally:
            pass
    
    # This is most important function that handle all the peer request and call the recieve peer function in threads
    def start_node(self):
        host = self.ip
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, self.port))
                s.listen()
                print(f"Node listening on {host}:{self.port}\n")
                while True:
                    peer_socket, addr = s.accept()
                    threading.Thread(target=self.receive_peer, args=(peer_socket, addr)).start()

            except KeyboardInterrupt:
                print(f"Node {self.port}: KeyboardInterrupt: Exiting...")
            except Exception as e:
                print(f"Node {self.port}: An error occurred: {e}")

    

    # It remove the dead node feom peer list and connect with seed to share the dead node info
    def dead_node_activation(self,neigh_port):
        self.lock.acquire()
        print("Dead Node detected : ",neigh_port)
        self.peer_list.remove(neigh_port)
        del self.dict_live[neigh_port]
        self.lock.release()

        timestamp=int(time.time())
        message=f"DEAD:{self.ip}:{neigh_port}:{timestamp}:{self.port}"
        for seed_ip, seed_port in self.selected_seeds:
            try:
                with socket.create_connection((seed_ip, seed_port), timeout=2) as sock:
                    sock.send(message.encode("utf-8"))
            except Exception as e:
                print(f"Failed to register with seed {seed_ip}:{seed_port}: {e}")

    # It is responsiple to send the liveliness message to a given peer port and keep account of live msg counts 
    def send_live_msg(self,neigh_port,message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((self.ip, neigh_port))
                if self.dict_live[neigh_port]<3:
                    try:
                        client.send(message.encode())
                    except ConnectionError as e:
                        print(f"send liveliness error form {self.port} : {e}")
                    self.dict_live[neigh_port] += 1
                if self.dict_live[neigh_port]>2:
                    self.dead_node_activation(neigh_port)
        except:
            client.close()
            if self.dict_live[neigh_port]>2:
                self.dead_node_activation(neigh_port)
            else:
                self.dict_live[neigh_port] += 1
                
    # This func call send_live_msg for each port in peer_list at every 13 seconds
    def liveliness(self):
        while True:
            timestamp = int(time.time())
            message = f"{1122}:{timestamp}:{self.port}:"
            self.lock.acquire()
            print(f"Peer list is : {self.peer_list}")
            for neigh_port in self.peer_list:
                if neigh_port != self.port:
                    threading.Thread(target=self.send_live_msg, args=(neigh_port,message)).start()
            self.lock.release()
            time.sleep(13)

class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()  # Ensure immediate flushing for real-time output

    def flush(self):
        pass

    def close(self):
        for f in self.files:
            f.close()


if __name__ == "__main__":
    ip = input("Please type the Host id of the peer = ")   #127.0.0.1
    port = int(input("Enter port number of the peer: "))   #8000
    peer = PeerNode(ip, port)
    peer.start()
    threading.Thread(target=peer.start_node).start()
    print("a")
    threading.Thread(target=peer.establish_connections).start()
    threading.Thread(target=peer.liveliness).start()

