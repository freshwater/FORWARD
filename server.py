
import http.server

import json
import time
import torch
import retro

import random
import os
import matplotlib.pyplot as plt

def block_partition(matrix, block_width):
    matrix = matrix.reshape(-1, block_width, matrix.shape[0] // block_width, block_width, 3)
    matrix = matrix.transpose(2, 1).reshape(-1, block_width, block_width, 3)

    return matrix

class Environment2:
    def __init__(self):
        self.environment = retro.make(game='SuperMarioBros-Nes')
        # self.environment = retro.make(game='NinjaGaiden-Nes')
        # self.environment = retro.make(game='DonkeyKong-Nes')
        # self.environment = retro.make(game='Airstriker-Genesis')

        self.blocks_seen = []
        self.blocks_seen_urls = []

        self.encodings = set()
        self.encodings_frame = set()

        random_key = str(random.random())[2:]
        self.image_files_folder = random_key
        os.makedirs('/tmp/' + self.image_files_folder)

        self.frame = self.environment.reset()
        self.blocks_identify(self.frame)

    def step(self, action, commitment_interval):
        t0 = time.time()
        for _ in range(commitment_interval):
            self.frame, reward, is_done, information = self.environment.step(action)
        
        self.blocks_identify(self.frame)

        return self.frame # , reward, is_done, information

    def close(self):
        self.environment.render(close=True)
        self.environment.close()

    __del__ = close

    def blocks_identify(self, frame):
        t0 = time.time()
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
        return self.frame.tolist(), list(self.encodings_frame), self.blocks_seen_urls



class Server(http.server.BaseHTTPRequestHandler):
    with open('index.html') as file:
        html_index_file = file.read()

    environments = {}
    blocks_seen = {}

    actions = {
        'Left':      [0, 0, 0, 0, 0, 0, 1, 0, 0],
        'Right':     [0, 0, 0, 0, 0, 0, 0, 1, 0],
        'Jump':      [0, 0, 0, 0, 0, 0, 0, 0, 1],
        'None':      [0, 0, 0, 0, 0, 0, 0, 0, 0],
        'Crouch':    [0, 0, 0, 0, 0, 1, 0, 0, 0],
        # 'Dash':    [0, 0, 1, 0, 0, 0, 0, 0, 0],
        'Dash':      [1, 0, 0, 0, 0, 0, 0, 0, 0],
        'RightDash': [1, 0, 0, 0, 0, 0, 0, 1, 0],
        'LeftJump':  [0, 0, 0, 0, 0, 0, 1, 0, 1],
        'RightJump': [0, 0, 0, 0, 0, 0, 0, 1, 1]
    }

    def request_process(self, request):
        request_name = request["Request"]
        client_id = request["ClientId"]

        if request_name == "Reset":
            if environment := Server.environments.get(client_id):
                environment.close()

            Server.environments[client_id] = Environment2()

            frame, encodings, blocks = Server.environments[client_id].interface_render()

            return {
                'Observation': frame,
                'BlockEncodings': encodings,
                'Blocks': blocks
            }

        elif request_name == "Action":
            commitment_interval = request["CommitmentInterval"]
            action = Server.actions[request["Action"]]

            environment = Server.environments[client_id]

            # action = environment.action_space.sample()
            unknown = [0, 0, 0, 0, 0, 1, 0, 0, 0]
            unknown = [0, 0, 0, 0, 1, 0, 0, 0, 0]
            unknown = [0, 0, 0, 1, 0, 0, 0, 0, 0]
            unknown = [0, 0, 1, 0, 0, 0, 0, 0, 0]
            unknown = [0, 1, 0, 0, 0, 0, 0, 0, 0]
            unknown = [1, 0, 0, 0, 0, 0, 0, 0, 0]

            print("ACTION", action)

            Server.environments[client_id].step(action, commitment_interval)
            frame, encodings, blocks = Server.environments[client_id].interface_render()

            return {
                'Observation': frame,
                'BlockEncodings': encodings,
                'Blocks': blocks
            }


    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        request = json.loads(data)

        print("Request")
        print(json.dumps(request).encode()[:800])

        t0 = time.time()
        response = self.request_process(request)
        print(f'QueryTime: {time.time() - t0}')

        self.wfile.write(json.dumps(response).encode())


    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            with open('index.html') as file:
                Server.html_index_file = file.read()

            response = Server.html_index_file

            self.wfile.write(response.encode())

        else:
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Cache-Control', 'max-age=30')
            self.end_headers()

            print(".", end="")

            with open('/tmp' + self.path, 'rb') as file:
                self.wfile.write(file.read())


def run(port=80):
    print("Listening on port", str(port) + ".")

    httpd = http.server.HTTPServer(('', port), Server)
    httpd.serve_forever()


run()
