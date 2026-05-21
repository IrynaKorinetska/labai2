using System;
using System.Drawing;
using System.Windows.Forms;

namespace TicTacToeDecisionTree
{
    public partial class Form1 : Form
    {
        private Button[] buttons;
        private char[] board;
        private char humanPlayer = 'X';
        private char aiPlayer = 'O';

        public Form1()
        {
            InitializeGame();
        }

        // Етап 5: Візуалізація поля гри та взаємодії з користувачем
        private void InitializeGame()
        {
            this.Text = "Хрестики-нулики (Дерево рішень / Minimax)";
            this.Size = new Size(320, 340);
            this.StartPosition = FormStartPosition.CenterScreen;

            buttons = new Button[9];
            board = new char[9];

            for (int i = 0; i < 9; i++)
            {
                board[i] = ' '; // Порожнє поле
                buttons[i] = new Button();
                buttons[i].Size = new Size(100, 100);
                buttons[i].Location = new Point((i % 3) * 100, (i / 3) * 100);
                buttons[i].Font = new Font("Arial", 36, FontStyle.Bold);
                buttons[i].Name = i.ToString();
                buttons[i].Click += new EventHandler(PlayerMove);
                this.Controls.Add(buttons[i]);
            }
        }

        // Хід людини (Етап 6)
        private void PlayerMove(object sender, EventArgs e)
        {
            Button btn = (Button)sender;
            int index = int.Parse(btn.Name);

            if (board[index] == ' ')
            {
                board[index] = humanPlayer;
                btn.Text = humanPlayer.ToString();
                btn.ForeColor = Color.Blue;

                if (CheckWin(humanPlayer))
                {
                    MessageBox.Show("Ви перемогли! (Це неможливо)", "Кінець гри");
                    ResetBoard();
                    return;
                }
                else if (IsBoardFull())
                {
                    MessageBox.Show("Нічия!", "Кінець гри");
                    ResetBoard();
                    return;
                }

                ComputerMove();
            }
        }

        # Етап 4: Допоміжна функція для вибору комп'ютером рішення з дерева (Мінімакс)
        private void ComputerMove()
        {
            int bestScore = int.MinValue;
            int move = -1;

            // Будуємо перший рівень дерева рішень
            for (int i = 0; i < 9; i++)
            {
                if (board[i] == ' ')
                {
                    board[i] = aiPlayer; // Пробуємо хід
                    int score = Minimax(board, 0, false);
                    board[i] = ' '; // Скасовуємо хід

                    if (score > bestScore)
                    {
                        bestScore = score;
                        move = i;
                    }
                }
            }

            if (move != -1)
            {
                board[move] = aiPlayer;
                buttons[move].Text = aiPlayer.ToString();
                buttons[move].ForeColor = Color.Red;

                if (CheckWin(aiPlayer))
                {
                    MessageBox.Show("Комп'ютер переміг!", "Кінець гри");
                    ResetBoard();
                }
                else if (IsBoardFull())
                {
                    MessageBox.Show("Нічия!", "Кінець гри");
                    ResetBoard();
                }
            }
        }

        // Етап 3: Обхід дерева рішень (Minimax) - забезпечує безпрограшну гру
        private int Minimax(char[] currentBoard, int depth, bool isMaximizing)
        {
            if (CheckWin(aiPlayer)) return 10 - depth; // Швидка перемога цінується більше
            if (CheckWin(humanPlayer)) return -10 + depth;
            if (IsBoardFull()) return 0;

            if (isMaximizing)
            {
                int bestScore = int.MinValue;
                for (int i = 0; i < 9; i++)
                {
                    if (currentBoard[i] == ' ')
                    {
                        currentBoard[i] = aiPlayer;
                        int score = Minimax(currentBoard, depth + 1, false);
                        currentBoard[i] = ' ';
                        bestScore = Math.Max(score, bestScore);
                    }
                }
                return bestScore;
            }
            else
            {
                int bestScore = int.MaxValue;
                for (int i = 0; i < 9; i++)
                {
                    if (currentBoard[i] == ' ')
                    {
                        currentBoard[i] = humanPlayer;
                        int score = Minimax(currentBoard, depth + 1, true);
                        currentBoard[i] = ' ';
                        bestScore = Math.Min(score, bestScore);
                    }
                }
                return bestScore;
            }
        }

        // Перевірка перемоги
        private bool CheckWin(char player)
        {
            int[,] winCombinations = new int[,] {
                {0, 1, 2}, {3, 4, 5}, {6, 7, 8}, // Горизонталі
                {0, 3, 6}, {1, 4, 7}, {2, 5, 8}, // Вертикалі
                {0, 4, 8}, {2, 4, 6}             // Діагоналі
            };

            for (int i = 0; i < 8; i++)
            {
                if (board[winCombinations[i, 0]] == player &&
                    board[winCombinations[i, 1]] == player &&
                    board[winCombinations[i, 2]] == player)
                {
                    return true;
                }
            }
            return false;
        }

        // Перевірка на заповненість дошки (нічия)
        private bool IsBoardFull()
        {
            foreach (char c in board)
            {
                if (c == ' ') return false;
            }
            return true;
        }

        // Очищення поля для нової гри
        private void ResetBoard()
        {
            for (int i = 0; i < 9; i++)
            {
                board[i] = ' ';
                buttons[i].Text = "";
            }
        }
    }
}