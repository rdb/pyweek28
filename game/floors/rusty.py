from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait

from ..floor import FloorBase


VALVE_POSITIONS = [0.66, 0.415, 0.28, 0.025]
VALVE_WIDTH = 0.15


class Floor(FloorBase):
    model_path = 'floors/rusty/scene.bam'
    walkable_path = 'floors/rusty/walkable.png'
    music_path = 'floors/rusty/music.ogg'
    sound_path = 'floors/rusty/sfx/'
    sound_names = [
        "entrance",
        "air_state",
        "big_pipe_rattling",
        "dial_pipes_rattling",
        "fly_up",
        "valve_0_turn_off",
        "valve_0_turn_on",
        "valve_x_turn_onoff",
    ]

    walkable_y_offset = 0.05

    def __init__(self, parent):
        FloorBase.__init__(self, parent)
        actor = self.actor

        # Make subparts for all the things that can animate independently.
        actor.make_subpart('airflow', ['airflow'])

        # Parts for the valves.
        self.valve_states = []
        for valve in range(4):
            bone_name = 'valve' + str(valve)
            actor.make_subpart(bone_name, [bone_name])
            self.valve_states.append(False)

        # All these parts can rattle.
        for rattler in ['big pipe', 'dial pipes', 'front tank', 'giant pipe left', 'rear tank', 'side pipe']:
            anim_name = rattler.replace(' ', '_') + '_rattling'
            actor.make_subpart(rattler, [rattler])

        self.indicator = self.actor.control_joint(None, 'modelRoot', 'indicator')
        self.indicator_interval = None

        self.rattle('side pipe')

        self.airflow = False

    def start(self):
        self.play('entrance', ['hobot'], sound=self.sfx["entrance"])

    def toggle_valve(self, valve):
        if self.hobot.locked:
            return
        state = not self.valve_states[valve]

        if valve == 0:
            sound_on = self.sfx["valve_0_turn_on"]
            sound_off = self.sfx["valve_0_turn_off"]
        else:
            sound_on = sound_off = self.sfx["valve_x_turn_onoff"]

        wait_time = 1.5 if valve == 0 else 1.0
        # After a second of playing the animation, call on_valve_changed
        extra_interval = Sequence(Wait(wait_time), Func(self.on_valve_changed))
        if state:
            self.play('valve_{}_turn_on'.format(valve), ['hobot', 'valve' + str(valve)], extra_interval=extra_interval, sound=sound_on)
        else:
            self.play('valve_{}_turn_off'.format(valve), ['hobot', 'valve' + str(valve)], extra_interval=extra_interval, sound=sound_off)

        self.valve_states[valve] = state

    def on_valve_changed(self):
        if self.valve_states[0]:
            self.rattle('big pipe')

            # How much is flowing to the tank?
            flow = 0
            if not self.valve_states[2]:
                flow += 3

                if not self.valve_states[1]:
                    flow -= 1

                if not self.valve_states[3]:
                    flow -= 1

            self.set_rattle_state('front tank', (flow >= 2))
            self.set_rattle_state('rear tank', (flow >= 1))
            self.set_rattle_state('dial pipes', (flow >= 2))
            self.set_rattle_state('giant pipe left', (flow >= 3))

            self.set_dial(flow / 3.0)

            self.set_airflow(flow >= 3)
        else:
            # Stop rattling everything.
            for part in ['big pipe', 'dial pipes', 'front tank', 'giant pipe left', 'rear tank']:
                self.stop_rattle(part)
            self.sfx["big_pipe_rattling"].stop()
            self.sfx["dial_pipes_rattling"].stop()

            self.set_dial(0.0)
            self.set_airflow(False)

    def set_rattle_state(self, part, state):
        if state:
            self.rattle(part)
        else:
            self.stop_rattle(part)

    def rattle(self, part):
        "Rattles the given rattleable part."

        if part == "big pipe":
            self.sfx["big_pipe_rattling"].setLoop(True)
            self.sfx["big_pipe_rattling"].play()
        elif part == "dial pipes":
            self.sfx["dial_pipes_rattling"].setLoop(True)
            self.sfx["dial_pipes_rattling"].play()

        anim_name = part.replace(' ', '_') + '_rattling'

        for control in self.actor.get_anim_controls(anim_name, part):
            if not control.playing:
                print("Rattling {}".format(part))
                control.loop(False)

    def stop_rattle(self, part):
        anim_name = part.replace(' ', '_') + '_rattling'

        for control in self.actor.get_anim_controls(anim_name, part):
            if control.playing:
                print("Stopping rattle of {}".format(part))
                control.stop()

    def set_dial(self, pos):
        if self.indicator_interval:
            self.indicator_interval.pause()

        print("Setting dial to {}".format(pos))
        new_h = 140 - pos * 270
        self.indicator_interval = self.indicator.hprInterval(0.3, (new_h, 0, 0), blendType='easeInOut')
        self.indicator_interval.start()

    def set_airflow(self, flow):
        if self.airflow != flow:
            if flow:
                print("Turning on airflow")
            else:
                print("Turning off airflow")

        self.airflow = flow

        control = self.actor.get_anim_controls('air_state', 'airflow')[0]
        if control.playing:
            if not flow:
                control.stop()
                self.actor.pose('air_turn_on', 0, partName='airflow')
            return

        control2 = self.actor.get_anim_controls('air_turn_on', 'airflow')[0]
        if control2.playing:
            if not flow:
                control2.stop()
                self.actor.pose('air_turn_on', 0, partName='airflow')
            return

        if flow:
            control.loop(True)

    def finish(self):
        self.play('fly_up', ['hobot'], callback=base.next_floor, sound=self.sfx["fly_up"])

    def check_interactions(self):
        hobot_pos = self.hobot.model.get_pos()

        if hobot_pos.y > -0.35:
            self.hobot.model.set_z(12.8201)
        else:
            self.hobot.model.set_z(15)

        if self.airflow and hobot_pos.y > -0.35 and hobot_pos.y < -0.29 and hobot_pos.x > 0.13 and hobot_pos.x < 0.31:
            self.hobot.clear_action()
            self.finish()
        elif hobot_pos.y > -0.31:
            closest_valve = None
            closest_valve_dist = 1000

            for i, valve_x in enumerate(VALVE_POSITIONS):
                if i > 0:
                    valve_dist = abs(hobot_pos.x - valve_x)
                    if valve_dist < closest_valve_dist:
                        closest_valve_dist = valve_dist
                        closest_valve = i

            if closest_valve_dist * 2 < VALVE_WIDTH:
                self.hobot.set_action(lambda: self.toggle_valve(closest_valve))
            else:
                self.hobot.clear_action()
            return
        elif hobot_pos.y > -0.4 and hobot_pos.x > 0.54:
            self.hobot.set_action(lambda: self.toggle_valve(0))
        else:
            self.hobot.clear_action()
