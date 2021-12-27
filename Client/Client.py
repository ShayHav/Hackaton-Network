from socket import *
import json
# TODO check what to do with sending messages via json


class Client:
    udpPort = 13117
    magicCookie = 0xabcddcba
    messageType = 0x2
    offerLength = 7 * 8
    server_port = None
    tcp_socket = None

    def __init__(self, team_name, ip_address=gethostbyname(gethostname())):
        self.udpSocket = socket(AF_INET, SOCK_DGRAM)
        self.udpSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # TODO change after
        self.ip = "10.0.0.38"
        self.udpSocket.bind((self.ip, self.udpPort))
        self.team_name = team_name

    def receive_offer(self):
        message, server_address = self.udpSocket.recvfrom(1024)
        decoded_message = json.loads(message.decode())
        magic_cookie = decoded_message.get("magicCookie")
        message_type = decoded_message.get("messageType")
        server_port = decoded_message.get("tcpPort")
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
                except InterruptedError:
                    print("got exception")
                except ConnectionRefusedError:
                    continue
                finally:
                    self.tcp_socket.close()
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
    print("Enter team name:")
    client = Client(input())
    client.start_client()
