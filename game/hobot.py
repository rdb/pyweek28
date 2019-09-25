from direct.actor.Actor import Actor


HOBOT_SCALE = 0.25


class Hobot:
    max_speed = 0.5
    acceleration = 1.0
    deceleration = 1.0

    def __init__(self, root):
        self.model = Actor('hobot.bam')
        self.model.reparent_to(root)
        self.model.set_two_sided(True)
        self.model.set_scale(HOBOT_SCALE)
        self.model.set_y(-0.45)
        self.model.set_z(50)
        self.facing = 1.0

        self.move_control = self.model.get_anim_control('move_forward')

        self.speed = 0.0

    def process_input(self, input, dt):
        move_x = input.get_axis('move-horizontal')
        move_y = input.get_axis('move-vertical')

        if move_x:
            self.speed += move_x * self.acceleration * dt
            self.facing = 1 if move_x > 0 else -1
            self.model.set_sx(self.facing * -HOBOT_SCALE)
        elif self.speed > 0:
            self.speed = max(0, self.speed - self.deceleration * dt)
        elif self.speed < 0:
            self.speed = min(0, self.speed + self.deceleration * dt)

        if self.speed != 0:
            if self.speed > self.max_speed:
                self.speed = self.max_speed
            elif self.speed < -self.max_speed:
                self.speed = -self.max_speed

            self.model.set_x(self.model.get_x() + self.speed * dt)

            self.move_control.set_play_rate(self.speed * self.facing * 4.0)

            if not self.move_control.playing:
                self.move_control.loop(False)

        elif self.move_control.playing:
            self.move_control.stop()
