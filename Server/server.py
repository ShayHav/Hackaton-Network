from socket import *
import threading
import time


class Server:
    udpDstPort = 13117
    server_udp_port = 12000
    server_tcp_port = 12001
    magicCookie = 0xabcddcba
    messageType = 0x2
    message = """Welcome to Quick Maths.
                    Player 1: Instinct
                    Player 2: Rocket
                    ==
                    Please answer the following question as fast as you can:
                    How much is 2+2?"""
    teams_names = [None]*2
    incoming_messages = []
    c_in = threading.Condition()

    outgoing_messages = []
    c_out = threading.Condition()

    def __init__(self):
        self.server_udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.welcoming_tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.welcoming_tcp_socket.setblocking(False)
        self.server_udp_socket.bind((gethostname(), self.server_udp_port))
        self.welcoming_tcp_socket.bind((gethostname(), self.server_tcp_port))
        self.welcoming_tcp_socket.listen(2)

    def send_offers(self):
        number_of_players = 0
        conn1, client_address1 = None, None
        conn2, client_address2 = None, None

        print(f"Server started, listening on IP address {gethostname()}")
        message = bytes([self.magicCookie, self.messageType, self.server_tcp_port])

        while number_of_players < 2:
            self.server_udp_socket.sendto(message, ("255.255.255.255", self.udpDstPort))
            time.sleep(1)

            if not conn1 and not client_address1:
                conn1, client1_address = self.welcoming_tcp_socket.accept()
                if conn1:
                    number_of_players = number_of_players + 1

            if not conn2 and not client_address2:
                conn2, client2_address = self.welcoming_tcp_socket.accept()
                if conn2:
                    number_of_players = number_of_players + 1

        player1 = threading.Thread(target=self.receive_player, args=(conn1, client_address1, 0)).start()
        player2 = threading.Thread(target=self.receive_player, args=(conn2, client_address2, 1)).start()

    def receive_player(self, conn, address, id):

        team_name = conn.recvfrom(2048)
        self.c_in.acquire()
        self.teams_names.insert(id, team_name)
        self.c_in.release()
        self.c_in.notify_all()

        self.c_out.acquire()
        if len(self.outgoing_messages) > 0:
            message = self.outgoing_messages[0]
            message = message.encode("utf-8")
            conn.sendto(message, address)
        else:
            time.sleep(50*(10**-3))
        self.c_out.release()
