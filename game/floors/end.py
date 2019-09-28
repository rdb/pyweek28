from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval
import sys

from ..floor import FloorBase


class Floor(FloorBase):
    model_path = 'floors/end/scene.bam'
    music_path = 'floors/end/music.ogg'

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor
        actor.make_subpart("credits", ["credits"])
        actor.make_subpart("cube", ['cube'])

    def start(self):
        self.play('entrance', ['credits'])
        self.play('cube', ['cube'], loop=True)
        base.accept('escape', sys.exit)
