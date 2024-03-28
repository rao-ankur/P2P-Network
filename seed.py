import socket
import threading
import json
import random
import pickle

# class for a seed node
class SeedNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.peer_list = []

    # to store output in output_seed.txt file 
    def write_to_file(self, message):
        with open("output_seed.txt", "a") as f:
            f.write(message)

    # to register the new peer in the peer list of the seed
    def handle_registration_request(self, peer_port):
        self.peer_list.append(peer_port)
        message = f"Peer {peer_port} registered to seed {self.port}\n"
        print(message)
        self.write_to_file(message)

    # to remove the dead node from the peer list
    def handle_dead_node_message(self, dead_ip, dead_port):
        if dead_port in self.peer_list:
            self.peer_list.remove(dead_port)

    # This is most important function that handle all the peer request
    def start(self):
        seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        seed_socket.bind((self.ip, self.port))
        seed_socket.listen(5)
        message = f"Seed node listening on {self.ip}:{self.port}\n"
        print(message)
        self.write_to_file(message)

        try:
            while True:
                client_socket, client_address = seed_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        except KeyboardInterrupt:
            print("Server is shutting down...")
        finally:
            seed_socket.close()

    # to handle the registration, Peerlist an removal of Dead node request
    def handle_client(self, client_socket):
        request = client_socket.recv(1024).decode("utf-8")
        if request.startswith("REGISTER"):
            _, peer_port = request.split(":")
            self.handle_registration_request(int(peer_port))
            client_socket.send(f"{peer_port} Registered successfully to {self.port}".encode("utf-8"))
        elif request.startswith("DEAD"):
            message_parts = request.split(':')
            dead_port = message_parts[2]
            dead_ip=message_parts[1]
            message = f"seed {self.port} recv dead node request : {request}"
            print(message)
            self.write_to_file(message)
            self.handle_dead_node_message(dead_ip, int(dead_port))
        elif request.startswith("PEERLIST_REQUEST"):
            neigh_list = pickle.dumps(self.peer_list)
            client_socket.sendall(neigh_list)
        client_socket.close()


if __name__ == "__main__":
    with open("output_seed.txt", "w") as f:  # Open file in write mode to clear it
        f.write(" ")

    with open("config.json", 'r') as f:
        config_data = json.load(f)

    seed_ports = config_data["seed_ports"]
    host = "127.0.0.1"
    try: 
        for port in seed_ports:
            seed = SeedNode(host, port)
            threading.Thread(target=seed.start).start()
    except KeyboardInterrupt:
        print("Ctrl+C pressed: Exiting...")
    finally:
        pass 