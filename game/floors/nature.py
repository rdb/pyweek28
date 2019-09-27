from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval

from ..floor import FloorBase


class Floor(FloorBase):
    # left, right, bottom, top
    boundaries = (-0.85, 0.7, -0.45, -0.28)

    def __init__(self, parent):
        FloorBase.__init__(self, parent, 'nature_mergedhobot.bam')
        actor = self.actor

        self.play('entrance')

        self.hook_position = 'original'

    def pickup_hook(self):
        self.play('grab_hook_wall')
        self.hook_position = 'hobot'

    def jump_tree(self):
        self.play('exit')

    def adjust_to_bounds(self, x, y, bounds):
        bounds = list(bounds)

        if x < 0:
            slope = -x * 0.2
            bounds[3] += slope

        bounds[0] = 0.81 * y - 0.435
        bounds[1] = -0.81 * y + 0.435

        # y = -0.166888, bounds[0] = -0.57
        # y = -0.45, bounds[0] = -0.8

        return FloorBase.adjust_to_bounds(self, x, y, bounds)

    def check_interactions(self):
        hobot_pos = self.hobot.model.get_pos()

        if self.hook_position == 'original' and hobot_pos.y > -0.33 and hobot_pos.x > 0 and hobot_pos.x < 0.1:
            self.hobot.set_action(self.pickup_hook)
        elif hobot_pos.x < -0.14 and hobot_pos.x > -0.33 and hobot_pos.y > -0.32:
            self.hobot.set_action(self.jump_tree)
        else:
            self.hobot.clear_action()
