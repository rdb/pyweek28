from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval

from ..floor import FloorBase


class Floor(FloorBase):
    model_path = 'nature_mergedhobot.bam'
    walkable_path = 'floors/nature/walkable.png'

    walkable_y_offset = 0.025

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor

        self.play('entrance')

        actor.make_subpart('pump', ['pump plunger', 'pump handle', 'drip'])
        actor.make_subpart('bucket', ['bucket'])

        self.hook_position = 'original'
        self.holding_bucket = False

    def pickup_hook(self):
        self.play('grab_hook_wall')
        self.hook_position = 'hobot'

    def knock_bucket(self):
        self.play('knock_get_bucket')

    def jump_tree(self):
        self.play('exit')

    def pump(self):
        if self.holding_bucket:
            self.play('fill_bucket', ['pump', 'hobot', 'bucket'])
        else:
            self.play('pump', ['pump', 'hobot'])

    def adjust_move(self, pos, delta, slide=True):
        if slide and pos[0] < 0:
            # Elevation
            new_delta = (delta[0], delta[1] + delta[0] * -0.2 * min(pos[1] * 4 + 2, 1.0))
            new_pos = FloorBase.adjust_move(self, pos, new_delta, slide)
            if new_pos != pos:
                return new_pos

        return FloorBase.adjust_move(self, pos, delta, slide)

    def check_interactions(self):
        hobot_pos = self.hobot.model.get_pos()

        if self.hook_position == 'original' and hobot_pos.y > -0.33 and hobot_pos.x > 0 and hobot_pos.x < 0.1:
            self.hobot.set_action(self.pickup_hook)
        elif hobot_pos.x < -0.14 and hobot_pos.x > -0.33 and hobot_pos.y > -0.32:
            self.hobot.set_action(self.jump_tree)
        elif hobot_pos.x > 0.4 and hobot_pos.y > -0.37 and hobot_pos.x < 0.6:
            self.hobot.set_action(self.pump)
        elif hobot_pos.x < -0.65:
            self.hobot.set_action(self.knock_bucket)
        else:
            self.hobot.clear_action()
