from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval
#from direct.gui.OnscreenImage import OnscreenImage

from ..floor import FloorBase


class Floor(FloorBase):
    model_path = 'floors/title/scene.bam'
    music_path = 'floors/title/music.ogg'
    sound_path = 'floors/title/sfx/'
    sound_names = [
        "fontflop",
        "hobo_intro1",
        "hobo_intro2",
    ]

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor
        actor.make_subpart("keypress", ["keypress"])
        actor.make_subpart("logo", ["H", "O", "b", "o", "t", "s", "hand2"])

    def start(self):
        self.play('fontflop', ['logo'], sound=self.sfx['fontflop'])
        self.play('entrance', ['hobot', 'keypress'], to_frame=80, sound=self.sfx['hobo_intro1'], callback=self.on_stumble)

        #img = OnscreenImage(loader.load_texture('floors/title/layers/a09-keypress.png'))
        #img.reparent_to(self.actor)
        #img.set_pos(0, 0, 1)
        #img.set_p(-90)
        #img.set_scale(0.451, 1, 0.041)

    def on_stumble(self):
        base.accept('enter', self.on_start)
        base.accept('space', self.on_start)

    def on_start(self):
        base.ignore('enter')
        base.ignore('space')
        self.play('fontflop', ['logo'], sound=self.sfx['fontflop'])
        self.play('entrance', ['hobot', 'keypress'], from_frame=80, callback=base.next_floor, sound=self.sfx['hobo_intro2'])
