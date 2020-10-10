
import numpy as np

import retro_server
import retro

import forward
from forward import *

class RetroModule2(Module):
    actions_map = {
        'UP':        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        'DOWN':      [0, 0, 0, 0, 0, 1, 0, 0, 0],
        'LEFT':      [0, 0, 0, 0, 0, 0, 1, 0, 0],
        'RIGHT':     [0, 0, 0, 0, 0, 0, 0, 1, 0],
        'NONE':      [0, 0, 0, 0, 0, 0, 0, 0, 0],
        'B':         [1, 0, 0, 0, 0, 0, 0, 0, 0],
        'A':         [0, 0, 0, 0, 0, 0, 0, 0, 1],
    }

    games_list = sorted([
        "SuperMarioBros-Nes",
        "DonkeyKong-Nes",
        "SectionZ-Nes",
        "BubbleBobble-Nes",
        "NinjaGaiden-Nes",
        "Gradius-Nes",
        "ThunderAndLightning-Nes",
        "SuperC-Nes",
        "Spelunker-Nes"
    ])

    ## import time
    ## t0 = time.time()
    ## games_list = []
    ## for game in retro.data.list_games():
    ##     try:
    ##         if 'Nes' in game:
    ##             retro.make(game).close()
    ##             games_list.append(game)
    ##     except RuntimeError:
    ##         pass
    ## print()
    ## print(f'Game check {time.time() - t0:0.2f}s')

    def __init__(self):
        super().__init__()

        self.game = 'SuperMarioBros-Nes'
        self.states = retro.data.list_states(self.game)
        self.state = self.states[0]
        self.environment = None
        self.commitment_interval = 6
        self.encodings = False
        self.reset()

    def reset(self):
        if self.environment != None:
            self.environment.close()

        print("\n\n", self.state, "\n\n")

        self.environment = retro_server.RetroClient(game=self.game, state=self.state)
        self.frame = self.environment.frame()[::5, ::5]

    def game_select(self, game):
        self.game = game
        self.states = retro.data.list_states(self.game)
        self.state = self.states[0]
        self.reset()

    def state_select(self, state):
        self.state = state
        self.reset()

    def commitment_interval_set(self, interval):
        self.commitment_interval = interval

    def encoding_display_set(self, key, value):
        self.encodings = value

    def controls(self):
        take_action_f = lambda action: lambda: self.environment.step(RetroModule2.actions_map[action],
                                                                     commitment_interval=self.commitment_interval)

        return [Button(label=action, on_click=take_action_f(action))
                for action in RetroModule2.actions_map.keys()]

    def settings(self):
        if np.random.rand() < 1/6:
            self.frame = self.environment.frame()[::4, ::4]

        # colors, counts = np.unique(self.frame.reshape(-1, 3), axis=0, return_counts=True)
        # background = colors[counts.argmax()]

        return ApplicationSettings({
            'Title': self.game,
            'Thumbnail': Image(self.frame),
            # 'Background': f'rgb({background[0]}, {background[1]}, {background[2]})'
            # 'Background': 'Black'
        })

    def interface(self):
        data_elements = self.environment.interface_render2(self.encodings)

        game_choices = SelectionList(options=RetroModule2.games_list,
                                     selected_option=self.game,
                                     on_change=self.game_select)

        state_choices = SelectionList(options=self.states,
                                      selected_option=self.state,
                                      on_change=self.state_select,
                                      is_enabled=len(self.states) > 1)

        encodings_choices = CheckList(options=["Encodings"],
                                      selected_options=["Encodings"] if self.encodings else [],
                                      on_check=self.encoding_display_set)

        ss = ([self.settings()] + [game_choices, state_choices]
                + data_elements[:1]
                + [self.controls()]
                + [encodings_choices]
                + data_elements[1:]
                + [{"Commitment Interval": NumberInput(minimum=1, maximum=None,
                                                       value=self.commitment_interval,
                                                       on_change=self.commitment_interval_set)}]
                + [Button(label="RESET", on_click=self.reset)])

        return ss


class RetroModule1(Module):
    def __init__(self):
        super().__init__()

        self.value = 1

    def increment(self, n):
        print("\n\n-.")
        self.value += n

    def reset(self):
        self.value = 1

    def interface(self):
        array = 1 - np.random.rand(self.value, 15)*0.1
        array.reshape(-1)[self.value] = 0

        return [
            1, 2,
            self.value,
            Button(label="DOWN", on_click=lambda: self.increment(-1)),
            Button(label="UP", on_click=lambda: self.increment(1)),
            # Divider(),
            Image(array, display_scale=20),

            [(8,Image(np.random.rand(5,5), display_scale=7),7),
             [Image(np.random.rand(5,5)) for _ in range(2)]],
             
            Button(label="RESET", on_click=self.reset)
        ]

class CurvyThing(Module):

    def interface(self):
        zed = [np.random.randn(np.random.randint(10, 100), 6)**2 for index in range(60)]

        return [
            ApplicationSettings({'Background': 'Black'}),
            # ApplicationParameters({'variable1': self.variable1_set}),
            [Image(1 - z, color_map='Grayscale') for z in zed]
        ]


class Active(Module):

    def interface(self):
        import pickle
        imagez = pickle.load(open('data/active.pickle', 'rb'))

        return imagez

