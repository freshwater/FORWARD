
import json
import http.server
import sys

import torch
import random
import numpy as np
import retro
import os

import matplotlib.pyplot as plt
import requests

def post_request_json(url, data):
    import urllib

    req = urllib.request.Request(url, bytes(json.dumps(data), encoding='utf-8'))
    r = urllib.request.urlopen(req).read()

    return json.loads(r)


def block_partition(matrix, block_width):
    matrix = matrix.reshape(-1, block_width, matrix.shape[0] // block_width, block_width, 3)
    matrix = matrix.transpose(2, 1).reshape(-1, block_width, block_width, 3)

    return matrix

class Environment3:
    def __init__(self, game, actions=[], bk2_location=None):
        self.environment = retro.make(game=game, record=bk2_location)

        self.blocks_seen = []
        self.blocks_seen_urls = []

        self.encodings = set()
        self.encodings_frame = set()

        random_key = str(random.random())[2:]
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


class RetroClient:
    def __init__(self, port, game, actions=[], bk2_location=None):
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

    def close(self):
        self.parent_connection.send(['close', {}])
        return self.parent_connection.recv()

    def image_files_folder(self):
        self.parent_connection.send(['[get_attribute]', {'attribute': 'image_files_folder'}])
        return self.parent_connection.recv()

    def actions_commitment_intervals(self):
        self.parent_connection.send(['actions_commitment_intervals', {}])
        return self.parent_connection.recv()


class RetroClient0:
    def __init__(self, port, game, actions=[], bk2_location=None):
        self.url = f'http://localhost:{port}'

        import subprocess
        subprocess.Popen(["python3", __file__, str(port)])

        while True:
            try:
                content = requests.get(self.url).content
                break
            except requests.exceptions.ConnectionError:
                import time
                time.sleep(0.05)

        self.initialize(game, actions, bk2_location)

    def initialize(self, game, actions, bk2_location):
        return post_request_json(self.url, {
            "Request": "Initialize",
            "Game": game,
            "Actions": actions,
            "bk2_location": bk2_location
        })

    def step(self, action, commitment_interval):
        response = requests.post(self.url, json={
            "Request": "MethodExecute",
            "Method": "step",
            "Arguments": [action, commitment_interval]
        })

        return response.json()

    def interface_render(self):
        response = requests.post(self.url, json={
            "Request": "MethodExecute",
            "Method": "interface_render",
            "Arguments": []
        })

        return response.json()

    def close(self):
        response = requests.post(self.url, json={
            "Request": "MethodExecute",
            "Method": "close",
            "Arguments": []
        })

        return response.json()

    def image_files_folder(self):
        return requests.post(self.url, json={
            "Request": "PropertyGet",
            "Property": "image_files_folder"
        }).json()

    def actions_commitment_intervals(self):
        return requests.post(self.url, json={
            "Request": "MethodExecute",
            "Method": "actions_commitment_intervals",
            "Arguments": []
        }).json()

    """
    def execute(self, body):
        return post_request_json(f'http://localhost:{self.port}', {
            "EvaluationType": "exec",
            "Body": body
        })

    def evaluate(self, body):
        return post_request_json(f'http://localhost:{self.port}', {
            "EvaluationType": "eval",
            "Body": body
        })
    """

class Client:
    def __init__(self, port):
        self.port = str(port)

        import subprocess
        subprocess.Popen(["python3", __file__, self.port])

    """
    def execute(self, body):
        return post_request_json(f'http://localhost:{self.port}', {
            "EvaluationType": "exec",
            "Body": body
        })

    def evaluate(self, body):
        return post_request_json(f'http://localhost:{self.port}', {
            "EvaluationType": "eval",
            "Body": body
        })
    """


environment1 = None
class Server(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        global environment1

        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        request = json.loads(data)

        print("Request")
        print(json.dumps(request).encode()[:800])

        """
        type = request['EvaluationType']
        body = request['Body']

        print("RECEIVED", body)

        if request['EvaluationType'] == 'eval':
            evaluate = eval
        elif request['EvaluationType'] == 'exec':
            evaluate = exec

        response = {
            "Response": evaluate(body, globals())
        }
        """

        respond = lambda response: self.wfile.write(json.dumps(response).encode())

        if request["Request"] == 'Initialize':
            bk2_location = request["bk2_location"]
            environment1 = Environment3(game=request['Game'], actions=request["Actions"], bk2_location=bk2_location)

            respond("AllGood")

        elif request["Request"] == 'MethodExecute':
            method = request["Method"]
            arguments = request["Arguments"]
            print("MethodExecute-", method, arguments, flush=True)

            responseo = environment1.__getattribute__(method)(*arguments)
            if isinstance(responseo, np.ndarray):
                respond(responseo.tolist())
            else:
                respond(environment1.__getattribute__(method)(*arguments))

        elif request["Request"] == 'PropertyGet':
            property = request["Property"]

            respond(environment1.__getattribute__(property))


def run(port):
    print("Listening on port-Retro", str(port) + ".")

    httpd = http.server.HTTPServer(('', port), Server)
    httpd.serve_forever()

if __name__ == "__main__":
    print("got args", sys.argv[1:])
    run(port=int(sys.argv[1]))
