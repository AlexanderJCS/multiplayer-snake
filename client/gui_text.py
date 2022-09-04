

class Text:
    def __init__(self, message, font, color, pos):
        self.font = font
        self.color = color

        self.text = self.font.render(message, True, color)
        self.rect = self.text.get_rect()
        self.rect.center = pos

    def draw(self, surface):
        surface.blit(self.text, self.rect)
