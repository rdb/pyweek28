from direct.showbase.ShowBase import ShowBase


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)


def main():
    game = Game()
    game.run()
