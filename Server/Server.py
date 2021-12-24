from socket import *
import threading
import time
import QuestionBank
import json

class Server:
    udpDstPort = 13117
    server_udp_port = 12000
    server_tcp_port = 12001
    magicCookie = 0xabcddcba
    messageType = 0x2
    message = None
    teams_names = [None]*2
    answers = []
    c_in = threading.Condition()
    outgoing_messages = []
    c_out = threading.Condition()

    def __init__(self):
        self.question_bank = QuestionBank.QuestionBank()
        self.server_udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.welcoming_tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.welcoming_tcp_socket.setblocking(False)
        # TODO change after
        self.ip = "10.0.0.38"
        self.server_udp_socket.bind((self.ip, self.server_udp_port))
        self.welcoming_tcp_socket.bind((gethostname(), self.server_tcp_port))
        self.welcoming_tcp_socket.listen(2)

    def send_offers(self):
        number_of_players = 0
        conn1, client_address1 = None, None
        conn2, client_address2 = None, None

        print(f"Server started, listening on IP address {self.ip}")
        message = json.dumps({"magicCookie": self.magicCookie,
                              "messageType":  self.messageType,
                              "tcpPort": self.server_tcp_port})
        # accepting two player
        while number_of_players < 2:
            self.server_udp_socket.sendto(message.encode(), ("255.255.255.255", self.udpDstPort))
            time.sleep(1)

            if not conn1 and not client_address1:
                conn1, client1_address = self.welcoming_tcp_socket.accept()
                if conn1:
                    number_of_players = number_of_players + 1

            if not conn2 and not client_address2:
                conn2, client2_address = self.welcoming_tcp_socket.accept()
                if conn2:
                    number_of_players = number_of_players + 1

        # creating the Threads, one to each player and starting the game
        player1 = threading.Thread(target=self.receive_player, args=(conn1, client_address1, 0))
        player2 = threading.Thread(target=self.receive_player, args=(conn2, client_address2, 1))

        player1.start()
        player2.start()

        self.assemble_message()
        self.decide_winner()
        player1.join()
        player2.join()

        # clean server resources after the game
        self.clean()

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
                self.c_in.release()
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
        self.c_out.release()
        self.c_out.notify_all()

    def draw(self):
        self.c_out.acquire()
        self.outgoing_messages.append(f"""Game over!
                                     The correct answer was {self.question_bank.get_answer()}
                                     The game was ended with a draw""")
        self.c_out.release()
        self.c_out.notify_all()

    def assemble_message(self):
        can_assemble = False
        while not can_assemble:
            self.c_in.acquire()
            if not (self.teams_names[0] and self.teams_names[1]):
                self.c_in.release()
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
        self.c_in.release()
        self.c_out.notify_all()

    def receive_player(self, conn, address, player_id):
        # get the team name of the player and save it
        team_name = conn.recvfrom(1024).decode("utf-8")
        self.c_in.acquire()
        self.teams_names.insert(player_id, team_name)
        self.c_in.release()
        self.c_in.notify_all()
        # sending the message
        self.send_question(conn, address)
        # getting the answer from the player
        answer = conn.recvfrom(1024).decode("utf-8")
        self.c_in.acquire()
        self.answers.append((player_id, answer))
        self.c_in.release()
        self.c_in.notify_all()
        # sending the response to the player
        self.c_in.acquire()
        if len(self.outgoing_messages) == 0:
            self.c_in.release()
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
            self.c_out.release()
            self.c_out.wait()
            self.c_out.acquire()
            message_to_send = self.message.encode("utf-8")
            conn.sendto(message_to_send, address)
        self.c_out.release()

    def start(self):
        while True:
            try:
                self.send_offers()
            except InterruptedError:
                print("got message")


if __name__ == "__main__":
    server = Server()
    server.start()
