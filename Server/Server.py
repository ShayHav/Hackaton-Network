from socket import *
import threading
import time
import QuestionBank
import json


class Server:
    udpDstPort = 13117
    server_udp_port = 20001
    server_tcp_port = 20000
    magicCookie = 0xabcddcba
    messageType = 0x2
    message = None
    teams_names = [None]*2
    answers = []
    c_in = threading.Condition()
    outgoing_messages = []
    c_out = threading.Condition()
    send_offers = True

    def __init__(self):
        self.question_bank = QuestionBank.QuestionBank()
        self.server_udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.server_udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.welcoming_tcp_socket = socket(AF_INET, SOCK_STREAM)
        # TODO change after
        self.ip = "192.168.1.210"
        self.server_udp_socket.bind((self.ip, self.server_udp_port))
        self.welcoming_tcp_socket.bind((self.ip, self.server_tcp_port))
        self.welcoming_tcp_socket.listen()

    def manage_server(self):
        print(f"Server started, listening on IP address {self.ip}")

        offer_thread = threading.Thread(target=self.send_udp_offers, args=[])
        offer_thread.start()

        # accepting two player
        conn1, client1_address = self.welcoming_tcp_socket.accept()
        conn2, client2_address = self.welcoming_tcp_socket.accept()
        print(client1_address, client2_address)
        self.send_offers = False

        # creating the Threads, one to each player and starting the game
        player1 = threading.Thread(target=self.receive_player, args=[conn1, client1_address, 0])
        player2 = threading.Thread(target=self.receive_player, args=[conn2, client2_address, 1])

        player1.start()
        player2.start()

        self.assemble_message()
        self.decide_winner()
        player1.join()
        player2.join()

        # clean server resources after the game
        self.clean()

    def send_udp_offers(self):
        message = json.dumps({"magicCookie": self.magicCookie,
                              "messageType":  self.messageType,
                              "tcpPort": self.server_tcp_port})
        while self.send_offers:
            self.server_udp_socket.sendto(message.encode(), ("255.255.255.255", self.udpDstPort))
            time.sleep(1)

    def clean(self):
        self.message = None
        self.teams_names = [None, None]
        self.answers = []
        self.outgoing_messages = []

    def decide_winner(self):
        current_time = time.time()
        correct_answer = self.question_bank.get_answer()
        self.c_in.acquire()
        while True:
            if time.time() - current_time > 10:
                self.draw()
                return
            self.c_in.acquire()
            if len(self.answers) == 0:
                self.c_in.wait(10)
            else:
                break

        self.c_in.acquire()
        player_id, answer = self.answers[0]
        if correct_answer == answer:
            winner = player_id
        else:
            winner = (player_id + 1) % 2

        self.c_in.release()
        self.c_out.acquire()
        self.outgoing_messages.append(f"""Game over!
                             The correct answer was {correct_answer}
                             Congratulations to the winner: {self.teams_names[winner]}""")
        self.c_out.notify_all()
        self.c_out.release()

    def draw(self):
        self.c_out.acquire()
        self.outgoing_messages.append(f"""Game over!
                                     The correct answer was {self.question_bank.get_answer()}
                                     The game was ended with a draw""")
        self.c_out.notify_all()
        self.c_out.release()

    def assemble_message(self):
        can_assemble = False
        while not can_assemble:
            self.c_in.acquire()
            if not (self.teams_names[0] and self.teams_names[1]):
                self.c_in.wait()
            else:
                can_assemble = True

        question = self.question_bank.get_question()
        self.message = f"""Welcome to Quick Maths.
                      Player 1: {self.teams_names[0]}
                      Player 2: {self.teams_names[1]}
                      ==
                      Please answer the following question as fast as you can:
                      {question}"""
        self.c_out.acquire()
        self.c_out.notify_all()
        self.c_out.release()
        self.c_in.release()

    def receive_player(self, conn, address, player_id):
        # get the team name of the player and save it
        team_name = conn.recv(1024).decode("utf-8")
        self.c_in.acquire()
        self.teams_names.insert(player_id, team_name)
        self.c_in.notify_all()
        self.c_in.release()
        # sending the message
        self.send_question(conn, address)
        # getting the answer from the player
        answer = conn.recv(1024).decode("utf-8")
        self.c_in.acquire()
        self.answers.append((player_id, answer))
        self.c_in.notify_all()
        self.c_in.release()
        # sending the response to the player
        self.c_in.acquire()
        if len(self.outgoing_messages) == 0:
            self.c_in.wait()
        self.c_in.acquire()
        message = self.outgoing_messages[0].encode("utf-8")
        conn.sendto(message)
        conn.close()

    def send_question(self, conn, address):
        # get the lock to the question to send
        self.c_out.acquire()
        if self.message:
            message_to_send = self.message.encode("utf-8")
            conn.sendto(message_to_send, address)
        else:
            self.c_out.wait()
            self.c_out.acquire()
            message_to_send = self.message.encode("utf-8")
            conn.sendto(message_to_send, address)
        self.c_out.release()

    def start(self):
        while True:
            try:
                self.manage_server()
            except InterruptedError:
                print("got message")


if __name__ == "__main__":
    server = Server()
    server.start()
