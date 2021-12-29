import random


class QuestionBank:

    def __init__(self):
        self.questions = ["How much is 2+2?", "How much is 2*2?", "How much is 1+7?", "How much is 4*2?",
                          "How much is 5%2?", "How much is 3%7?", "How much is 6%3?", "How much is 9-6?",
                          "How much is 30*2-56?", "What is the derivative of x^2 at 4?",
                          "What is the derivative of (x^3-3x) at 2?",
                          "What is te derivative of sin(x) at x = pi\\2?",
                          "what is the limit of f(x)= 1\\x when x approaches infinity",
                          "what is the value of sqrt(5^2 - 16)? "
                          ]
        self.answers = ["4", "4", "8", "8", "1", "3", "0", "3", "4", "8", "9", "0", '0', '3']
        self.index = -1

    def get_question(self):
        self.index = random.randrange(0, len(self.questions))
        return self.questions[self.index]

    def get_answer(self):
        return self.answers[self.index]
