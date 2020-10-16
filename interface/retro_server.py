
import torch
import torch.nn.functional as F
import uuid
import numpy as np
import retro

import matplotlib.pyplot as plt

import forward

class Environment3:
    import pickle
    import sklearn.decomposition
    pca_blocks = pickle.load(open('models/blocks_75923_3_component.sklearn.decomposition.PCA.pickle', 'rb'))
    pca_encodings = pickle.load(open('models/pca_top_4_of_256.sklearn.decomposition.PCA.pickle', 'rb'))

    def __init__(self, game, state, actions=[], bk2_location=None):
        self.environment = retro.make(game=game, state=state, record=bk2_location)

        self.blocks_seen_images = []

        self.encodings = set()
        self.encodings_frame = set()
        self.encodings_all = []

        if bk2_location:
            random_key = str(uuid.uuid4())

            # Not sure how retro's recording mechanism works, but this seems
            # to force a bk2 file to be written in the bk2_location.
            self.environment.unwrapped.record_movie(f'/tmp/unused-{random_key}._bk2')

        asymmetric = torch.linspace(0.5, 1.5, 16*16*3)**3
        asymmetric = asymmetric.numpy()

        aa = torch.tensor(asymmetric).reshape(16, 16, 3).unsqueeze(0).permute(0, 3, 1, 2)
        filter_ = torch.tensor(aa, dtype=torch.float)
        self.filter_ = filter_ / 16 / 16 / 3 / 255

        self.encodings_frame_array = []

        self.frame = self.environment.reset()
        self.blocks_identify(self.frame)
        self.frame_index = 0
        self.frame_deltas_history = []

        self.actions_all = []
        self.commitment_intervals_all = []

        if actions:
            # note this produces different encodings, since the default
            # encodings are only sampled at the intervals and not on every step
            # for now, mainly meant to be used in generating replays
            # for action in actions:
            #     self.step(action, commitment_interval=1)
            for action in actions:
                self.environment.step(action)

    def actions_commitment_intervals(self):
        return list(zip(self.actions_all, self.commitment_intervals_all))

    def step(self, action, commitment_interval):
        for _ in range(commitment_interval):
            self.frame, reward, is_done, information = self.environment.step(action)
            self.frame_index += 1

        self.actions_all.append(action)
        self.commitment_intervals_all.append(commitment_interval)
        
        self.blocks_identify(self.frame)
        self.encodings_all.append(self.encodings_frame)

        return self.interface_render2(False)

    def close(self):
        self.environment.unwrapped.stop_record()
        if env := self.environment:
            env.render(close=True)
            env.close()

    def blocks_identify(self, frame):
        frame_chw = torch.tensor(frame, dtype=torch.float).permute(2, 0, 1)
        frame_chw = frame_chw.unsqueeze(0)

        unfolded = F.unfold(input=frame_chw,
                            kernel_size=(16, 16),
                            stride=(16, 16))

        blocks_chw = unfolded.squeeze().T.reshape(-1, 3, 16, 16)
        blocks_hwc = blocks_chw.permute(0, 2, 3, 1)

        # Encoding the full frame can acount for the "entropy" in the score
        # for better or worse, but here we are only encoding the middle region
        # to not spam the interface.
        blocks_hwc = blocks_hwc[4*15:-1*15]

        encodings_x = F.conv2d(input=frame_chw,
                               weight=self.filter_,
                               stride=16)

        encodings_x = encodings_x[:, :, 4:-1].squeeze()
        self.encodings_frame_array = encodings_x
        encodings_frame = encodings_x.flatten().numpy()

        new_encodings = set(encodings_frame).difference(self.encodings)

        # A single frame can contain multiple instances of a new block.
        # Uniqueness can be determined by the encoding.
        already_added = set()
        for encoding, block in zip(encodings_frame, blocks_hwc):
            if encoding in new_encodings and encoding not in already_added:
                already_added.add(encoding)

                image = forward.Image(array=block.byte(), display_scale=0.5)
                image.json() # cache base64 image before it is serialized for multiprocess

                self.blocks_seen_images.append((encoding, image))

        self.encodings.update(new_encodings)
        self.encodings_frame = encodings_frame

    def block_pca(self):
        import forward
        import pandas as pd

        frame_chw = torch.tensor(self.frame).permute(2, 0, 1)

        unfolded = F.unfold(input=frame_chw.unsqueeze(0).float(),
                            kernel_size=(16, 16),
                            stride=(16, 16))

        blocks_chw = unfolded.squeeze().T.reshape(-1, 3, 16, 16)
        frames_hwc = blocks_chw.permute(0, 2, 3, 1)

        ts = Environment3.pca_blocks.transform(frames_hwc.reshape(-1, 16*16*3))

        ts = ts[4*15:-1*15]
        # return pd.DataFrame(ts).describe()

        mins_maxs = np.array([[-1653.122679835112, 2280.690047041602],
                              [-1306.2888620104206, 1849.7466062093176],
                              [-1345.0536233578957, 2515.16959599922]])

        rescaled = (ts.T - mins_maxs[:,[0]]) / (mins_maxs[:,[1]] - mins_maxs[:,[0]])
        rescaled = (rescaled.T*255).astype(np.uint8)
        # rescaled = rescaled[:, [2, 0, 1]]
        rescaled = rescaled.reshape(-1, 15, 3)

        return forward.Image(rescaled, display_scale=12, inspect_form=ts.reshape(-1, 15, 3))

    def interface_render2(self, show_encodings):
        output_array = self.encodings_frame_array.numpy()

        height, width, depth = self.frame.shape

        regions = []
        if show_encodings:
            import hashlib
            to_number = lambda x: (int(hashlib.sha1(x.encode()).hexdigest(), 16) % 100_000_000) / 100_000_000

            output = [[str(e*10)[:4] for e in row]
                      for row in output_array.tolist()]

            seed = "6"
            for i in range(output_array.shape[0]):
                for j in range(output_array.shape[1]):
                    value = output_array[i][j].item()
                    r, g, b = (to_number(str(value) + seed + color) for color in ["Red", "Green", "Blue"])
                    regions.append(forward.Region(geometry=[[j*16, (i+4)*16], [j*16 + 16, (i+4)*16 + 16]],
                                                  color=[r, g, b, 0.2],
                                                  label=output[i][j],
                                                  label_color=[1, 1, 0, 0.75]))

        frame_index_region = forward.Region(geometry=[[width - 16, 0], [width, 8]],
                                            color=[0, 0, 0, 0],
                                            label=self.frame_index)

        regions.append(frame_index_region)

        block_images = [image_F for encoding, image_F in sorted(self.blocks_seen_images)]

        import matplotlib.pyplot as plt

        fig, ax1 = plt.subplots(figsize=(2, 2))

        ax1.imshow(np.diff(self.encodings_all or [[0]], axis=0), aspect='auto', cmap='gray')
        ax1.set_xticks(ticks=range(0, 9*15+1, 15))
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)
        ax1.set_title("Diffs", fontsize=8)

        filename1 = f'/tmp/{uuid.uuid4()}.png'
        plt.savefig(filename1, dpi=300)
        plt.close()

        fig, ax2 = plt.subplots(figsize=(2, 2))

        if self.encodings_all != []:
            all_x, all_y = Environment3.pca_encodings.transform(self.encodings_all).T
            ax2.plot(all_x, all_y, lw=0.2, color='gray')
            ax2.scatter(all_x, all_y, lw=0, c=np.linspace(1, 0, num=len(all_x)), cmap='gray', s=4);

        ax2.set_xlim(-0.76876307, 0.8960005)
        ax2.set_ylim(-0.7623395, 1.0323112)
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)
        ax2.set_title("Frame Encodings PCA", fontsize=8)

        filename2 = f'/tmp/{uuid.uuid4()}.png'
        plt.savefig(filename2, dpi=300)

        return {
            "Frame": self.frame,
            'FrameIndex': self.frame_index,
            "Elements": regions,
            "DiffsImageFile": filename1,
            "PCAEncodingsImageFile": filename2,
            "EncodingsArray": output_array,
            "PCA RGB": self.block_pca(),
            "Actions": forward.Image(self.actions_all),
            'Blocks': block_images
        }


class RetroClient:
    def __init__(self, game, state, actions=[], bk2_location=None):
        import multiprocessing as mp

        self.parent_connection, child_connection = mp.Pipe()
        process = mp.Process(target=RetroClient.dispatch, args=[child_connection])
        process.start()

        self.parent_connection.send(['__init__', {'game': game, 'state': state, 'actions': actions, 'bk2_location': bk2_location}])
        self.parent_connection.recv()
        self.parent_connection.send(['print', {}])
        self.parent_connection.recv()

    def dispatch(connection):
        while not connection.closed:
            method, kwargs = connection.recv()

            if method == '__init__':
                environment = Environment3(**kwargs)
                connection.send(None)

            elif method == 'print':
                print('inr', environment)
                connection.send(None)

            elif method == '[get_attribute]':
                result = environment.__getattribute__(kwargs['attribute'])
                connection.send(result)

            else:
                result = environment.__getattribute__(method)(**kwargs)
                connection.send(result)

    def step(self, action, commitment_interval):
        self.parent_connection.send(['step', {'action': action,
                                              'commitment_interval': commitment_interval}])
        return self.parent_connection.recv()

    def interface_render2(self, show_encodings):
        self.parent_connection.send(['interface_render2', {'show_encodings': show_encodings}])
        return self.parent_connection.recv()

    def close(self):
        self.parent_connection.send(['close', {}])
        return self.parent_connection.recv()

    def actions_commitment_intervals(self):
        self.parent_connection.send(['actions_commitment_intervals', {}])
        return self.parent_connection.recv()
