import math
import random
import tkinter as tk
from tkinter import messagebox

class TicTacToe:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна №6: Хрестики-нулики")
        
        self.board = [' ' for _ in range(9)]
        self.human = 'X'
        self.ai = 'O'
        self.buttons = []
        
        # Шанс того, що комп'ютер зробить випадковий (неідеальний) хід. 
        # 0.3 означає 30% ймовірність помилки. Ви можете змінювати це значення.
        self.error_chance = 0.3 
        
        self.create_gui()

    def create_gui(self):
        for i in range(9):
            button = tk.Button(self.root, text=' ', font=('Arial', 40, 'bold'), width=5, height=2,
                               command=lambda i=i: self.human_move(i))
            button.grid(row=i // 3, column=i % 3)
            self.buttons.append(button)

    def human_move(self, index):
        if self.board[index] == ' ':
            self.board[index] = self.human
            self.buttons[index].config(text=self.human)
            
            if self.check_win(self.board, self.human):
                messagebox.showinfo("Кінець гри", "Вітаємо! Ви перемогли!")
                self.reset_game()
            elif self.is_draw(self.board):
                messagebox.showinfo("Кінець гри", "Нічия!")
                self.reset_game()
            else:
                self.ai_move()

    def ai_move(self):
        best_move = None
        
        # Перевіряємо, чи спрацює шанс на помилку
        if random.random() < self.error_chance:
            # Комп'ютер "помиляється" і робить випадковий хід
            empty_spots = [i for i in range(9) if self.board[i] == ' ']
            if empty_spots:
                best_move = random.choice(empty_spots)
        else:
            # Комп'ютер грає ідеально за алгоритмом Minimax
            best_score = -math.inf
            for i in range(9):
                if self.board[i] == ' ':
                    self.board[i] = self.ai 
                    score = self.minimax(self.board, 0, False) 
                    self.board[i] = ' ' 
                    
                    if score > best_score:
                        best_score = score
                        best_move = i

        if best_move is not None:
            self.board[best_move] = self.ai
            self.buttons[best_move].config(text=self.ai)

            if self.check_win(self.board, self.ai):
                messagebox.showinfo("Кінець гри", "Комп'ютер переміг!")
                self.reset_game()
            elif self.is_draw(self.board):
                messagebox.showinfo("Кінець гри", "Нічия!")
                self.reset_game()

    def minimax(self, board, depth, is_maximizing):
        if self.check_win(board, self.ai): return 10 - depth
        if self.check_win(board, self.human): return depth - 10
        if self.is_draw(board): return 0

        # ВИПРАВЛЕНИЙ ВІДСТУП ТУТ:
        if is_maximizing:
            best_score = -math.inf
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.ai
                    score = self.minimax(board, depth + 1, False)
                    board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = math.inf
            for i in range(9):
                if board[i] == ' ':
                    board[i] = self.human
                    score = self.minimax(board, depth + 1, True)
                    board[i] = ' '
                    best_score = min(score, best_score)
            return best_score

    def check_win(self, board, player):
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for condition in win_conditions:
            if board[condition[0]] == board[condition[1]] == board[condition[2]] == player:
                return True
        return False

    def is_draw(self, board):
        return ' ' not in board

    def reset_game(self):
        self.board = [' ' for _ in range(9)]
        for button in self.buttons:
            button.config(text=' ')

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToe(root)
    root.mainloop()