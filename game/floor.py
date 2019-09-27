from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval
#from direct.fsm.FSM import FSM

from .hobot import Hobot


class FloorBase:#(FSM):
    # l, r, b, t
    boundaries = (-0.6, 0.6, -0.5, -0.26)

    def __init__(self, parent, bamfile):
        actor = Actor(bamfile)
        actor.set_two_sided(True)
        actor.reparent_to(parent)
        print(actor.get_anim_names())
        actor.list_joints()
        self.actor = actor

        # Make subparts for hobot.
        actor.make_subpart('hobot', ['hobot root', 'chain_a', 'chain_b', 'hand', 'wheel', 'neck', 'head', 'tuit', 'eyes'])

        # Make a copy for inspection of the animations, specifically to be able
        # to obtain the starting position of hobot in each animation.
        self.shadow_actor = Actor(bamfile)
        self.shadow_hobot_root = self.shadow_actor.expose_joint(None, 'modelRoot', 'hobot root')

        # Make sure hobot is in a defined state in the actor
        actor.pose('entrance', 0)

        self.hobot_root = actor.expose_joint(None, 'modelRoot', 'hobot root')
        self.hobot = Hobot(self.hobot_root)

    def get_anim_starting_hobot_pos(self, anim):
        # Returns Hobot's starting position for a given animation.
        self.shadow_actor.pose(anim, 0)
        self.shadow_actor.update()
        return self.shadow_hobot_root.get_pos()

    def play(self, anim, parts=None, loop=False, extra_interval=None):
        if parts is None:
            print("Playing {} on all parts".format(anim))
        else:
            print("Playing {} on {}".format(anim, list(parts)))

        if parts is None or 'hobot' in parts:
            # Move hobot to the position first
            self.hobot.model.show()
            self.hobot.lock()
            hobot_pos = self.get_anim_starting_hobot_pos(anim)

            delta = hobot_pos.x - self.hobot.model.get_x()
            self.hobot.face(delta)
            time = abs(delta) * 4

            anims = []
            for part in parts or (None,):
                anims.append(ActorInterval(self.actor, anim, partName=part))

            if extra_interval:
                anims.append(extra_interval)

            seq = Sequence(
                self.hobot.model.posInterval(time, hobot_pos, blendType='easeInOut'),
                Func(self.switch_to_scene_hobot),
                Parallel(*anims),
                Func(self.switch_to_free_hobot))

            if loop:
                seq.loop()
            else:
                seq.start()
        elif loop:
            if not parts:
                self.actor.loop(anim)
            else:
                for part in parts:
                    self.actor.loop(anim, partName=part)
        else:
            if not parts:
                self.actor.play(anim)
            else:
                for part in parts:
                    self.actor.play(anim, partName=part)

    def switch_to_scene_hobot(self):
        self.hobot.lock()
        self.hobot.model.hide()
        self.actor.release_joint('modelRoot', 'hobot root')

    def switch_to_free_hobot(self):
        self.hobot.face(self.hobot_root.get_sz() * -1)
        self.hobot.model.show()
        bone = self.actor.control_joint(None, 'modelRoot', 'hobot root')
        bone.set_pos(-100, -100, -100)
        self.hobot.unlock()

    def process_input(self, input, dt):
        if self.hobot.locked:
            return
        self.hobot.process_input(input, dt)

        hobot_model = self.hobot.model
        hobot_pos = hobot_model.get_pos()

        if hobot_pos.x < self.boundaries[0]:
            hobot_model.set_x(self.boundaries[0])
        elif hobot_pos.x > self.boundaries[1]:
            hobot_model.set_x(self.boundaries[1])

        if hobot_pos.y < self.boundaries[2]:
            hobot_model.set_y(self.boundaries[2])
        elif hobot_pos.y > self.boundaries[3]:
            hobot_model.set_y(self.boundaries[3])

        self.check_interactions()

    def check_interactions(self):
        pass
