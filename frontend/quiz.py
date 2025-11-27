import tkinter as tk
from tkinter import ttk, messagebox
import json
import websocket
import threading
import time

class QuizClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Game - Cliente")
        self.root.geometry("800x600")
        
        self.ws = None
        self.quiz_code = None
        self.username = None
        self.current_question = None
        
        self.setup_styles()
        self.create_main_frame()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Button.TButton', font=('Arial', 10))
        style.configure('Answer.TButton', font=('Arial', 10), width=30)

    def create_main_frame(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Título
        title_label = ttk.Label(self.main_frame, text="🎮 Quiz Game", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        self.show_connection_screen()

    def show_connection_screen(self):
        self.clear_frame()
        
        # Entrada do código do quiz
        ttk.Label(self.main_frame, text="Código da Sala:", style='Subtitle.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quiz_code_entry = ttk.Entry(self.main_frame, font=('Arial', 12), width=15)
        self.quiz_code_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Entrada do username
        ttk.Label(self.main_frame, text="Seu Nome:", style='Subtitle.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(self.main_frame, font=('Arial', 12), width=20)
        self.username_entry.bind('<Return>', lambda e: self.connect_to_quiz())
        self.username_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Botão conectar
        connect_btn = ttk.Button(self.main_frame, text="Entrar na Sala", 
                               command=self.connect_to_quiz, style='Button.TButton')
        connect_btn.grid(row=3, column=0, columnspan=2, pady=20)

    def connect_to_quiz(self):
        self.quiz_code = self.quiz_code_entry.get().strip().upper()
        self.username = self.username_entry.get().strip()
        
        if not self.quiz_code:
            messagebox.showerror("Erro", "Digite o código da sala!")
            return
        if not self.username:
            messagebox.showerror("Erro", "Digite seu nome!")
            return
        
        try:
            # Conectar ao WebSocket
            self.ws = websocket.WebSocketApp(
                f"ws://localhost:8000/ws/quiz/{self.quiz_code}/",
                on_open=self.on_ws_open,
                on_message=self.on_ws_message,
                on_error=self.on_ws_error,
                on_close=self.on_ws_close
            )
            
            # Executar em thread separada
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Mostrar loading
            self.show_loading_screen("Conectando à sala...")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar: {e}")

    def on_ws_open(self, ws):
        # Enviar mensagem de join após conectar
        join_message = {
            'action': 'join',
            'username': self.username
        }
        ws.send(json.dumps(join_message))
        
        # Atualizar UI na thread principal
        self.root.after(0, self.show_lobby_screen)

    def on_ws_message(self, ws, message):
        data = json.loads(message)
        message_type = data.get('type')
        
        print(f"Mensagem recebida: {data}")  # Debug
        
        if message_type == 'player_joined':
            self.root.after(0, lambda: self.update_players_list(data['players']))
        elif message_type == 'quiz_started':
            self.root.after(0, lambda: self.show_question_screen(data['questions']))
        elif message_type == 'answer_result':
            self.root.after(0, lambda: self.show_answer_result(data))
        elif message_type == 'error':
            self.root.after(0, lambda: messagebox.showerror("Erro", data['message']))

    def on_ws_error(self, ws, error):
        self.root.after(0, lambda: messagebox.showerror("Erro WebSocket", str(error)))

    def on_ws_close(self, ws, close_status_code, close_msg):
        self.root.after(0, lambda: messagebox.showinfo("Conexão", "Desconectado do servidor"))

    def show_loading_screen(self, message):
        self.clear_frame()
        ttk.Label(self.main_frame, text=message, style='Subtitle.TLabel').grid(row=1, column=0, pady=20)

    def show_lobby_screen(self):
        self.clear_frame()
        
        # Header
        ttk.Label(self.main_frame, text=f"Sala: {self.quiz_code}", style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(self.main_frame, text=f"Jogador: {self.username}", style='Subtitle.TLabel').grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Lista de jogadores
        ttk.Label(self.main_frame, text="Jogadores na Sala:", style='Subtitle.TLabel').grid(row=2, column=0, sticky=tk.W, pady=10)
        
        # Frame para a lista de jogadores
        players_frame = ttk.Frame(self.main_frame)
        players_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.players_tree = ttk.Treeview(players_frame, columns=('score',), show='headings', height=8)
        self.players_tree.heading('#0', text='Jogador')
        self.players_tree.heading('score', text='Pontuação')
        self.players_tree.column('#0', width=200)
        self.players_tree.column('score', width=100)
        self.players_tree.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Scrollbar para a lista
        scrollbar = ttk.Scrollbar(players_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.players_tree.configure(yscrollcommand=scrollbar.set)
        
        # Botões
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Apenas o host pode iniciar o quiz (primeiro jogador)
        if len(self.players_tree.get_children()) == 1:  # Se é o primeiro jogador
            start_btn = ttk.Button(button_frame, text="Iniciar Quiz", 
                                 command=self.start_quiz, style='Button.TButton')
            start_btn.grid(row=0, column=0, padx=10)
        
        leave_btn = ttk.Button(button_frame, text="Sair da Sala", 
                             command=self.leave_room, style='Button.TButton')
        leave_btn.grid(row=0, column=1, padx=10)

    def update_players_list(self, players):
        # Limpar lista atual
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)
        
        # Adicionar jogadores
        for player in players:
            self.players_tree.insert('', 'end', text=player['username'], values=(player['score'],))

    def start_quiz(self):
        start_message = {
            'action': 'start_quiz'
        }
        self.ws.send(json.dumps(start_message))

    def show_question_screen(self, questions):
        self.clear_frame()
        
        if not questions:
            messagebox.showerror("Erro", "Nenhuma questão disponível!")
            return
        
        self.questions = questions
        self.current_question_index = 0
        self.show_current_question()

    def show_current_question(self):
        self.clear_frame()
        
        question = self.questions[self.current_question_index]
        self.current_question = question
        
        # Header
        ttk.Label(self.main_frame, text=f"Questão {self.current_question_index + 1}/{len(self.questions)}", 
                 style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Pergunta
        question_text = tk.Text(self.main_frame, wrap=tk.WORD, width=60, height=4, 
                               font=('Arial', 11), bg=self.root.cget('bg'), relief='flat')
        question_text.insert('1.0', question['text'])
        question_text.config(state='disabled')
        question_text.grid(row=1, column=0, columnspan=2, pady=10, padx=20)
        
        # Respostas
        for i, answer in enumerate(question['answers']):
            btn = ttk.Button(self.main_frame, text=answer['text'], 
                           command=lambda a=answer: self.submit_answer(a),
                           style='Answer.TButton')
            btn.grid(row=2+i, column=0, columnspan=2, pady=5, padx=50)

    def submit_answer(self, answer):
        answer_message = {
            'action': 'answer',
            'question_id': self.current_question['id'],
            'answer_id': answer['id']
        }
        self.ws.send(json.dumps(answer_message))

    def show_answer_result(self, data):
        result_window = tk.Toplevel(self.root)
        result_window.title("Resultado")
        result_window.geometry("300x200")
        result_window.transient(self.root)
        result_window.grab_set()
        
        if data['is_correct']:
            ttk.Label(result_window, text="✅ Resposta Correta!", style='Title.TLabel').pack(pady=20)
            ttk.Label(result_window, text="+10 pontos!").pack(pady=5)
        else:
            ttk.Label(result_window, text="❌ Resposta Incorreta", style='Title.TLabel').pack(pady=20)
        
        ttk.Label(result_window, text=f"Pontuação: {data['score']}").pack(pady=10)
        
        # Próxima questão após 3 segundos
        def next_question():
            result_window.destroy()
            self.current_question_index += 1
            if self.current_question_index < len(self.questions):
                self.show_current_question()
            else:
                self.show_quiz_completed()
        
        result_window.after(3000, next_question)

    def show_quiz_completed(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="🎉 Quiz Concluído!", style='Title.TLabel').grid(row=0, column=0, pady=20)
        ttk.Label(self.main_frame, text="Obrigado por jogar!").grid(row=1, column=0, pady=10)
        
        back_btn = ttk.Button(self.main_frame, text="Voltar ao Início", 
                            command=self.show_connection_screen, style='Button.TButton')
        back_btn.grid(row=2, column=0, pady=20)

    def leave_room(self):
        if self.ws:
            self.ws.close()
        self.show_connection_screen()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = QuizClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()