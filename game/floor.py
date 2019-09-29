from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval
#from direct.fsm.FSM import FSM
from panda3d import core
from panda3d.core import PNMImage, Filename, Vec2, TransformState

from .hobot import Hobot


class FloorBase:#(FSM):

    walkable_path = None
    music_path = None
    sound_names = []

    walkable_y_offset = 0.0
    free_hobot_z = None

    def __init__(self, parent):
        actor = Actor(self.model_path)
        actor.set_two_sided(True)
        actor.reparent_to(parent)
        #print(actor.get_anim_names())
        #actor.list_joints()
        self.actor = actor
        self.actor.hide()

        if self.walkable_path:
            self.walk_map = PNMImage()
            self.load_walk_map(self.walkable_path)
        else:
            self.walk_map = None

        if self.music_path:
            self.music = base.loader.load_music(self.music_path)
            self.music.set_loop(True)
            self.music.set_volume(0.5)
            self.music.play()
        else:
            self.music = None

        self.sfx = {}
        for s in self.sound_names:
            self.sfx[s] = base.loader.load_sfx(Filename(self.sound_path, s + ".wav"))

        # Make subparts for hobot.
        actor.make_subpart('hobot', ['hobot root', 'chain_a', 'chain_b', 'hand', 'wheel', 'neck', 'head', 'tuit', 'eyes'])

        # Make a copy for inspection of the animations, specifically to be able
        # to obtain the starting position of hobot in each animation.
        self.shadow_actor = Actor(self.model_path)
        self.shadow_hobot_root = self.shadow_actor.expose_joint(None, 'modelRoot', 'hobot root')

        # Make sure hobot is in a defined state in the actor
        actor.pose('entrance', 0)

        self.hobot_root = actor.expose_joint(None, 'modelRoot', 'hobot root')
        self.hobot_hand = actor.expose_joint(None, 'modelRoot', 'hand')
        self.hobot = Hobot(self.hobot_root)

        shadow_texture = loader.load_texture('hobot/drop_shadow.png')
        shadow_texture.set_wrap_u(core.SamplerState.WM_clamp)
        shadow_texture.set_wrap_v(core.SamplerState.WM_clamp)
        cm = core.CardMaker('card')
        cm.set_frame(-0.35, 0.35, -0.45, -0.1)
        self.shadow = self.hobot_root.attach_new_node(cm.generate())
        self.shadow.set_texture(shadow_texture)
        self.shadow.set_attrib(core.ColorBlendAttrib.make(core.ColorBlendAttrib.M_add, core.ColorBlendAttrib.O_zero, core.ColorBlendAttrib.O_one_minus_incoming_alpha))
        self.shadow.set_p(-90)
        self.shadow.set_depth_write(False)
        self.shadow.set_x(0.2)
        self.shadow.set_billboard_point_eye()
        self.shadow.set_two_sided(True)
        self.shadow.set_bin('transparent', 0)
        self.shadow.set_alpha_scale(0)
        self.shadow_fade = None

        self.carrying_joint = None
        self.carrying_joint_name = None

    def destroy(self):
        self.actor.cleanup()
        self.hobot.destroy()
        if self.music:
            self.music.stop()
        self.actor.remove_node()
        for sound_name in self.sound_names:
            self.sfx[sound_name].stop()

    def start(self):
        pass

    def load_walk_map(self, path):
        path = Filename.expand_from('$MAIN_DIR/assets/' + path)
        if not self.walk_map.read(path):
            print("Failed to read {}".format(path))

    def grab_joint(self, name):
        print("Grabbing {}".format(name))
        self.carrying_joint_name = name
        self.hobot.model.set_pos(self.hobot.anim_root.get_pos())
        transform = self.actor.get_joint_transform_state('modelRoot', name)

        parent = self.actor.attach_new_node('parent')
        self.carrying_joint = self.actor.control_joint(parent.attach_new_node('joint'), 'modelRoot', name)
        self.carrying_joint.set_transform(transform)
        self.carrying_joint_initial_transform = transform
        self.carrying_joint_initial_hobot_hand_pos = self.hobot.hand.get_pos(self.actor)

    def release_joint(self, name):
        print("Releasing {}".format(name))
        self.actor.release_joint('modelRoot', name)
        self.carrying_joint = None
        self.carrying_joint_name = None

    def get_anim_starting_hobot_pos(self, anim):
        # Returns Hobot's starting position for a given animation.
        self.shadow_actor.pose(anim, 0)
        self.shadow_actor.update()
        return self.shadow_hobot_root.get_pos()

    def play(self, anim, parts=None, loop=False, extra_interval=None, from_frame=None, to_frame=None, callback=None, release_joint=None, sound=None):
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
                anims.append(ActorInterval(self.actor, anim, startFrame=from_frame, endFrame=to_frame, partName=part))

            if extra_interval:
                anims.append(extra_interval)

            if sound:
                anims.append(Func(sound.play))

            if callback is None:
                callback = self.switch_to_free_hobot

            seq = Sequence(
                self.hobot.model.posInterval(time, hobot_pos, blendType='easeInOut'),
                Func(self.switch_to_scene_hobot),
                Parallel(*anims),
                Func(callback))

            if loop:
                seq.loop()
            else:
                seq.start()
        elif loop:
            if sound:
                sound.play()
            if not parts:
                self.actor.loop(anim, fromFrame=from_frame, toFrame=to_frame)
            else:
                for part in parts:
                    self.actor.loop(anim, fromFrame=from_frame, toFrame=to_frame, partName=part)
        else:
            if sound:
                sound.play()

            if callback:
                anims = []
                for part in parts or (None,):
                    anims.append(ActorInterval(self.actor, anim, startFrame=from_frame, endFrame=to_frame, partName=part))

                Sequence(Parallel(*anims), Func(callback)).start()
            else:
                if not parts:
                    self.actor.play(anim)
                else:
                    for part in parts:
                        self.actor.play(anim, fromFrame=from_frame, toFrame=to_frame, partName=part)

    def switch_to_scene_hobot(self):
        self.hobot.lock()
        self.hobot.model.hide()
        self.hobot.lightbulb.hide()
        self.actor.release_joint('modelRoot', 'hobot root')
        if self.carrying_joint_name and self.carrying_joint:
            self.actor.release_joint('modelRoot', self.carrying_joint_name)
            self.carrying_joint = None

        if self.shadow_fade is not None:
            self.shadow_fade.pause()
        self.shadow.set_alpha_scale(self.hobot.shadow.get_color_scale()[3])
        self.shadow_fade = self.shadow.colorScaleInterval(5.0, (1, 1, 1, 0), blendType='easeInOut')
        self.shadow_fade.start()

    def switch_to_free_hobot(self):
        if self.hobot.model.is_empty():
            return
        self.hobot.face(self.hobot_root.get_sz() * -1)
        self.hobot.model.show()
        bone = self.actor.control_joint(None, 'modelRoot', 'hobot root')
        bone.set_pos(-100, -100, -100)
        self.hobot.unlock()

        if self.hobot.shadow_fade is not None:
            self.hobot.shadow_fade.pause()
        self.hobot.shadow.set_alpha_scale(self.shadow.get_color_scale()[3])
        self.hobot.shadow_fade = self.hobot.shadow.colorScaleInterval(5.0, (1, 1, 1, 1), blendType='easeInOut')
        self.hobot.shadow_fade.start()

        if self.free_hobot_z is not None:
            self.hobot.model.set_z(self.free_hobot_z)

        if self.carrying_joint_name and not self.carrying_joint:
            self.grab_joint(self.carrying_joint_name)

    def hide_scene_hobot(self):
        print("Hiding hobot")
        self.actor.control_joint(None, 'modelRoot', 'hobot root').set_z(-10000)

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

        if self.carrying_joint:
            pos = self.hobot.hand.get_pos(self.actor) - self.carrying_joint_initial_hobot_hand_pos
            self.carrying_joint.set_transform(TransformState.make_pos((self.hobot.model.get_z(), pos[1], -pos[0])).compose(self.carrying_joint_initial_transform))

        self.check_interactions()

    def check_interactions(self):
        pass
