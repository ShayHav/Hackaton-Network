import struct
from socket import *
import json
from scapy.arch import get_if_addr
# TODO check what to do with sending messages via json


class Client:
    udpPort = 13117
    magicCookie = 0xabcddcba
    messageType = 0x2
    server_port = None
    tcp_socket = None

    def __init__(self, team_name, inter='eth1'):
        self.udpSocket = socket(AF_INET, SOCK_DGRAM)
        self.udpSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        #self.ip = "132.73.206.118"
        self.ip = get_if_addr(inter)
        self.udpSocket.bind(("172.99.255.255", self.udpPort))
        self.team_name = team_name

    def receive_offer(self):
        message, server_address = self.udpSocket.recvfrom(1024)
        magic_cookie = int.from_bytes(message[0:4], "little")
        message_type = int.from_bytes(message[4:5], "little")
        server_port = int.from_bytes( message[5:], "little")
        # magic_cookie, message_type, server_port = struct.unpack("Ibh", message)
        print(f"Received offer from {server_address[0]},attempting to connect...")
        return magic_cookie, message_type, server_port, server_address

    def start_client(self):
        while True:
            print("Client started, listening for offer requests...")
            magic_cookie, message_type, server_port, server_address = self.receive_offer()
            if magic_cookie == self.magicCookie and message_type == self.messageType:
                try:
                    self.tcp_socket = socket(AF_INET, SOCK_STREAM)
                    self.tcp_socket.connect((server_address[0], server_port))
                    message = f"{self.team_name}\n".encode("utf-8")
                    self.tcp_socket.send(message)
                    self.handle_game()
                except (InterruptedError, ConnectionRefusedError, ConnectionResetError) as e:
                    print("error message")
                    continue

                print("Server disconnected, listening for offer requests...")

    def handle_game(self):
        message = self.tcp_socket.recv(2048)
        print(message.decode("utf-8"))
        answer = input()
        self.tcp_socket.send(answer.encode("utf-8"))
        message = self.tcp_socket.recv(2048)
        print(message.decode("utf-8"))
        self.tcp_socket.close()
        return None


if __name__ == '__main__':
    print("dev mode?[y,n]")
    ans = input()
    inter = 'eth1' if ans == "y" else 'eth2'
    print("Enter team name:")
    client = Client(input(), inter)
    client.start_client()
