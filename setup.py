from setuptools import setup

setup(
    name='hobots-ascent',
    version='1.0.1',
    options={
        'build_apps': {
            'include_patterns': {
                'assets/**',
                'settings.prc',
                'README.md',
            },
            'include_modules': {
                'run_game': [
                    'game.floors.title',
                    'game.floors.rusty',
                    'game.floors.nature',
                    'game.floors.time',
                    'game.floors.light',
                    'game.floors.bells',
                    'game.floors.end',
                ],
            },
            'gui_apps': {
                'run_game': 'run_game.py',
            },
            'icons': {
                'run_game': ['icon-256.png'],
            },
            'log_filename': "$USER_APPDATA/Hobot's Ascent/output.log",
            'log_append': False,
            'plugins': [
                'pandagl',
                'p3openal_audio',
                'p3fmod_audio',
            ],
        },
    }
)
