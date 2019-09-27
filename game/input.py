class Input:
    button_map = {
        'interact': ['e', 'space', 'enter'],
        'move-left': ['a', 'arrow_left'],
        'move-right': ['d', 'arrow_right'],
        'move-up': ['w', 'arrow_up'],
        'move-down': ['s', 'arrow_down'],
    }

    def __init__(self, mouse_watcher, keyboard_map):
        self.__is_button_down = mouse_watcher.is_button_down
        self.keyboard_map = keyboard_map

    def get_axis(self, axis):
        if axis == 'move-horizontal':
            return self.get_action('move-right') - self.get_action('move-left')
        elif axis == 'move-vertical':
            return self.get_action('move-up') - self.get_action('move-down')
        else:
            return 0.0

    def get_action(self, action):
        is_down = self.__is_button_down
        return any(is_down(mapped) for mapped in self.button_map.get(action, ()))
