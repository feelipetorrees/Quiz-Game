import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Quiz, Player, Question, Answer

class QuizConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_code = None
        self.quiz = None
        self.player = None
        self.room_group_name = None

    async def connect(self):
        self.quiz_code = self.scope['url_route']['kwargs']['quiz_code']
        self.room_group_name = f'quiz_{self.quiz_code}'
        
        # ✅ ACEITA a conexão primeiro (evita 403)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # ✅ DEPOIS busca/cria o quiz
        self.quiz = await self.get_or_create_quiz()

    async def disconnect(self, close_code):
        if self.player:
            await self.set_player_offline()
            
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'join':
                await self.handle_join(data)
            elif action == 'start_quiz':
                await self.handle_start_quiz()
            elif action == 'answer':
                await self.handle_answer(data)
                
        except json.JSONDecodeError:
            await self.send_error("JSON inválido")

    async def handle_join(self, data):
        username = data.get('username', '').strip()
        if not username:
            await self.send_error("Nome de usuário é obrigatório")
            return
        
        self.player = await self.create_player(username)
        if not self.player:
            await self.send_error("Erro ao entrar na sala")
            return
        
        # Notificar todos os jogadores
        players = await self.get_room_players()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_joined',
                'player': {
                    'username': self.player.username,
                    'score': self.player.score
                },
                'players': players
            }
        )

    async def handle_start_quiz(self):
        questions = await self.get_quiz_questions()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'quiz_started',
                'questions': questions
            }
        )

    async def handle_answer(self, data):
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        
        is_correct = await self.check_answer(question_id, answer_id)
        if is_correct:
            await self.update_player_score(10)
        
        await self.send(text_data=json.dumps({
            'type': 'answer_result',
            'is_correct': is_correct,
            'score': self.player.score if self.player else 0
        }))

    async def player_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'player': event['player'],
            'players': event['players']
        }))

    async def quiz_started(self, event):
        await self.send(text_data=json.dumps({
            'type': 'quiz_started',
            'questions': event['questions']
        }))

    # ✅ FUNÇÃO QUE FALTAVA - get_or_create_quiz
    @database_sync_to_async
    def get_or_create_quiz(self):
        try:
            quiz, created = Quiz.objects.get_or_create(
                code=self.quiz_code,
                defaults={'title': f'Quiz {self.quiz_code}'}
            )
            return quiz
        except Exception as e:
            print(f"Erro ao criar quiz: {e}")
            return None

    @database_sync_to_async
    def create_player(self, username):
        try:
            player, created = Player.objects.get_or_create(
                quiz=self.quiz,
                username=username,
                defaults={'is_online': True, 'session_id': str(uuid.uuid4())}
            )
            if not created:
                player.is_online = True
                player.session_id = str(uuid.uuid4())
                player.save()
            return player
        except Exception as e:
            print(f"Erro ao criar player: {e}")
            return None

    @database_sync_to_async
    def set_player_offline(self):
        if self.player:
            self.player.is_online = False
            self.player.save()

    @database_sync_to_async
    def get_room_players(self):
        players = Player.objects.filter(quiz=self.quiz, is_online=True)
        return [
            {
                'username': player.username,
                'score': player.score
            }
            for player in players
        ]

    @database_sync_to_async
    def get_quiz_questions(self):
        questions = Question.objects.filter(quiz=self.quiz)
        result = []
        for question in questions:
            answers = Answer.objects.filter(question=question)
            result.append({
                'id': question.id,
                'text': question.text,
                'time_limit': question.time_limit,
                'answers': [
                    {
                        'id': answer.id,
                        'text': answer.text,
                        'is_correct': answer.is_correct
                    }
                    for answer in answers
                ]
            })
        return result

    @database_sync_to_async
    def check_answer(self, question_id, answer_id):
        try:
            answer = Answer.objects.get(id=answer_id, question_id=question_id)
            return answer.is_correct
        except Answer.DoesNotExist:
            return False

    @database_sync_to_async
    def update_player_score(self, points):
        if self.player:
            self.player.score += points
            self.player.save()

    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))