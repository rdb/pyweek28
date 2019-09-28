from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval

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
        actor.make_subpart("logo", ["H", "O", "b", "o", "t", "s", "hand2"])

    def start(self):
        self.play('fontflop', ['logo'], sound=self.sfx['fontflop'])
        self.play('entrance', ['hobot'], to_frame=80, sound=self.sfx['hobo_intro1'], callback=self.on_stumble)

    def on_stumble(self):
        base.accept('enter', self.on_start)
        base.accept('space', self.on_start)

    def on_start(self):
        base.ignore('enter')
        base.ignore('space')
        self.play('fontflop', ['logo'], sound=self.sfx['fontflop'])
        self.play('entrance', ['hobot'], from_frame=80, callback=self.on_stumble, sound=self.sfx['hobo_intro2'])
