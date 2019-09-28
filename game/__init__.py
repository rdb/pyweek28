from direct.showbase.ShowBase import ShowBase
from direct.interval.IntervalGlobal import Wait, Func, Sequence
from panda3d import core

import importlib

from . import floors
from .input import Input


ASPECT_RATIO = 16 / 9.0

FLOORS = ['title','rusty', 'nature', 'time', 'light', 'bells','end']


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

        base.accept('alt-enter', self.toggle_fullscreen)
        base.accept('f11', self.toggle_fullscreen)
        base.accept('f12', self.screenshot)

        self.floor = None
        self.floor_index = -1
        self.transitions.IrisModelName = 'ui/iris.egg'
        self.transitions.fadeOut(0)

        self.stored_win_size = (1280, 800)

    def toggle_fullscreen(self):
        props = self.win.get_properties()
        if props.fullscreen:
            wp = core.WindowProperties()
            wp.size = self.stored_win_size
            wp.fullscreen = False
            self.win.request_properties(wp)
        else:
            info = self.pipe.get_display_information()

            wp = core.WindowProperties()
            if self.find_display_mode(info, 1920, 1080):
                wp.size = (1920, 1080)
            else:
                wp.size = (self.pipe.get_display_width(), self.pipe.get_display_height())

            wp.fullscreen = True
            self.win.request_properties(wp)

    def find_display_mode(self, info, width, height):
        if not info:
            return False

        for mode in info.get_display_modes():
            if mode.width == width and mode.height == height:
                return True

        return False

    def input_task(self, task):
        dt = self.input_clock.dt
        if self.floor is not None:
            self.floor.process_input(self.input, dt)
        return task.cont

    def next_floor(self):
        if self.floor is not None:
            print("Transitioning to next floor")
            old_floor = self.floor
            self.floor = None
            self.transitions.fadeOut(2.0)
            Sequence(Wait(2.5), Func(old_floor.destroy), Func(self.next_floor)).start()
        else:
            self.floor_index += 1
            self.load_floor(FLOORS[self.floor_index])

    def load_floor(self, name):
        print("Loading floor {}".format(name))
        module = importlib.import_module('.floors.' + name, 'game')
        self.transitions.fadeOut(0)
        self.floor = module.Floor(self.render)
        try:
            self.floor_index = FLOORS.index(name)
        except ValueError:
            self.floor_index = 0
        Sequence(Wait(1.0), Func(self.floor.actor.show), Func(self.transitions.fadeIn, 2.0), Wait(1.0), Func(self.floor.start)).start()

    def end_game(self):
        old_floor = self.floor
        self.floor = None
        self.transitions.setFadeColor(1, 1, 1)
        self.transitions.fadeOut(3.0, blendType='easeIn')
        Sequence(Wait(3.5), Func(old_floor.destroy), Func(self.next_floor)).start()


def main(floor=None):
    game = Game()
    if floor:
        game.load_floor(floor)
    else:
        game.next_floor()
    game.run()
