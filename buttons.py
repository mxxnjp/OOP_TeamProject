"""9강 'PyGame with OOP: Button'의 SimpleButton을 우리 게임에 맞게 옮긴 버튼 클래스.

강의와 같은 구조:
  - 상태 3개: STATE_NORMAL(기본) / STATE_HOVER(마우스가 위에) / STATE_ACTIVE(누르는 중)
  - handleEvent(eventObj): MOUSEMOTION / MOUSEBUTTONDOWN / MOUSEBUTTONUP 으로 상태를 바꾸고,
    버튼 위에서 눌렀다 뗐을 때만 True (= 클릭) + 콜백 실행
  - draw(): 상태에 따라 다른 그림(surfaceUp / surfaceOn / surfaceDown)을 blit
"""
import pygame


class SimpleButton:
    STATE_NORMAL = "normal"
    STATE_HOVER = "hover"
    STATE_ACTIVE = "active"

    def __init__(self, window, loc, surfaceUp, surfaceOn=None, surfaceDown=None, callBack=None):
        self.window = window
        self.loc = loc
        self.surfaceUp = surfaceUp                    # 기본 그림
        self.surfaceOn = surfaceOn or surfaceUp       # 마우스를 올렸을 때 그림
        self.surfaceDown = surfaceDown or self.surfaceOn   # 누르고 있을 때 그림
        self.callBack = callBack                      # 클릭되면 실행할 함수 (강의 Callback 부분)
        self.rect = surfaceUp.get_rect(topleft=loc)   # 마우스가 버튼 위인지 판단하는 Rect
        self.state = SimpleButton.STATE_NORMAL
        if self.rect.collidepoint(pygame.mouse.get_pos()):   # 화면이 열릴 때 이미 마우스가 위에 있으면
            self.state = SimpleButton.STATE_HOVER

    def handleEvent(self, eventObj):
        if eventObj.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
            return False
        if eventObj.type != pygame.MOUSEMOTION and eventObj.button > 3:   # 마우스 휠은 무시
            return False

        eventPointInButtonRect = self.rect.collidepoint(eventObj.pos)

        if self.state == SimpleButton.STATE_NORMAL:
            if eventPointInButtonRect:
                self.state = (SimpleButton.STATE_ACTIVE if eventObj.type == pygame.MOUSEBUTTONDOWN
                              else SimpleButton.STATE_HOVER)

        elif self.state == SimpleButton.STATE_HOVER:
            if not eventPointInButtonRect:
                self.state = SimpleButton.STATE_NORMAL
            elif eventObj.type == pygame.MOUSEBUTTONDOWN:
                self.state = SimpleButton.STATE_ACTIVE           # Normal/Hover -> Active

        elif self.state == SimpleButton.STATE_ACTIVE:
            if eventObj.type == pygame.MOUSEBUTTONUP:
                self.state = SimpleButton.STATE_HOVER if eventPointInButtonRect else SimpleButton.STATE_NORMAL
                if eventPointInButtonRect:                       # 버튼 위에서 뗐다 = 클릭!
                    if self.callBack:
                        self.callBack()
                    return True
            elif eventObj.type == pygame.MOUSEMOTION and not eventPointInButtonRect:
                self.state = SimpleButton.STATE_NORMAL

        return False

    def current_surface(self):
        if self.state == SimpleButton.STATE_ACTIVE:
            return self.surfaceDown
        if self.state == SimpleButton.STATE_HOVER:
            return self.surfaceOn
        return self.surfaceUp

    def draw_rect(self):
        """지금 그림이 그려지는 위치 (그림 크기가 달라도 버튼 가운데에 맞춤)."""
        return self.current_surface().get_rect(center=self.rect.center)

    def draw(self, window=None):
        (window or self.window).blit(self.current_surface(), self.draw_rect())


class ZoomButton(SimpleButton):
    """SimpleButton을 상속: 그림 한 장만 주면 hover 그림은 크게, active 그림은 살짝 작고 어둡게 자동으로 만든다.
    커진 그림이 화면 밖으로 나가지 않게 bounds 안으로 밀어 넣는다."""
    HOVER_SCALE = 1.2
    ACTIVE_SCALE = 1.12

    def __init__(self, window, loc, image, callBack=None, bounds=None):
        on = self._scaled(image, self.HOVER_SCALE)
        down = self._scaled(image, self.ACTIVE_SCALE)
        down.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_SUB)     # 누르는 중엔 살짝 어둡게
        super().__init__(window, loc, image, on, down, callBack)
        self.bounds = bounds

    @staticmethod
    def _scaled(image, k):
        w, h = image.get_size()
        return pygame.transform.smoothscale(image, (round(w * k), round(h * k)))

    def draw_rect(self):
        r = super().draw_rect()
        return r.clamp(self.bounds) if self.bounds else r
