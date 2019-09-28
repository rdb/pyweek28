from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, ActorInterval

from ..floor import FloorBase


TREE_WATER_COUNT = 2


class Floor(FloorBase):
    model_path = 'floors/nature/scene.bam'
    walkable_path = 'floors/nature/walkable.png'
    music_path = 'floors/nature/music.ogg'
    sound_path = 'floors/nature/sfx/'
    sound_names = [
        "entrance",
        "exit",
        "fill_bucket",
        "pump",
        "grab_hook_plank",
        "knock_get_bucket",
        "tree_grow_0",
        "tree_grow_1",
        "tree_grow_2",
    ]

    walkable_y_offset = 0.025

    free_hobot_z = 20

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor

        actor.make_subpart('pump', ['pump plunger', 'pump handle'])
        actor.make_subpart('drip', ['drip'])
        actor.make_subpart('bucket', ['bucket'])
        actor.make_subpart('plank', ['plank'])
        actor.make_subpart('hook', ['hook'])
        actor.make_subpart('tree', ['sapling', 'tree main', 'tree bottom bra', 'tree top', 'tree top branch', 'tree mid', 'tree shadow'])
        actor.make_subpart('entrance', ['entrance cover'])
        actor.make_subpart('sky', ['sky'])

        self.actor.pose('sky_scroll', 1, partName='sky')

        actor.pose('tree_grow', 30, partName='tree')
        self.tree_frame = 30

        self.hook_position = 'wall'
        self.bucket_position = 'plank'
        self.bucket_knocked = False
        self.bucket_filled = False
        self.water_count = 0

    def start(self):
        self.play('entrance', ['hobot', 'entrance'], sound=self.sfx["entrance"])


    def pickup_hook(self):
        if self.hook_position == 'wall':
            self.play('grab_hook_wall', ['hobot', 'hook'], callback=self.on_pickup_hook,
                sound=self.sfx["grab_hook_plank"])
        elif self.hook_position == 'plank':
            self.play('grab_hook_plank', ['hobot', 'hook'], callback=self.on_pickup_hook,
                sound=self.sfx["grab_hook_plank"])

    def on_pickup_hook(self):
        self.hook_position = 'hobot'
        self.grab_joint('hook')
        self.switch_to_free_hobot()

    def knock_bucket(self):
        if self.hook_position == 'hobot':
            self.play('knock_get_bucket', ['hobot', 'bucket', 'hook', 'plank'], callback=self.on_grab_bucket,
                sound=self.sfx["knock_get_bucket"])
            self.hook_position = 'plank'
            self.bucket_knocked = True

    def on_grab_bucket(self):
        if self.carrying_joint_name == 'hook':
            self.release_joint('hook')
        self.bucket_position = 'hobot'
        self.grab_joint('bucket')
        self.switch_to_free_hobot()

    def jump_tree(self):
        if self.hook_position == 'hobot':
            self.play('exit', ['hobot', 'tree', 'hook'], sound=self.sfx["exit"], callback=base.next_floor)

    def pump(self):
        if self.bucket_position == 'hobot':
            self.play('fill_bucket', ['hobot', 'pump', 'bucket', 'drip'],
                sound=self.sfx["fill_bucket"])
            self.bucket_filled = True
        else:
            self.play('pump', ['hobot', 'pump', 'drip'], sound=self.sfx["pump"])

    def water_rock(self):
        if self.water_count >= TREE_WATER_COUNT:
            return

        self.water_count += 1
        extra_interval = Sequence(Wait(1.0), Func(self.grow_tree))
        if self.water_count >= TREE_WATER_COUNT:
            self.play('water_rock_last', ['hobot', 'bucket', 'drip'], extra_interval=extra_interval, callback=self.on_drop_bucket)
        else:
            self.play('water_rock_repeat', ['hobot', 'bucket', 'drip'], extra_interval=extra_interval)
        self.bucket_filled = False

    def on_drop_bucket(self):
        self.release_joint('bucket')
        self.bucket_position = 'tree'
        self.switch_to_free_hobot()

    def grow_tree(self):
        to_frame = self.tree_frame
        if self.water_count >= 2:
            to_frame = None
            self.sfx["tree_grow_2"].play()
        elif self.water_count >= 1:
            to_frame = 80
            self.sfx["tree_grow_1"].play()
        else:
            to_frame = 30
            self.sfx["tree_grow_0"].play()

        if to_frame != self.tree_frame:
            print("Growing tree from frame {} to frame {}".format(self.tree_frame, to_frame))
            self.play('tree_grow', ['tree'], from_frame=self.tree_frame, to_frame=to_frame)
            self.tree_frame = to_frame

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

        if hobot_pos.y > -0.25:
            self.hobot.model.set_z(8)
        elif hobot_pos.x > 0 and hobot_pos.y > -0.31:
            self.hobot.model.set_z(8)
        else:
            self.hobot.model.set_z(20)

        if self.hook_position == 'wall' and hobot_pos.y > -0.33 and hobot_pos.x > 0 and hobot_pos.x < 0.1:
            self.hobot.set_action(self.pickup_hook)
        elif self.water_count >= TREE_WATER_COUNT and self.hook_position == 'hobot' and hobot_pos.x < -0.14 and hobot_pos.x > -0.35 and hobot_pos.y > -0.32:
            self.hobot.set_action(self.jump_tree)
        elif hobot_pos.x > 0.4 and hobot_pos.y > -0.37 and hobot_pos.x < 0.6 and self.hook_position != 'hobot' :
            self.hobot.set_action(self.pump)
        elif hobot_pos.x < -0.65 and self.hook_position == 'hobot' and not self.bucket_knocked and self.bucket_position != 'hobot':
            self.hobot.set_action(self.knock_bucket)
        elif hobot_pos.x < -0.65 and self.hook_position == 'plank' and self.bucket_position != 'hobot':
            self.hobot.set_action(self.pickup_hook)
        elif self.bucket_position == 'hobot' and self.bucket_filled and hobot_pos.x < -0.3 and hobot_pos.x > -0.55 and hobot_pos.y > -0.32:
            self.hobot.set_action(self.water_rock)
        else:
            self.hobot.clear_action()
