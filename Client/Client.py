from socket import *


class Client:
    udpPort = 13117
    magicCookie = 0xabcddcba
    messageType = 0x2
    offerLength = 7 * 8
    server_port = None
    tcp_socket = None

    def __init__(self, team_name, ip_address=gethostname()):
        self.udpSocket = socket(AF_INET, SOCK_DGRAM)
        self.udpSocket.bind((ip_address, self.udpPort))
        self.team_name = team_name

    def receive_offer(self):
        message, server_address = self.udpSocket.recvfrom(7)
        magic_cookie = int(message[0:4])
        message_type = int(message[4:5])
        server_port = int(message[5:])
        print(f"Received offer from {server_address},attempting to connect...")
        return magic_cookie, message_type, server_port, server_address

    def start_client(self):
        while True:
            print("Client started, listening for offer requests...")
            magic_cookie, message_type, server_port, server_address = self.receive_offer()
            if magic_cookie == self.magicCookie and message_type == self.messageType:
                try:
                    tcp_socket = self.tcp_socket = socket(AF_INET, SOCK_STREAM)
                    tcp_socket.connect((server_address, server_port))
                    message = f"{self.team_name}\n".encode("utf-8")
                    tcp_socket.send(message)
                    self.handle_game()
                except:
                    print("got exception")
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
