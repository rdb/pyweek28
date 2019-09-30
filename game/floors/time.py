from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval

from ..floor import FloorBase

from random import randint


CLOCK_SPEED = 30


class Floor(FloorBase):
    model_path = 'floors/time/scene.bam'
    walkable_path = 'floors/time/walkable.png'
    music_path = 'floors/time/music.ogg'
    sound_path = 'floors/time/sfx/'
    sound_names = [
        "entrance",
        "exit",
        "pull_rope",
        "solved",
        "time_speed",
    ]

    walkable_y_offset = 0.08

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor

        actor.make_subpart('ropes', ['rope0', 'rope1', 'rope2'])
        actor.make_subpart('clocks', ['hand-0-b', 'hand-1-b', 'hand-2-b', 'hand-0-s', 'hand-1-s', 'hand-2-s'])

        self.time = [(0, 0), (0, 0), (0, 0)]
        self.big_hands = [actor.control_joint(None, 'modelRoot', 'hand-{}-b'.format(i)) for i in range(3)]
        self.small_hands = [actor.control_joint(None, 'modelRoot', 'hand-{}-s'.format(i)) for i in range(3)]

        # They all need to be set to 7:05 (which is 425 minutes)
        self.set_time_now(0, 0, 425 - randint(1, 3) * 60 * 2)
        self.set_time_now(1, 0, 425 - randint(1, 2) * 90 * 2)
        self.set_time_now(2, 0, 425 - randint(1, 2) * 72 * 2)

        self.solved = False

        self.__spin_task = None

    def destroy(self):
        if self.__spin_task:
            self.__spin_task.remove()
            self.__spin_task = None
        FloorBase.destroy(self)

    def start(self):
        self.play('entrance', ['hobot'], sound=self.sfx['entrance'])

        self.__spin_task = taskMgr.add(self.spin_clock)

    def ride_up(self):
        self.play('exit', ['hobot'], sound=self.sfx['exit'], callback=base.next_floor)

    def pull_rope(self, rope):
        if rope == 0:
            m = 60
        elif rope == 1:
            m = 90
        elif rope == 2:
            m = 72

        self.play('pull_rope{}'.format(rope), ['hobot', 'ropes'], extra_interval=Sequence(Wait(1.25), Func(self.add_time, rope, m)), sound=self.sfx['pull_rope'], callback=self.check_clocks)

    def check_clocks(self):
        if self.time[0] == 425 and self.time[1] == 425 and self.time[2] == 425:
            self.solved = True
            for i in range(3):
                self.actor.release_joint('modelRoot', 'hand-{}-b'.format(i))
                self.actor.release_joint('modelRoot', 'hand-{}-s'.format(i))
                self.actor.pose('solved', 1, ['clocks'])

        self.switch_to_free_hobot()

    def set_time(self, clock, hours, minutes):
        minutes = (hours * 60 + minutes) % (12 * 60)
        self.time[clock] = minutes
        minutes = int(minutes)
        print("Clock {} set to {: >2d}:{:02d}".format(clock, minutes // 60 if minutes else 12, minutes % 60))

    def set_time_now(self, clock, hours, minutes):
        self.set_time(clock, hours, minutes)

        minutes = self.time[clock]
        target_h = (minutes * -0.5) % 360
        self.small_hands[clock].set_h(target_h)
        self.big_hands[clock].set_h(target_h * 12)

    def add_time(self, clock, minutes):
        time = self.time[clock]
        self.set_time(clock, 0, time + minutes)

    def spin_clock(self, task):
        dt = globalClock.dt

        for clock in range(3):
            minutes = self.time[clock]
            current_h = self.small_hands[clock].get_h() % 360
            target_h = (minutes * -0.5) % 360
            diff = target_h - current_h
            if abs(diff) < 0.01:
                continue
            while diff > 0:
                diff -= 360
            rot = ((diff > 0) - (diff < 0)) * dt * CLOCK_SPEED

            if abs(rot) > abs(diff):
                rot = diff

            self.small_hands[clock].set_h(current_h + rot)
            self.big_hands[clock].set_h(self.big_hands[clock].get_h() + rot * 12)

        return task.cont

    def check_interactions(self):
        hobot_pos = self.hobot.model.get_pos()

        rope_positions = [0.27, 0.46, 0.65]
        if not self.solved:
            closest_rope = None
            closest_rope_dist = 1000

            for i, rope_x in enumerate(rope_positions):
                rope_dist = abs(hobot_pos.x - rope_x)
                if rope_dist < closest_rope_dist:
                    closest_rope_dist = rope_dist
                    closest_rope = i

            if closest_rope_dist < 0.09:
                self.hobot.set_action(lambda: self.pull_rope(closest_rope))
            else:
                self.hobot.clear_action()
        elif self.solved and hobot_pos.x < -0.20:
            self.hobot.set_action(self.ride_up)
        else:
            self.hobot.clear_action()

