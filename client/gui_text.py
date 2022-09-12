

class Text:
    def __init__(self, message, font, color, pos):
        self.font = font
        self.color = color
        self.pos = pos

        self.text = self.font.render(message, True, self.color)
        self.rect = self.text.get_rect()
        self.rect.center = self.pos

    def draw(self, surface):
        surface.blit(self.text, self.rect)

    def change_text(self, new_text):
        self.text = self.font.render(new_text, True, self.color)
        self.rect = self.text.get_rect()
        self.rect.center = self.pos
