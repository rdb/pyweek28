from direct.actor.Actor import Actor
from panda3d import core


MOVE_Y_SPEED = 0.2


class Hobot:
    max_speed = 0.25
    acceleration = 0.5
    deceleration = 0.5

    def __init__(self, anim_root):
        self.move_root = base.render.attach_new_node('hobot')
        self.anim_root = anim_root

        self.model = Actor('hobot/hobot.bam')

        self.hand = self.model.expose_joint(None, 'modelRoot', 'hand')
        head = self.model.expose_joint(None, 'modelRoot', 'head')

        self.model.reparent_to(self.anim_root)
        self.model.set_two_sided(True)
        self.model.find("**/+GeomNode").set_transform(self.model.get_joint_transform_state('modelRoot', 'hobot root').get_inverse())
        self.model.set_z(0.1)
        self.facing = 1.0

        self.move_control = self.model.get_anim_control('move_forward')

        self.speed = 0.0
        self.locked = True

        self.model.wrt_reparent_to(self.move_root)
        self.model.hide()

        light_texture = loader.load_texture('hobot/light_on.png')
        light_texture.set_wrap_u(core.SamplerState.WM_clamp)
        light_texture.set_wrap_v(core.SamplerState.WM_clamp)
        cm = core.CardMaker('card')
        cm.set_frame(-0.15, 0.15, 0.15, 0.45)
        self.lightbulb = head.attach_new_node(cm.generate())
        self.lightbulb.set_texture(light_texture)
        self.lightbulb.set_attrib(core.ColorBlendAttrib.make(core.ColorBlendAttrib.M_add, core.ColorBlendAttrib.O_incoming_alpha, core.ColorBlendAttrib.O_one))
        self.lightbulb.set_depth_test(False)
        self.lightbulb.set_bin('fixed', 0)
        self.lightbulb.set_p(-90)
        self.lightbulb.set_billboard_point_eye()
        self.lightbulb.set_two_sided(True)
        self.lightbulb.hide()

        shadow_texture = loader.load_texture('hobot/drop_shadow.png')
        shadow_texture.set_wrap_u(core.SamplerState.WM_clamp)
        shadow_texture.set_wrap_v(core.SamplerState.WM_clamp)
        cm = core.CardMaker('card')
        cm.set_frame(-0.35, 0.35, -0.45, -0.1)
        self.shadow = self.model.attach_new_node(cm.generate())
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

        self.ding_sfx = loader.load_sfx('hobot/sfx/ding.wav')
        self.ding_sfx.set_volume(0.5)
        self.move_sfx = loader.load_sfx('hobot/sfx/move.wav')
        self.move_sfx.set_loop(True)

        self.action_callback = None

    def destroy(self):
        if self.move_control.playing:
            self.move_control.stop()
            self.move_sfx.stop()

        # RIP hobot :-(
        self.model.cleanup()

    def set_action(self, callback):
        self.action_callback = callback
        if self.lightbulb.is_hidden():
            self.ding_sfx.play()
            self.lightbulb.show()

    def clear_action(self):
        self.action_callback = None
        self.lightbulb.hide()

    def do_action(self):
        if self.action_callback:
            self.action_callback()

    def lock(self):
        #self.model.wrt_reparent_to(self.anim_root)
        self.locked = True
        self.speed = 0.0

    def unlock(self):
        self.model.set_pos(self.anim_root.get_pos())
        self.locked = False
        self.model.set_hpr(0, 0, -90)
        self.model.show()

    def face(self, dir):
        if dir:
            self.facing = 1 if dir > 0 else -1
            self.model.set_sz(self.facing * -self.model.get_sx())

    def process_input(self, input, dt, level):
        if self.locked:
            return

        if input.get_action('interact'):
            self.do_action()

        move_x = input.get_axis('move-horizontal')
        move_y = input.get_axis('move-vertical')

        if move_x:
            self.speed += move_x * self.acceleration * dt
            self.face(move_x)
        elif self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration * dt)
        elif self.speed < 0:
            self.speed = min(0, self.speed + self.deceleration * dt)

        delta = core.Vec2(0, 0)

        if move_y:
            delta.y = move_y * dt * MOVE_Y_SPEED

        if self.speed != 0:
            if self.speed > self.max_speed:
                self.speed = self.max_speed
            elif self.speed < -self.max_speed:
                self.speed = -self.max_speed

            delta.x = self.speed * dt
            pos_changed = True

            self.move_control.set_play_rate(self.speed * self.facing * 4.0)

            if not self.move_control.playing:
                self.move_control.loop(False)
                self.move_sfx.play()

        elif self.move_control.playing:
            self.move_control.stop()
            self.move_sfx.stop()

        if delta.length_squared() > 0:
            old_pos = self.model.get_pos()
            new_pos = level.adjust_move(old_pos.xy, delta)
            self.model.set_pos(core.LPoint3(new_pos, old_pos.z))
