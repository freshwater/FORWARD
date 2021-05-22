
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
        self.commitment_interval = 16
        self.encodings = False
        self.reset()

    def reset(self):
        if self.environment != None:
            self.environment.close()

        self.frame_previous = None
        self.index_previous = -1
        self.frame_history = []
        self.frame_deltas_history = []
        self.last_interface = None
        self.environment = retro_server.RetroClient(game=self.game, state=self.state)

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

    def step(self, action, commitment_interval):
        if (self.game == 'SuperMarioBros-Nes'
            and self.index_previous < 120
            and action == RetroModule2.actions_map['RIGHT']):
            commitment_interval = 22
            action = [a + b for a, b in zip(RetroModule2.actions_map['B'], RetroModule2.actions_map['RIGHT'])]
            # ☝️😂👌👌

        self.last_interface = self.environment.step(action, commitment_interval)

    def controls(self):
        take_action_f = lambda action: lambda: self.step(RetroModule2.actions_map[action],
                                                         commitment_interval=self.commitment_interval)

        return [Button(label=action, on_click=take_action_f(action))
                for action in RetroModule2.actions_map.keys()]

    def settings(self):
        # colors, counts = np.unique(self.frame.reshape(-1, 3), axis=0, return_counts=True)
        # background = colors[counts.argmax()]

        return ApplicationSettings({
            'Title': self.game,
            'Thumbnail': Image(self.frame[::4, ::4]),
            # 'Background': f'rgb({background[0]}, {background[1]}, {background[2]})'
            # 'Background': 'Black'
        })

    def interface(self):
        # Both Retro and PyTorch have issues with multiple instances on a single process,
        # necessitating a multiprocess mechanism.
        # Generally we try to keep as much data on this side of the serialization.
        # Controls/events in particular are easier to use on this side of the boundary
        # since they can't directly alter state from the other side.

        if self.last_interface is not None:
            objects = self.last_interface
        else:
            objects = self.environment.interface_render2(self.encodings)

        self.frame = objects["Frame"]

        frame = self.frame

        if objects["FrameIndex"] != self.index_previous:
            # add alpha channel
            padded = 255 * np.ones(np.array(frame.shape) + [0, 0, 1])
            padded[:, :, :frame.shape[2]] = frame
            frame = padded

            # make background transparent
            colors, counts = np.unique(frame.reshape(-1, 4), axis=0, return_counts=True)
            background = colors[counts.argmax()]
            mask = (1 + frame.reshape(-1, 4)).dot(1 + background) == (1 + background).dot(1 + background)
            frame.reshape(-1, 4)[mask] = [0, 0, 0, 0]

            self.frame_history.append(frame[::2, ::2])

        if self.frame_previous is not None:
            mask = ((1 + frame.reshape(-1, 4)).dot(np.array([1, 2, 4, 8])) ==
                    (1 + self.frame_previous.reshape(-1, 4)).dot(np.array([1, 2, 4, 8])))

            frame_x = frame.copy()
            frame_x.reshape(-1, 4)[mask] = [0, 0, 0, 0]
            frame_x.reshape(-1, 4)[~mask] = [0.5, 0.5, 0.5, 1]

            if objects["FrameIndex"] != self.index_previous:
                self.frame_deltas_history.append(frame_x[::3, ::3])

        self.index_previous = objects["FrameIndex"]
        self.frame_previous = frame
        empty = np.ones(frame[::3, ::3].shape)
        empty[::,::,3] = 0

        game_choices = SelectionList(options=RetroModule2.games_list,
                                     selected_option=self.game,
                                     on_change=self.game_select)

        game_state_choices = SelectionList(options=self.states,
                                           selected_option=self.state,
                                           on_change=self.state_select,
                                           is_enabled=len(self.states) > 1)

        encodings_choices = CheckList(options=["Encodings"],
                                      selected_options=["Encodings"] if self.encodings else [],
                                      on_check=self.encoding_display_set)

        # self.frame[:,range(16, 240, 16)] = [255, 255, 0]
        # self.frame[range(16, 224, 16), :] = [255, 255, 0]

        return [
            self.settings(),
            game_choices,
            game_state_choices,
            # Image(self.frame, elements=objects["Elements"], display_scale=2),
            Image(self.frame, display_scale=1.5),
            self.controls(),

            {"Encodings": Image(objects["EncodingsArray"], display_scale=12),
             "PCA RGB": objects["PCA RGB"]},

            {"R": Image(self.frame[::2,::2,0], color_map='Grayscale'),
             "G": Image(self.frame[::2,::2,1], color_map='Grayscale'),
             "B": Image(self.frame[::2,::2,2], color_map='Grayscale')},

            ArrayPlot3D(self.frame_history, _sequence_hacks_much_spooky_do_not_use="secr3tcode"),

            objects["Actions"],
            FileImage(objects["DiffsImageFile"]),
            FileImage(objects["PCAEncodingsImageFile"]),
            ArrayPlot3D(self.frame_deltas_history or [empty], _sequence_hacks_much_spooky_do_not_use="secr3tcode"),

            {"Frame Index": objects["FrameIndex"],
             "Blocks Count": len(objects["Blocks"])},
            {"Blocks": objects["Blocks"]},

            [{"Frame Skip": NumberInput(minimum=1, maximum=None,
                                        value=self.commitment_interval,
                                        on_change=self.commitment_interval_set)}],
            Button(label="RESET", on_click=self.reset)
        ]


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

