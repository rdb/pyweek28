from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval
from panda3d import core

from ..floor import FloorBase

BEAM_COLOR = (0.6, 0.6, 0.5)


class Floor(FloorBase):
    model_path = 'floors/light/scene.bam'
    walkable_path = 'floors/light/walkable.png'
    music_path = 'floors/light/music.ogg'
    sound_path = 'floors/light/sfx/'
    sound_names = [
        "entrance",
        "exit",
        "elevator_down",
        "mirror_adjust",
        "solved",
    ]

    walkable_y_offset = 0.05

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor

        actor.make_subpart('eye', ['eye'])
        actor.make_subpart('elevator', ['elevator', 'elevatordoor-l', 'elevatordoor-r', 'elevatorshadow'])
        actor.make_subpart('mirror0', ['mirror0', 'beam0'])
        actor.make_subpart('mirror1', ['mirror1', 'beam1'])
        actor.make_subpart('mirror2', ['mirror2', 'beam2'])

        self.mirror_states = [0, 0, 0]
        self.solved = False
        self.elevator_down = False

        self.beam_geoms = []
        for gnode_path in self.actor.find_all_matches("**/+GeomNode"):
            gnode = gnode_path.node()
            for gi in range(gnode.get_num_geoms()):
                state = gnode.get_geom_state(gi)
                mattr = state.get_attrib(core.MaterialAttrib)
                if mattr:
                    mat = mattr.get_material()
                    if mat and mat.name in ('a03-beam_mirror', 'a04-beam_eye'):
                        self.beam_geoms.append([gnode, gi])

        for gnode, gi in self.beam_geoms:
            state = gnode.get_geom_state(gi)
            state = state.set_attrib(core.DepthWriteAttrib.make(False))
            state = state.set_attrib(core.ColorBlendAttrib.make(core.ColorBlendAttrib.M_add, core.ColorBlendAttrib.O_incoming_alpha, core.ColorBlendAttrib.O_one))
            state = state.set_attrib(core.ColorScaleAttrib.make((*BEAM_COLOR, 1.0)))
            gnode.set_geom_state(gi, state)

    def start(self):
        self.play('entrance', sound=self.sfx['entrance'])

    def adjust_mirror(self, mirror):
        if self.solved:
            return
        self.play('mirror{}_adjust'.format(mirror), ['hobot'], sound=self.sfx['mirror_adjust'], callback=self.on_mirror_changed)

        def rotate(m, d=1):
            self.mirror_states[m] = (self.mirror_states[m] + d) % 3

        if mirror == 0:
            rotate(0)
            rotate(2, -1)
        elif mirror == 1:
            rotate(1)
        elif mirror == 2:
            rotate(1)
            rotate(2)

    def on_mirror_changed(self):
        for mirror, state in enumerate(self.mirror_states):
            self.actor.pose('mirror{}_state'.format(mirror), state, partName='mirror{}'.format(mirror))

        if self.mirror_states == [2, 2, 2]:
            self.solved = True
            self.play('escape', ['hobot'], callback=self.on_escaped, sound=self.sfx['solved'])
        else:
            self.switch_to_free_hobot()

    def hide_beams_task(self, task):
        brightness = max(0.0, 1.0 - task.time)
        for gnode, gi in self.beam_geoms:
            state = gnode.get_geom_state(gi)
            state = state.set_attrib(core.ColorScaleAttrib.make((0.5, 0.5, 0.4, brightness)))
            gnode.set_geom_state(gi, state)

        if brightness > 0.0:
            return task.cont
        else:
            return task.done

    def on_escaped(self):
        base.taskMgr.add(self.hide_beams_task, 'hide_beams')
        self.load_walk_map('floors/light/walkable2.png')
        self.play('elevator_down', ['eye', 'elevator'], sound=self.sfx['elevator_down'], callback=self.on_elevator_down)
        self.switch_to_free_hobot()
        self.hobot.model.set_z(15)
        self.hobot.face(-1)

    def on_elevator_down(self):
        self.elevator_down = True

    def ride_elevator_up(self):
        self.play('exit', ['hobot', 'elevator'], extra_interval=Sequence(Wait(3.0), Func(self.hide_scene_hobot)), callback=base.next_floor, sound=self.sfx["exit"])

    def check_interactions(self):
        hobot_pos = self.hobot.model.get_pos()

        if not self.solved and hobot_pos.y >= -0.24:
            if hobot_pos.x > -0.53 and hobot_pos.x < -0.3:
                self.hobot.set_action(lambda: self.adjust_mirror(0))
            elif hobot_pos.x > -0.076 and hobot_pos.x < 0.19:
                self.hobot.set_action(lambda: self.adjust_mirror(1))
            elif hobot_pos.x > 0.33 and hobot_pos.x < 0.57:
                self.hobot.set_action(lambda: self.adjust_mirror(2))
            else:
                self.hobot.clear_action()
        elif self.elevator_down and hobot_pos.x > -0.1 and hobot_pos.x < 0.15 and hobot_pos.y > -0.28:
            self.ride_elevator_up()
        else:
            self.hobot.clear_action()
