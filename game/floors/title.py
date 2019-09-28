from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval

from ..floor import FloorBase


class Floor(FloorBase):
    model_path = 'floors/title/scene.bam'
    music_path = 'floors/title/music.ogg'
    sound_path = 'floors/title/sfx/'
    sound_names = [
        "fontflop",
        "hobo_intro",
    ]

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor
        actor.make_subpart("logo", ["H", "O", "b", "o", "t", "s", "hand2"])

    def start(self):
        self.play('fontflop', ['logo'], sound=self.sfx['fontflop'])
        self.play('entrance', ['hobot'], sound=self.sfx['hobo_intro'])

    def check_interactions(self):
        base.next_floor()
