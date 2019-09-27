from direct.showbase.ShowBase import ShowBase
from panda3d import core

import importlib

from . import floors
from .input import Input


ASPECT_RATIO = 16 / 9.0


class Game(ShowBase):
    def __init__(self):
        core.load_prc_file(core.Filename.expand_from('$MAIN_DIR/settings.prc'))

        ShowBase.__init__(self)

        # Set up a letterbox.
        # For some reason, using a scissor effect decapitates Hobot, the clumsy
        # oaf.  We'll just cover up the bottom and top with some black bars.
        #self.render.set_effect(core.ScissorEffect.make_node((-ASPECT_RATIO * 0.5, -0.5, 0), (ASPECT_RATIO * 0.5, 0.5, 0)))
        self.set_background_color(0, 0, 0, 1)
        cm = core.CardMaker('black-bar')
        cm.set_color((0, 0, 0, 1))
        cm.set_frame(-100, 100, 0.5, 100)
        upper_bar = self.render.attach_new_node(cm.generate())
        upper_bar.set_p(-90)
        upper_bar.set_bin('background', 0)
        upper_bar.set_z(99)
        cm.set_frame(-100, 100, -100, -0.5)
        lower_bar = self.render.attach_new_node(cm.generate())
        lower_bar.set_p(-90)
        lower_bar.set_bin('background', 0)
        lower_bar.set_z(99)

        # Set up camera
        self.disable_mouse()
        lens = core.OrthographicLens()
        lens.film_size = (ASPECT_RATIO, 1)
        lens.set_view_vector((0, 0, -1), (0, 1, 0))
        lens.set_near_far(-100, 100)
        self.cam.node().set_lens(lens)
        self.camLens = lens

        self.input = Input(self.mouseWatcherNode, self.win.get_keyboard_map())
        self.task_mgr.add(self.input_task, 'input')
        self.input_clock = core.ClockObject.get_global_clock()

        self.input_clock.set_mode(core.ClockObject.M_limited)
        self.input_clock.set_frame_rate(60.0)

    def input_task(self, task):
        dt = self.input_clock.dt
        self.floor.process_input(self.input, dt)
        return task.cont

    def load_floor(self, name):
        module = importlib.import_module('.floors.' + name, 'game')
        self.floor = module.Floor(self.render)


def main(floor='rusty'):
    game = Game()
    game.load_floor(floor)
    game.run()
