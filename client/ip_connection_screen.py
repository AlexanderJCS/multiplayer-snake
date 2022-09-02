import pygame

pygame.init()

COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
FONT = pygame.font.SysFont("Calibri Light", 30, (255, 255, 255))


class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            self.active = not self.active if self.rect.collidepoint(event.pos) else False

            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]

            else:
                self.text += event.unicode

            # Re-render the text.
            self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_text(self):
        return self.text


class IPConnectionScreen:
    def __init__(self, surface, width, player_offset):
        self.surface = surface

        self.width = width
        self.player_offset = player_offset

        self.ip_text = FONT.render("IP:", True, (255, 255, 255))
        self.ip_text_rect = self.ip_text.get_rect()
        self.ip_text_rect.center = (self.width // 2, self.player_offset)

        self.ip_input = InputBox(self.width // 2 - 100, self.player_offset + 20, 200, 40)

        self.port_text = FONT.render("Port:", True, (255, 255, 255))
        self.port_text_rect = self.port_text.get_rect()
        self.port_text_rect.center = (self.width // 2, self.player_offset + 180)

        self.port_input = InputBox(self.width // 2 - 100, self.player_offset + 200, 200, 40)

    def draw(self):
        self.surface.fill((0, 0, 0))

        self.surface.blit(self.ip_text, self.ip_text_rect)
        self.surface.blit(self.port_text, self.port_text_rect)

        self.ip_input.draw(self.surface)
        self.port_input.draw(self.surface)
        pygame.display.update()

    def run(self):
        while True:
            events = pygame.event.get()

            for event in events:
                if event == pygame.QUIT:
                    pygame.quit()
                    exit()

                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    return self.ip_input.get_text(), self.port_input.get_text()

                self.ip_input.handle_event(event)
                self.port_input.handle_event(event)

            self.draw()

            pygame.time.wait(1 // 60)
