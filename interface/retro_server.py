
import json
import http.server
import sys

import torch
import uuid
import numpy as np
import retro
import os

import matplotlib.pyplot as plt

import forward as fwd

def block_partition(matrix, block_width):
    matrix = matrix.reshape(-1, block_width, matrix.shape[0] // block_width, block_width, 3)
    matrix = matrix.transpose(2, 1).reshape(-1, block_width, block_width, 3)

    return matrix

class Environment3:
    def __init__(self, game, actions=[], bk2_location=None):
        self.environment = retro.make(game=game, record=bk2_location)

        self.blocks_seen = []
        self.blocks_seen_urls = []
        self.blocks_seen_images = []

        self.encodings = set()
        self.encodings_frame = set()
        self.encodings_all = []

        import sklearn.decomposition
        import pickle
        self.pca = pickle.load(open('models/pca_top_4_of_256.sklearn.decomposition.PCA', 'rb'))

        random_key = str(uuid.uuid4())
        self.image_files_folder = random_key
        os.makedirs('/tmp/' + self.image_files_folder)

        if bk2_location:
            # Not sure how retro's recording mechanism works, but this seems
            # to force a bk2 file to be written in the bk2_location.
            self.environment.unwrapped.record_movie(f'/tmp/unused-{random_key}._bk2')

        self.frame = self.environment.reset()
        self.blocks_identify(self.frame)
        self.frame_index = 0

        self.actions_all = []
        self.commitment_intervals_all = []

        asymmetric = torch.linspace(0.5, 1.5, 16*16*3)**3
        asymmetric = asymmetric.numpy()
        
        aa = torch.tensor(asymmetric).reshape(16, 16, 3).unsqueeze(0).permute(0, 3, 1, 2)
        filter_ = torch.tensor(aa, dtype=torch.float)
        self.filter_ = filter_ / 16 / 16 / 3 / 255

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

        return self.frame # , reward, is_done, information

    def close(self):
        self.environment.unwrapped.stop_record()
        if env := self.environment:
            env.render(close=True)
            env.close()
            # del self.environment

    # __del__ = close

    def blocks_identify(self, frame):
        obs = torch.tensor(frame)

        obs = torch.cat([obs,
                         torch.zeros(16, 240, 3)]).long()

        blocks = block_partition(obs, 16)

        blocks = blocks[4*15:-2*15]

        exponent = 2

        asymmetric = torch.linspace(0.5, 1.5, 16*16*3)**3
        # encodings = [((block.float() / 255 / 16 / 16).sum()**exponent).item() for block in blocks]
        # encodings = [hash(((block.float() / 255 / 16 / 16).sum()**exponent).item()) % 255 for block in blocks]
        # encodings = [((block.flatten().float() @ asymmetric / 16 / 16 / 3 / 255) - 0.5).item() for block in blocks]
        encodings_frame = [((block.flatten().float() @ asymmetric / 16 / 16 / 3 / 255)).item() for block in blocks]

        diffs = set(encodings_frame).difference(self.encodings)

        written = set()
        for encoding, block in zip(encodings_frame, blocks):
            if encoding in diffs and encoding not in written:
                written.add(encoding)

                plt.imsave(f"/tmp/{self.image_files_folder}/{str(encoding)[2:]}.png", block.byte().numpy())
                self.blocks_seen_urls.append(f"{self.image_files_folder}/{str(encoding)[2:]}.png")

                image = fwd.Image(array=block.byte(), display_scale=0.5)
                image.json() # ??

                self.blocks_seen_images.append((encoding, image))


        new_blocks = [block for encoding, block in zip(encodings_frame, blocks)
                            if encoding in diffs]

        new_blocks = set(tuple(block.flatten().tolist()) for block in new_blocks)
        new_blocks = [torch.tensor(block).reshape(16, 16, 3) for block in new_blocks]

        # update
        new_blocks = [block.tolist() for block in new_blocks]
        self.blocks_seen.extend(new_blocks)

        # if random.random() < 0.1:
        #     self.blocks_seen = sorted(self.blocks_seen, key=lambda x: tuple(torch.tensor(x).flatten().tolist()))

        self.encodings.update(diffs)
        self.encodings_frame = encodings_frame


    def interface_render(self):
        self.blocks_seen_urls = sorted(self.blocks_seen_urls)
        return self.frame.tolist(), list(self.encodings_frame), self.blocks_seen_urls, self.frame_index


    def interface_render2(self):
        import torch
        import torch.nn.functional as F

        import forward as fwd

        # self.blocks_seen_urls = sorted(self.blocks_seen_urls)
        # return self.frame.tolist(), list(self.encodings_frame), self.blocks_seen_urls, self.frame_index

        # ax1.hist(self.frame.ravel())
        # plt.plot(sorted(self.frame.ravel()))
        # plt.imshow(self.frame[:,:,0])

        # tensor = torch.tensor(np.stack(self.frames_all)).float()
        tensor = torch.tensor(self.frame, dtype=torch.float).unsqueeze(0)
        images = tensor.permute(0, 3, 1, 2)
        
        # id_ = str(uuid.uuid4())
        # np.savez_compressed(f'/tmp/{id}.npz', np.stack(self.frames_all).astype('uint8'))

        output = F.conv2d(input=images,
                          weight=self.filter_,
                          stride=16)

        output = output[:, :, 4:-1].squeeze()
        output_array = output

        output = [[str(e*10)[:4] for e in row]
                  for row in output.tolist()]

        height, width, depth = self.frame.shape

        import hashlib
        to_number = lambda x: (int(hashlib.sha1(x.encode()).hexdigest(), 16) % 100_000_000) / 100_000_000

        regions = []
        seed = "6"
        for i in range(output_array.shape[0]):
            for j in range(output_array.shape[1]):
                value = output_array[i][j].item()
                r, g, b = (to_number(str(value) + seed + color) for color in ["Red", "Green", "Blue"])
                regions.append(fwd.Region(geometry=[[j*16, (i+4)*16], [j*16 + 16, (i+4)*16 + 16]],
                                          color=[r, g, b, 0.2],
                                          label=output[i][j],
                                          label_color=[1, 1, 0, 0.75]))

        frame_index_region = fwd.Region(geometry=[[width - 16, 0], [width, 8]],
                                        color=[0, 0, 0, 0],
                                        label=self.frame_index)

        regions.append(frame_index_region)

        block_images = [image_F for encoding, image_F in sorted(self.blocks_seen_images)]

        import matplotlib.pyplot as plt

        fig, ax1 = plt.subplots(figsize=(2, 2))

        ax1.imshow(np.diff(self.encodings_all or [[0]], axis=0), aspect='auto', cmap='gray')
        ax1.set_xticks(ticks=range(0, 9*15+1, 15));
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)
        ax1.set_title("Diffs", fontsize=8)

        filename1 = f'/tmp/{uuid.uuid4()}.png'
        plt.savefig(filename1, dpi=300)
        plt.close()

        fig, ax2 = plt.subplots(figsize=(2, 2))

        if self.encodings_all != []:
            all_x, all_y = self.pca.transform(self.encodings_all).T
            ax2.plot(all_x, all_y, lw=0.2, color='gray')
            ax2.scatter(all_x, all_y, lw=0, c=np.linspace(1, 0, num=len(all_x)), cmap='gray', s=4);

        ax2.set_xlim(-0.76876307, 0.8960005)
        ax2.set_ylim(-0.7623395, 1.0323112)
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)
        ax2.set_title("PCA", fontsize=8)

        filename2 = f'/tmp/{uuid.uuid4()}.png'
        plt.savefig(filename2, dpi=300)

        return [fwd.Image(self.frame, elements=regions, display_scale=2),
                fwd.Image(output_array, display_scale=12),

                {"R": fwd.Image(self.frame[::2,::2,0], color_map='Grayscale'),
                 "G": fwd.Image(self.frame[::2,::2,1], color_map='Grayscale'),
                 "B": fwd.Image(self.frame[::2,::2,2], color_map='Grayscale')},

                fwd.Image(self.actions_all),
                fwd.FileImage(file=filename1),
                fwd.FileImage(file=filename2),
                fwd.ArrayPlot3D(np.random.rand(5, 5, 5)),

                fwd.Array(output),

                {'Frame Index': self.frame_index,
                 'Blocks Count': len(block_images)},
                {'Blocks': block_images}
        ]


class RetroClient:
    def __init__(self, game, actions=[], bk2_location=None):
        import multiprocessing as mp

        self.parent_connection, child_connection = mp.Pipe()
        process = mp.Process(target=RetroClient.dispatch, args=[child_connection])
        process.start()

        self.parent_connection.send(['__init__', {'game': game, 'actions': actions, 'bk2_location': bk2_location}])
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

    def interface_render(self):
        self.parent_connection.send(['interface_render', {}])
        return self.parent_connection.recv()

    def interface_render2(self):
        self.parent_connection.send(['interface_render2', {}])
        return self.parent_connection.recv()

    def close(self):
        self.parent_connection.send(['close', {}])
        return self.parent_connection.recv()

    def image_files_folder(self):
        self.parent_connection.send(['[get_attribute]', {'attribute': 'image_files_folder'}])
        return self.parent_connection.recv()

    def actions_commitment_intervals(self):
        self.parent_connection.send(['actions_commitment_intervals', {}])
        return self.parent_connection.recv()
