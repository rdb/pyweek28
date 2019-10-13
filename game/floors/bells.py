from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval

from ..floor import FloorBase


class Floor(FloorBase):
    model_path = 'floors/bells/scene.bam'
    walkable_path = 'floors/bells/walkable.png'
    music_path = 'floors/bells/music.ogg'
    sound_path = 'floors/bells/sfx/'
    sound_names = [
        'bell0_smack',
        'bell1_smack',
        'bell2_smack',
        'bell3_smack',
        'cubesong',
        'cube_landing',
        'entrance',
        'exit',
    ]

    walkable_y_offset = 0.02

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor

        actor.make_subpart('sky', ['sky'])
        actor.make_subpart('cube', ['cube'])
        actor.make_subpart('elevator', ['elevator', 'elevator opening', 'elevator door right', 'elevator door left'])
        actor.make_subpart('bells', ['bell0', 'bell1', 'bell2', 'bell3'])

        self.actor.pose('sky_scroll', 1, partName='sky')

        # Contains last four bells that Hobot smacked
        self.sequence = ()
        self.cube_landed = False

        self.cube_idle_loop = Sequence(
            ActorInterval(self.actor, 'cube idle', partName='cube'),
            ActorInterval(self.actor, 'cube idle', partName='cube'),
            ActorInterval(self.actor, 'cube idle', partName='cube'),
            Func(self.sfx['cubesong'].play),
            ActorInterval(self.actor, 'cube singing', partName='cube'),
            ActorInterval(self.actor, 'cube singing', partName='cube'),
            ActorInterval(self.actor, 'cube idle', partName='cube'),
        )

    def start(self):
        self.play('entrance', ['hobot', 'elevator'], sound=self.sfx['entrance'])
        self.cube_idle_loop.loop()

    def smack_bell(self, bell):
        self.sequence = self.sequence[-3:] + (bell,)
        anim_name = 'bell{}_smack'.format(bell)

        if self.sequence == (1, 3, 0, 2):
            callback = self.on_good_bell_smacking
        else:
            callback = None

        self.play(anim_name, ['hobot', 'bells'], sound=self.sfx[anim_name], callback=callback)

    def on_good_bell_smacking(self):
        self.cube_idle_loop.pause()
        self.cube_idle_loop = None
        self.cube_landed = True
        self.play('cube landing', ['cube'], sound=self.sfx['cube_landing'])

        self.switch_to_free_hobot()

    def enter_cube(self):
        self.play('exit', ['cube', 'hobot'], extra_interval=Sequence(Wait(3.0), Func(self.hide_scene_hobot)), callback=base.end_game, sound=self.sfx['exit'])

    def check_interactions(self):
        hobot_pos = self.hobot.model.get_pos()

        if self.cube_landed and hobot_pos.x > 0.25 and hobot_pos.y > -0.40:
            self.enter_cube()
        elif hobot_pos.y > -0.3:
            if hobot_pos.x > -0.33 and hobot_pos.x < -0.20:
                self.hobot.set_action(lambda: self.smack_bell(0))
            elif hobot_pos.x > -0.17 and hobot_pos.x < -0.05:
                self.hobot.set_action(lambda: self.smack_bell(1))
            elif hobot_pos.x > 0.01 and hobot_pos.x < 0.14:
                self.hobot.set_action(lambda: self.smack_bell(2))
            elif hobot_pos.x > 0.20 and hobot_pos.x < 0.33:
                self.hobot.set_action(lambda: self.smack_bell(3))
            else:
                self.hobot.clear_action()
        else:
            self.hobot.clear_action()
