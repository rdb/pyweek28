from direct.showbase.ShowBase import ShowBase
from panda3d.core import OrthographicLens, Filename, ScissorEffect, load_prc_file


ASPECT_RATIO = 16 / 9.0


class Game(ShowBase):
    def __init__(self):
        load_prc_file(Filename.expand_from('$MAIN_DIR/settings.prc'))

        ShowBase.__init__(self)

        # Set up letterbox
        self.set_background_color(0, 0, 0, 1)
        self.render.set_effect(ScissorEffect.make_node((-ASPECT_RATIO * 0.5, -0.5, 0), (ASPECT_RATIO * 0.5, 0.5, 0)))

        # Set up camera
        self.disable_mouse()
        lens = OrthographicLens()
        lens.film_size = (ASPECT_RATIO, 1)
        lens.set_view_vector((0, 0, -1), (0, 1, 0))
        lens.set_near_far(-100, 100)
        self.cam.node().set_lens(lens)
        self.camLens = lens

    def load_floor(self, name):
        #module = importlib.import_module('.' + name, 'floors')
        #self.floor = module.Floor()
        model = loader.load_model(name + '.bam')
        model.reparent_to(self.render)


def main():
    game = Game()
    game.load_floor('rusty')
    game.run()
