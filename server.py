
import http.server

import json
import time
import torch
import numpy as np
import retro

import random
import os
import matplotlib.pyplot as plt

import retro_server


class Server(http.server.BaseHTTPRequestHandler):
    with open('index.html') as file:
        html_index_file = file.read()

    environments = {}
    blocks_seen = {}

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
    ## print(f'Game check time {time.time() - t0:0.2f}s')

    actions = {
        'Up':        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        'Down':      [0, 0, 0, 0, 0, 1, 0, 0, 0],
        'Left':      [0, 0, 0, 0, 0, 0, 1, 0, 0],
        'Right':     [0, 0, 0, 0, 0, 0, 0, 1, 0],
        'None':      [0, 0, 0, 0, 0, 0, 0, 0, 0],
        'B':         [1, 0, 0, 0, 0, 0, 0, 0, 0],
        'A':         [0, 0, 0, 0, 0, 0, 0, 0, 1],
        'RightDash': [1, 0, 0, 0, 0, 0, 0, 1, 0],
        'LeftJump':  [0, 0, 0, 0, 0, 0, 1, 0, 1],
        'RightJump': [0, 0, 0, 0, 0, 0, 0, 1, 1]
    }

    def request_process(self, request):
        request_name = request["Request"]
        client_id = request["ClientId"]

        if request_name == "AvailableGames":
            return {
                "AvailableGames": Server.games_list
            }

        elif request_name == "ImageUrl":
            import uuid

            image_files_folder = Server.environments[client_id].image_files_folder()
            file_name = f"{image_files_folder}/{uuid.uuid4()}.png"
            frame, _encodings, _blocks, _frame_index = Server.environments[client_id].interface_render()
            plt.imsave("/tmp/" + file_name, np.array(frame).astype(np.uint8))

            return file_name

        elif request_name == "ResourceURL":
            game = request['Game']

            import os
            os.makedirs('/tmp/bobbity')
            environment = RetroClient(game=game, bk2_location='/tmp/bobbity')

            for action, commitment_interval in actions_commitment_intervals:
                environment.step(action, commitment_interval)

            environment.close()
            print("BOB", os.listdir('/tmp/bobbity'))

            return "NORB"

        elif request_name == "Reset":
            game = request["Game"]

            if environment := Server.environments.get(client_id):
                environment.close()

            random_port = random.randint(1024, 65536)
            Server.environments[client_id] = retro_server.RetroClient(game=game, port=random_port)
            print("RETROCLIENT")

            frame, encodings, blocks, frame_index = Server.environments[client_id].interface_render()

            return {
                'Observation': frame,
                'BlockEncodings': encodings,
                'Blocks': blocks,
                'FrameIndex': frame_index
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

            import time
            t0 = time.time()
            Server.environments[client_id].step(action, commitment_interval)
            frame, encodings, blocks, frame_index = Server.environments[client_id].interface_render()
            print("TIME", time.time() - t0)

            return {
                'Observation': frame,
                'BlockEncodings': encodings,
                'Blocks': blocks,
                'FrameIndex': frame_index
            }

        raise NotImplementedError(request)


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
