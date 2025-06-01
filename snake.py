import pygame
import random
import sys
import socket
import pickle
import threading
from pathlib import Path

# Инициализация pygame
pygame.init()
pygame.mixer.init()

# Константы игры
SNAKE_BLOCK = 32
SCORE_PANEL_HEIGHT = 80
info = pygame.display.Info()
SCREEN_WIDTH = (info.current_w // SNAKE_BLOCK) * SNAKE_BLOCK
SCREEN_HEIGHT = (info.current_h // SNAKE_BLOCK) * SNAKE_BLOCK
GAME_AREA_TOP = SCORE_PANEL_HEIGHT
GAME_AREA_HEIGHT = SCREEN_HEIGHT - GAME_AREA_TOP
FPS = 10

# Цвета
WHITE = (255, 255, 255)
YELLOW = (255, 255, 102)
BLACK = (0, 0, 0)
GREEN = (0, 102, 0)
RED = (213, 50, 80)
BLUE = (51, 153, 255)
PURPLE = (128, 0, 128)
GRAY = (100, 100, 100)
DARK_GREEN = (14, 63, 14)

# Инициализация экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Snake II")

# Шрифты
font_btn = pygame.font.SysFont("comicsansms", 28)
font_score = pygame.font.SysFont("comicsansms", 30)
font_end = pygame.font.SysFont("comicsansms", 48)
font_leader = pygame.font.SysFont("comicsansms", 26)
clock = pygame.time.Clock()

# Пути к ресурсам
RESOURCES_DIR = Path(__file__).parent
IMAGES_DIR = RESOURCES_DIR / "images"
SOUNDS_DIR = RESOURCES_DIR / "sounds"

# Создание папок для ресурсов
IMAGES_DIR.mkdir(exist_ok=True)
SOUNDS_DIR.mkdir(exist_ok=True)

# Имена игроков
player1_name = "Игрок 1"
player2_name = "Игрок 2"


def load_image(path, size=None):
    # Загрузка изображения с обработкой ошибок
    try:
        full_path = IMAGES_DIR / path
        if not full_path.exists():
            raise FileNotFoundError(f"Image file not found: {full_path}")
        img = pygame.image.load(full_path)
        return pygame.transform.scale(img, size) if size else img
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
        surface = pygame.Surface((SNAKE_BLOCK, SNAKE_BLOCK))
        surface.fill(RED)
        return surface


def load_sound(path):
    # Загрузка звука с обработкой ошибок
    try:
        full_path = SOUNDS_DIR / path
        if not full_path.exists():
            raise FileNotFoundError(f"Sound file not found: {full_path}")
        return pygame.mixer.Sound(full_path)
    except Exception as e:
        print(f"Ошибка загрузки звука: {e}")
        return None


# Загрузка изображений и звуков
head_img = load_image("snake_head.png", (SNAKE_BLOCK, SNAKE_BLOCK))
head2_img = head_img.copy()
head2_img.fill(PURPLE, special_flags=pygame.BLEND_ADD)
body_img = load_image("snake_body.png", (SNAKE_BLOCK, SNAKE_BLOCK))
body2_img = body_img.copy()
body2_img.fill(PURPLE, special_flags=pygame.BLEND_ADD)
food_img = load_image("apple.png", (SNAKE_BLOCK, SNAKE_BLOCK))
background_img = load_image("background.png", (SCREEN_WIDTH, GAME_AREA_HEIGHT))

eat_sound = load_sound("eat.wav")
game_over_sound = load_sound("game_over.wav")
background_music = load_sound("background_music.mp3")


def draw_snake(snake_list, player=1):
    # Отрисовка змейки на экране
    for i, pos in enumerate(snake_list):
        if player == 1:
            image = head_img if i == len(snake_list) - 1 else body_img
        else:
            image = head2_img if i == len(snake_list) - 1 else body2_img
        screen.blit(image, (pos[0], pos[1]))


def your_score(score1, score2):
    # Отображение счета игроков
    pygame.draw.rect(screen, BLUE, (0, 0, SCREEN_WIDTH, SCORE_PANEL_HEIGHT))
    val1 = font_score.render(f"{player1_name}: {score1}", True, YELLOW)
    val2 = font_score.render(f"{player2_name}: {score2}", True, PURPLE)
    screen.blit(val1, (10, 10))
    screen.blit(val2, (SCREEN_WIDTH - 260, 10))


def new_food_position(snake1, snake2):
    # Генерация новой позиции для еды
    while True:
        x = random.randint(0, (SCREEN_WIDTH - SNAKE_BLOCK) // SNAKE_BLOCK) * SNAKE_BLOCK
        y = random.randint(GAME_AREA_TOP // SNAKE_BLOCK, (SCREEN_HEIGHT - SNAKE_BLOCK) // SNAKE_BLOCK) * SNAKE_BLOCK
        if [x, y] not in snake1 and [x, y] not in snake2:
            return [x, y]


def generate_random_position():
    # Генерация случайной позиции на поле
    x = random.randint(0, (SCREEN_WIDTH - SNAKE_BLOCK) // SNAKE_BLOCK) * SNAKE_BLOCK
    y = random.randint(GAME_AREA_TOP // SNAKE_BLOCK, (SCREEN_HEIGHT - SNAKE_BLOCK) // SNAKE_BLOCK) * SNAKE_BLOCK
    return [x, y]


def show_countdown(seconds):
    # Отображение обратного отсчета перед началом игры
    font = pygame.font.SysFont("comicsansms", 72)
    for i in range(seconds, 0, -1):
        screen.fill(BLACK)
        screen.blit(background_img, (0, GAME_AREA_TOP))
        text = font.render(str(i), True, YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text, text_rect)
        pygame.display.update()
        pygame.time.delay(1000)


class Button:
    # Класс для создания кнопок интерфейса
    def __init__(self, text, x, y, w, h, color, action):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.action = action

    def draw(self, surface):
        # Отрисовка кнопки
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
        txt = font_btn.render(self.text, True, BLACK)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        # Проверка клика по кнопке
        return self.rect.collidepoint(pos)


def save_score(winner, score):
    # Сохранение рекорда в файл
    try:
        highscores_file = RESOURCES_DIR / "highscores.txt"
        with open(highscores_file, "a", encoding="utf-8") as f:
            f.write(f"{winner}:{score}\n")
    except Exception as e:
        print(f"Ошибка сохранения счета: {e}")


def load_highscores():
    # Загрузка таблицы рекордов из файла
    try:
        highscores_file = RESOURCES_DIR / "highscores.txt"
        if highscores_file.exists():
            with open(highscores_file, "r", encoding="utf-8") as f:
                scores = []
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            winner, score = line.split(":")
                            scores.append((winner, int(score)))
                        except ValueError:
                            print(f"Неверный формат строки: {line}")
                return scores
    except Exception as e:
        print(f"Ошибка загрузки рекордов: {e}")
    return []


def clear_highscores():
    # Очистка таблицы рекордов
    try:
        highscores_file = RESOURCES_DIR / "highscores.txt"
        if highscores_file.exists():
            highscores_file.unlink()
    except Exception as e:
        print(f"Ошибка при очистке таблицы лидеров: {e}")


class Server:
    # Класс сервера для сетевой игры
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            if ip and ip != "localhost":
                socket.inet_aton(ip)
            self.sock.bind((ip, port))
        except socket.error as e:
            error_msg = f"Ошибка создания сервера: {e}"
            if "Cannot assign requested address" in str(e):
                error_msg = "Неверный IP-адрес для сервера"
            elif "Address already in use" in str(e):
                error_msg = "Порт уже занят"
            self.show_error_screen(error_msg)
            return
        except OverflowError:
            self.show_error_screen("Номер порта должен быть от 1 до 65535")
            return
        
        self.sock.listen(1)
        self.conn = None
        self.running = True
        self.receive_thread = None
        self.restart_requested = False
        
        self.wait_for_connection(ip, port)

    def wait_for_connection(self, ip, port):
        # Ожидание подключения клиента
        cancel_btn = Button("Отмена", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50, YELLOW, self.cancel_connection)
        
        while self.running and not self.conn:
            screen.fill(BLACK)
            screen.blit(background_img, (0, GAME_AREA_TOP))

            title = font_score.render("Ожидание подключения...", True, WHITE)
            ip_text = font_score.render(f"IP: {ip}", True, WHITE)
            port_text = font_score.render(f"Порт: {port}", True, WHITE)

            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 200)))
            screen.blit(ip_text, ip_text.get_rect(center=(SCREEN_WIDTH // 2, 250)))
            screen.blit(port_text, port_text.get_rect(center=(SCREEN_WIDTH // 2, 300)))
            
            cancel_btn.draw(screen)
            pygame.display.update()

            try:
                self.sock.settimeout(0.1)
                self.conn, addr = self.sock.accept()
                self.receive_thread = threading.Thread(target=self.receive_data, daemon=True)
                self.receive_thread.start()
                self.reset_game()
                clear_highscores()
                self.run()
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Ошибка подключения: {e}")
                self.running = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if cancel_btn.is_clicked(event.pos):
                        self.cancel_connection()
                        return

            clock.tick(30)

    def receive_data(self):
        # Получение данных от клиента
        while self.running and self.conn:
            try:
                data = self.conn.recv(1024)
                if not data:
                    break
                    
                message = pickle.loads(data)
                
                if isinstance(message, dict) and message.get("request_restart"):
                    self.restart_requested = True
                elif isinstance(message, list):
                    self.dir2 = message
            except (ConnectionError, pickle.UnpicklingError):
                break
            except Exception as e:
                print(f"Ошибка получения данных: {e}")
                continue

    def move(self, snake, direction):
        # Движение змейки
        head = [snake[-1][0] + direction[0], snake[-1][1] + direction[1]]
        snake.append(head)
        if head == self.food:
            if snake == self.snake1:
                self.score1 += 1
            else:
                self.score2 += 1
            if eat_sound:
                eat_sound.play()
            self.food = new_food_position(self.snake1, self.snake2)
        else:
            snake.pop(0)

    def check_collision(self, snake, other_snake=None):
        # Проверка столкновений змейки
        head = snake[-1]
        if (head[0] < 0 or head[0] >= SCREEN_WIDTH or
            head[1] < GAME_AREA_TOP or head[1] >= SCREEN_HEIGHT):
            return True
        
        if head in snake[:-1]:
            return True
        
        if other_snake and head in other_snake:
            return True
            
        return False

    def reset_game(self):
        # Сброс состояния игры
        self.snake1 = [generate_random_position()]
        self.snake2 = [generate_random_position()]
        self.dir1 = [SNAKE_BLOCK, 0]
        self.dir2 = [-SNAKE_BLOCK, 0]
        self.score1 = 0
        self.score2 = 0
        self.food = new_food_position(self.snake1, self.snake2)
        self.winner = None
        self.game_over = False
        self.restart_requested = False

    def show_game_over_screen(self, winner=None, score=None):
        # Отображение экрана окончания игры
        if background_music and background_music.get_num_channels() > 0:
            background_music.stop()
        if game_over_sound:
            game_over_sound.play()

        elements = []
        if winner:
            win_text = font_end.render(f"Победил {winner}!", True, YELLOW)
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, 150))
            elements.append((win_text, win_rect))

            score_text = font_score.render(f"Очки: {score}", True, YELLOW)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 200))
            elements.append((score_text, score_rect))

        highscores = load_highscores()
        if highscores:
            top_text = font_score.render("Топ игроков:", True, WHITE)
            top_rect = top_text.get_rect(center=(SCREEN_WIDTH//2, 250))
            elements.append((top_text, top_rect))

            for i, (win, s) in enumerate(highscores[:5]):
                entry = font_leader.render(f"{i+1}. {win} - {s}", True, WHITE)
                entry_rect = entry.get_rect(center=(SCREEN_WIDTH//2, 300 + i*30))
                elements.append((entry, entry_rect))

        exit_btn = Button("Выход", SCREEN_WIDTH//2 + 20, SCREEN_HEIGHT - 150, 200, 50, RED, self.exit_to_menu)

        alpha = 0
        fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade_surface.fill(BLACK)

        waiting = True

        while waiting and self.running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        return
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                            exit_btn.is_clicked(event.pos)
                            exit_btn.action()
                            waiting = False

                if self.restart_requested:
                    self.restart_game()
                    waiting = False

                alpha = min(alpha + 5, 255)
                fade_surface.set_alpha(255 - alpha)
                screen.fill(BLACK)
                screen.blit(background_img, (0, GAME_AREA_TOP))

                for element, rect in elements:
                    element.set_alpha(alpha)
                    screen.blit(element, rect)

                exit_btn.draw(screen)
                screen.blit(fade_surface, (0, 0))

                pygame.display.flip()
                clock.tick(30)
            except pygame.error:
                self.running = False
                return

    def restart_game(self):
        # Перезапуск игры
        self.reset_game()
        if self.conn:
            try:
                self.conn.sendall(pickle.dumps({"restart": True}))
            except ConnectionError:
                print("Не удалось отправить команду перезапуска клиенту")
        self.run()

    def exit_to_menu(self):
        # Выход в главное меню
        self.safe_close()
        main_menu()

    def run(self):
        # Основной игровой цикл сервера
        if not self.conn:
            return
        
        screen.fill(BLACK)
        pygame.display.update()
        
        show_countdown(3)
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP and self.dir1 != [0, SNAKE_BLOCK]:
                        self.dir1 = [0, -SNAKE_BLOCK]
                    elif event.key == pygame.K_DOWN and self.dir1 != [0, -SNAKE_BLOCK]:
                        self.dir1 = [0, SNAKE_BLOCK]
                    elif event.key == pygame.K_LEFT and self.dir1 != [SNAKE_BLOCK, 0]:
                        self.dir1 = [-SNAKE_BLOCK, 0]
                    elif event.key == pygame.K_RIGHT and self.dir1 != [-SNAKE_BLOCK, 0]:
                        self.dir1 = [SNAKE_BLOCK, 0]

            if not self.game_over:
                self.move(self.snake1, self.dir1)
                self.move(self.snake2, self.dir2)

                snake1_collision = self.check_collision(self.snake1, self.snake2)
                snake2_collision = self.check_collision(self.snake2, self.snake1)
                
                if snake1_collision and snake2_collision:
                    self.game_over = True
                    self.winner = "Ничья"
                elif snake1_collision:
                    self.game_over = True
                    self.winner = player2_name
                elif snake2_collision:
                    self.game_over = True
                    self.winner = player1_name

                try:
                    state = {
                        "snake1": self.snake1,
                        "snake2": self.snake2,
                        "food": self.food,
                        "score1": self.score1,
                        "score2": self.score2,
                        "winner": self.winner,
                        "game_over": self.game_over,
                        "restart": False
                    }
                    self.conn.sendall(pickle.dumps(state))
                except ConnectionError:
                    self.running = False
                    break

            screen.fill(BLACK)
            screen.blit(background_img, (0, GAME_AREA_TOP))
            your_score(self.score1, self.score2)
            draw_snake(self.snake1, 1)
            draw_snake(self.snake2, 2)
            screen.blit(food_img, self.food)
            pygame.display.update()
            clock.tick(FPS)

            if self.game_over:
                if self.winner != "Ничья?":
                    save_score(self.winner, max(self.score1, self.score2))
                self.show_game_over_screen(self.winner, max(self.score1, self.score2))
                break

    def cancel_connection(self):
        # Отмена подключения
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        try:
            self.sock.close()
        except:
            pass
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)
        main_menu()

    def safe_close(self):
        # Безопасное закрытие соединений
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.running = False

    def show_error_screen(self, msg):
        # Отображение экрана с ошибкой
        screen.fill(BLACK)
        screen.blit(background_img, (0, GAME_AREA_TOP))
        
        error_text = font_end.render("Ошибка подключения", True, RED)
        msg_text = font_score.render(msg, True, WHITE)
        back_text = font_score.render("Нажмите любую клавишу для возврата в меню", True, YELLOW)
        
        screen.blit(error_text, error_text.get_rect(center=(SCREEN_WIDTH//2, 200)))
        screen.blit(msg_text, msg_text.get_rect(center=(SCREEN_WIDTH//2, 300)))
        screen.blit(back_text, back_text.get_rect(center=(SCREEN_WIDTH//2, 400)))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        
        main_menu()


class Client:
    # Класс клиента для сетевой игры
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = None
        self.running = False
        self.error_msg = ""
        self.connect()

    def connect(self):
        # Подключение к серверу
        try:
            if self.ip and self.ip != "localhost":
                socket.inet_aton(self.ip)
                
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.ip, self.port))
            self.sock.settimeout(None)
            self.direction = [SNAKE_BLOCK, 0]
            self.running = True
            self.game_over = False
            return True
            
        except socket.timeout as e:
            self.error_msg = "Таймаут подключения: сервер не отвечает"
        except ConnectionRefusedError:
            self.error_msg = "Сервер отклонил подключение"
        except Exception as e:
            self.error_msg = f"Ошибка подключения: {str(e)}"
        
        return False

    def run(self):
        # Основной игровой цикл клиента
        if not self.running or not self.sock:
            self.show_error_screen()
            return
        
        show_countdown(3)
        
        while self.running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP and self.direction != [0, SNAKE_BLOCK]:
                            self.direction = [0, -SNAKE_BLOCK]
                        elif event.key == pygame.K_DOWN and self.direction != [0, -SNAKE_BLOCK]:
                            self.direction = [0, SNAKE_BLOCK]
                        elif event.key == pygame.K_LEFT and self.direction != [SNAKE_BLOCK, 0]:
                            self.direction = [-SNAKE_BLOCK, 0]
                        elif event.key == pygame.K_RIGHT and self.direction != [-SNAKE_BLOCK, 0]:
                            self.direction = [SNAKE_BLOCK, 0]
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()

                if not self.game_over and self.direction:
                    self.sock.sendall(pickle.dumps(self.direction))
                
                data = self.sock.recv(4096)
                if not data:
                    self.error_msg = "Соединение с сервером разорвано"
                    self.running = False
                    break
                    
                received = pickle.loads(data)
                
                if isinstance(received, dict):
                    if received.get("restart", False):
                        self.game_over = False
                        continue
                        
                    self.state = received
                    self.game_over = self.state.get("game_over", False)

                screen.fill(BLACK)
                screen.blit(background_img, (0, GAME_AREA_TOP))
                your_score(self.state.get("score1", 0), self.state.get("score2", 0))
                draw_snake(self.state.get("snake1", []), 1)
                draw_snake(self.state.get("snake2", []), 2)
                screen.blit(food_img, self.state.get("food", [0, 0]))
                pygame.display.update()
                clock.tick(FPS)

                if self.game_over:
                    if game_over_sound:
                        game_over_sound.play()
                    winner = self.state.get("winner")
                    score = self.state.get("score2", 0) if winner == player2_name else self.state.get("score1", 0)
                    self.show_game_over_screen(winner, score)
                    self.running = False
                    break
                    
            except (ConnectionError, pickle.UnpicklingError):
                self.error_msg = "Ошибка соединения с сервером"
                self.running = False
                break
            except Exception as e:
                print(f"Ошибка в клиенте: {e}")
                self.error_msg = "Неизвестная ошибка"
                self.running = False
                break

        if self.sock:
            try:
                self.sock.close()
            except:
                pass

    def show_game_over_screen(self, winner=None, score=None):
        # Отображение экрана окончания игры
        if background_music and background_music.get_num_channels() > 0:
            background_music.stop()
        if game_over_sound:
            game_over_sound.play()

        elements = []
        if winner:
            win_text = font_end.render(f"Победил {winner}!", True, YELLOW)
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, 150))
            elements.append((win_text, win_rect))

            score_text = font_score.render(f"Очки: {score}", True, YELLOW)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 200))
            elements.append((score_text, score_rect))

        highscores = load_highscores()
        if highscores:
            top_text = font_score.render("Топ игроков:", True, WHITE)
            top_rect = top_text.get_rect(center=(SCREEN_WIDTH//2, 250))
            elements.append((top_text, top_rect))

            for i, (win, s) in enumerate(highscores[:5]):
                entry = font_leader.render(f"{i+1}. {win} - {s}", True, WHITE)
                entry_rect = entry.get_rect(center=(SCREEN_WIDTH//2, 300 + i*30))
                elements.append((entry, entry_rect))

        request_btn = Button("Запросить перезапуск", SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT - 150, 320, 50, GREEN, self.request_restart)
        exit_btn = Button("Выход", SCREEN_WIDTH//2 + 90, SCREEN_HEIGHT - 150, 200, 50, RED, self.exit_to_menu)

        alpha = 0
        fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade_surface.fill(BLACK)

        waiting = True

        while waiting:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        waiting = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        if request_btn.is_clicked(pos):
                            request_btn.action()
                        elif exit_btn.is_clicked(pos):
                            exit_btn.action()
                            waiting = False

                alpha = min(alpha + 5, 255)
                fade_surface.set_alpha(255 - alpha)
                screen.fill(BLACK)
                screen.blit(background_img, (0, GAME_AREA_TOP))

                for element, rect in elements:
                    element.set_alpha(alpha)
                    screen.blit(element, rect)

                request_btn.draw(screen)
                exit_btn.draw(screen)
                screen.blit(fade_surface, (0, 0))

                pygame.display.flip()
                clock.tick(30)
            except pygame.error:
                self.running = False
                waiting = False

    def request_restart(self):
        # Запрос перезапуска игры у сервера
        if self.sock:
            try:
                self.sock.sendall(pickle.dumps({"request_restart": True}))
                self.show_waiting_message()
            except ConnectionError:
                self.error_msg = "Не удалось отправить запрос серверу"
                self.show_error_screen()

    def show_waiting_message(self):
        # Отображение сообщения об ожидании
        screen.fill(BLACK)
        screen.blit(background_img, (0, GAME_AREA_TOP))
        
        waiting_text = font_end.render("Ожидание сервера...", True, YELLOW)
        info_text = font_score.render("Сервер должен подтвердить перезапуск", True, WHITE)
        
        screen.blit(waiting_text, waiting_text.get_rect(center=(SCREEN_WIDTH//2, 200)))
        screen.blit(info_text, info_text.get_rect(center=(SCREEN_WIDTH//2, 250)))
        
        pygame.display.flip()
        
        waiting = True
        while waiting and self.running:
            try:
                data = self.sock.recv(1024)
                if data:
                    received = pickle.loads(data)
                    if isinstance(received, dict) and received.get("restart", False):
                        waiting = False
                        self.game_over = False
                        self.run()
                        return
            except:
                waiting = False
        
        self.error_msg = "Сервер не ответил на запрос"
        self.show_error_screen()

    def exit_to_menu(self):
        # Выход в главное меню
        self.safe_close()
        main_menu()

    def safe_close(self):
        # Безопасное закрытие соединения
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.running = False

    def show_error_screen(self):
        # Отображение экрана с ошибкой
        screen.fill(BLACK)
        screen.blit(background_img, (0, GAME_AREA_TOP))
        
        error_text = font_end.render("Ошибка подключения", True, RED)
        msg_text = font_score.render(self.error_msg, True, WHITE)
        back_text = font_score.render("Нажмите любую клавишу для возврата в меню", True, YELLOW)
        
        screen.blit(error_text, error_text.get_rect(center=(SCREEN_WIDTH//2, 200)))
        screen.blit(msg_text, msg_text.get_rect(center=(SCREEN_WIDTH//2, 300)))
        screen.blit(back_text, back_text.get_rect(center=(SCREEN_WIDTH//2, 400)))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        
        main_menu()


def input_ip_port(mode="server"):
    # Ввод IP и порта для подключения
    ip, port, active = "", "", "ip"
    input_rects = {
        "ip": pygame.Rect(SCREEN_WIDTH // 2 - 150, 280, 300, 50),
        "port": pygame.Rect(SCREEN_WIDTH // 2 - 150, 360, 300, 50)
    }
    back_btn = Button("Назад", SCREEN_WIDTH // 2 - 75, 430, 150, 50, YELLOW, lambda: (None, None))
    error_msg = ""

    while True:
        screen.fill(BLACK)
        screen.blit(background_img, (0, GAME_AREA_TOP))

        if mode == "server":
            label = font_score.render("Введите параметры для создания сервера", True, YELLOW)
        else:
            label = font_score.render("Введите параметры для подключения", True, YELLOW)
        screen.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, 180)))

        if error_msg:
            error_text = font_score.render(error_msg, True, RED)
            screen.blit(error_text, error_text.get_rect(center=(SCREEN_WIDTH // 2, 220)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if active == "ip":
                        active = "port"
                    elif ip and port:
                        if mode == "client":
                            try:
                                if ip != "localhost":
                                    socket.inet_aton(ip)
                            except socket.error:
                                error_msg = "Неверный формат IP-адреса (пример: 192.168.1.1)"
                                continue
                        
                        try:
                            port_num = int(port)
                            if not 0 < port_num <= 65535:
                                error_msg = "Порт должен быть от 1 до 65535"
                                continue
                            return ip, port_num
                        except ValueError:
                            error_msg = "Порт должен быть числом"
                            continue
                elif event.key == pygame.K_BACKSPACE:
                    if active == "ip":
                        ip = ip[:-1]
                    elif active == "port":
                        port = port[:-1]
                    error_msg = ""
                else:
                    if active == "ip":
                        if event.unicode.isdigit() or event.unicode == '.' or (not ip and event.unicode.isalpha()):
                            ip += event.unicode
                    elif active == "port" and event.unicode.isdigit():
                        port += event.unicode
                    error_msg = ""
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_rects["ip"].collidepoint(event.pos):
                    active = "ip"
                elif input_rects["port"].collidepoint(event.pos):
                    active = "port"
                elif back_btn.is_clicked(event.pos):
                    return None, None

        pygame.draw.rect(screen, DARK_GREEN, input_rects["ip"])
        pygame.draw.rect(screen, DARK_GREEN, input_rects["port"])

        if active == "ip":
            pygame.draw.rect(screen, WHITE, input_rects["ip"], 2)
        else:
            pygame.draw.rect(screen, WHITE, input_rects["port"], 2)

        screen.blit(font_score.render("IP:", True, WHITE), (input_rects["ip"].x - 70, input_rects["ip"].y + 10))
        screen.blit(font_score.render(ip, True, WHITE), (input_rects["ip"].x + 10, input_rects["ip"].y + 10))
        screen.blit(font_score.render("Порт:", True, WHITE), (input_rects["port"].x - 112, input_rects["port"].y + 10))
        screen.blit(font_score.render(port, True, WHITE), (input_rects["port"].x + 10, input_rects["port"].y + 10))

        back_btn.draw(screen)
        pygame.display.update()
        clock.tick(30)


def network_game_menu():
    # Меню сетевой игры
    buttons = []
    w, h = 300, 70
    x = SCREEN_WIDTH // 2 - w // 2
    y = SCREEN_HEIGHT // 2 - h * 2
    buttons.append(Button("Создать сервер", x, y, w, h, GREEN, start_server_menu))
    buttons.append(Button("Подключиться", x, y + 90, w, h, GREEN, start_client_menu))
    buttons.append(Button("Назад", x, y + 180, w, h, YELLOW, main_menu))

    while True:
        screen.fill(BLACK)
        screen.blit(background_img, (0, GAME_AREA_TOP))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.is_clicked(event.pos):
                        btn.action()
                        return

        for btn in buttons:
            btn.draw(screen)
        pygame.display.update()
        clock.tick(30)


def start_server_menu():
    # Запуск сервера
    ip, port = input_ip_port("server")
    if ip is None and port is None:
        network_game_menu()
    elif ip is not None and port is not None:
        server = Server(ip, port)
        if server.running and hasattr(server, 'conn') and server.conn:
            server.run()


def start_client_menu():
    # Подключение к серверу
    ip, port = input_ip_port("client")
    if ip is None and port is None:
        network_game_menu()
    elif ip is not None and port is not None:
        client = Client(ip, port)
        if client.running:
            client.run()


def main_menu():
    # Главное меню игры
    if background_music:
        background_music.play(loops=-1)
    buttons = []
    w, h = 300, 70
    x = SCREEN_WIDTH // 2 - w // 2
    y = SCREEN_HEIGHT // 2 - h
    buttons.append(Button("Играть", x, y, w, h, GREEN, network_game_menu))
    buttons.append(Button("Выход", x, y + 90, w, h, RED, lambda: sys.exit()))

    while True:
        screen.fill(BLACK)
        screen.blit(background_img, (0, GAME_AREA_TOP))
        title = font_score.render("SnaKE II", True, YELLOW)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.is_clicked(event.pos):
                        if background_music:
                            background_music.stop()
                        btn.action()
                        return

        for btn in buttons:
            btn.draw(screen)
        pygame.display.update()
        clock.tick(30)


if __name__ == "__main__":
    main_menu()