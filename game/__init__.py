from direct.showbase.ShowBase import ShowBase
from panda3d import core

from .input import Input
from .hobot import Hobot


ASPECT_RATIO = 16 / 9.0


class Game(ShowBase):
    def __init__(self):
        core.load_prc_file(core.Filename.expand_from('$MAIN_DIR/settings.prc'))

        ShowBase.__init__(self)

        # Set up letterbox
        self.set_background_color(0, 0, 0, 1)
        self.render.set_effect(core.ScissorEffect.make_node((-ASPECT_RATIO * 0.5, -0.5, 0), (ASPECT_RATIO * 0.5, 0.5, 0)))

        # Set up camera
        self.disable_mouse()
        lens = core.OrthographicLens()
        lens.film_size = (ASPECT_RATIO, 1)
        lens.set_view_vector((0, 0, -1), (0, 1, 0))
        lens.set_near_far(-100, 100)
        self.cam.node().set_lens(lens)
        self.camLens = lens

        self.hobot = Hobot(self.render)

        self.input = Input(self.mouseWatcherNode, self.win.get_keyboard_map())
        self.task_mgr.add(self.input_task, 'input')
        self.input_clock = core.ClockObject.get_global_clock()

        self.input_clock.set_mode(core.ClockObject.M_limited)
        self.input_clock.set_frame_rate(60.0)

    def input_task(self, task):
        dt = self.input_clock.dt
        self.hobot.process_input(self.input, dt)
        return task.cont

    def load_floor(self, name):
        #module = importlib.import_module('.' + name, 'floors')
        #self.floor = module.Floor()
        model = loader.load_model(name + '.bam')
        model.reparent_to(self.render)


def main():
    game = Game()
    game.load_floor('rusty')
    game.run()
