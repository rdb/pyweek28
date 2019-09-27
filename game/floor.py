from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval
#from direct.fsm.FSM import FSM
from panda3d.core import PNMImage, Filename, Vec2

from .hobot import Hobot


class FloorBase:#(FSM):

    def __init__(self, parent):
        actor = Actor(self.model_path)
        actor.set_two_sided(True)
        actor.reparent_to(parent)
        print(actor.get_anim_names())
        actor.list_joints()
        self.actor = actor

        if self.walkable_path:
            self.walk_map = PNMImage()
            path = Filename.expand_from('$MAIN_DIR/assets/' + self.walkable_path)
            if not self.walk_map.read(path):
                print("Failed to read {}".format(path))
        else:
            self.walk_map = None

        # Make subparts for hobot.
        actor.make_subpart('hobot', ['hobot root', 'chain_a', 'chain_b', 'hand', 'wheel', 'neck', 'head', 'tuit', 'eyes'])

        # Make a copy for inspection of the animations, specifically to be able
        # to obtain the starting position of hobot in each animation.
        self.shadow_actor = Actor(self.model_path)
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
        self.hobot.lightbulb.hide()
        self.actor.release_joint('modelRoot', 'hobot root')

    def switch_to_free_hobot(self):
        self.hobot.face(self.hobot_root.get_sz() * -1)
        self.hobot.model.show()
        bone = self.actor.control_joint(None, 'modelRoot', 'hobot root')
        bone.set_pos(-100, -100, -100)
        self.hobot.unlock()

    def adjust_move(self, pos, delta, slide=True):
        x = (pos[0] + 16/9/2) * (9/16.0) * self.walk_map.size.x
        y = -(pos[1] - self.walkable_y_offset) * 2 * self.walk_map.size.y

        new_pos = pos + delta
        new_x = (new_pos[0] + 16/9/2) * (9/16.0) * self.walk_map.size.x
        new_y = -(new_pos[1] - self.walkable_y_offset) * 2 * self.walk_map.size.y

        if new_x < 0 or round(new_x) >= self.walk_map.size.x:
            return pos
        elif new_y < 0 or round(new_y) >= self.walk_map.size.y:
            return pos

        x = int(round(x))
        y = int(round(y))
        new_x = int(round(new_x))
        new_y = int(round(new_y))

        if self.walk_map.get_gray(new_x, new_y) > 0.5:
            return new_pos

        if not slide:
            return pos

        if delta[0] != 0 and self.walk_map.get_gray(new_x, y) > 0.5:
            return (new_pos[0], pos[1])
        elif delta[1] != 0 and self.walk_map.get_gray(x, new_y) > 0.5:
            return (pos[0], new_pos[1])
        elif delta[0] != 0 and delta[1] == 0:
            # Try 45 degree angle down and up
            new_pos = self.adjust_move(pos, Vec2(delta[0] * 0.894, delta[0] * 0.447), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[0] * 0.894, delta[0] * -0.707), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[0] * 0.707, delta[0] * 0.707), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[0] * 0.707, delta[0] * -0.707), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[0] * 0.447, delta[0] * 0.894), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[0] * 0.447, delta[0] * -0.894), slide=False)
            return new_pos
        elif delta[0] == 0 and delta[1] != 0:
            # Try 45 degree angle left and right
            new_pos = self.adjust_move(pos, Vec2(delta[1] * 0.447, delta[1] * 0.894), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[1] * -0.447, delta[1] * 0.894), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[1] * 0.707, delta[1] * 0.707), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[1] * -0.707, delta[1] * 0.707), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[1] * 0.894, delta[1] * 0.447), slide=False)
            if new_pos == pos:
                new_pos = self.adjust_move(pos, Vec2(delta[1] * -0.894, delta[1] * 0.447), slide=False)
            return new_pos
        else:
            return pos

    def process_input(self, input, dt):
        if self.hobot.locked:
            return
        self.hobot.process_input(input, dt, self)

        self.check_interactions()

    def check_interactions(self):
        pass
