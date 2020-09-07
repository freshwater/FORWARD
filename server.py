
import http.server

import json
import time
import torch
import retro


def block_partition(matrix, block_width):
    matrix = matrix.reshape(-1, block_width, matrix.shape[0] // block_width, block_width, 3)
    matrix = matrix.transpose(2, 1).reshape(-1, block_width, block_width, 3)

    return matrix

def observation_prepare(observation, blocks_seen):
    obs = torch.tensor(observation)

    obs = torch.cat([obs,
                     torch.zeros(16, 240, 3)]).long()

    blocks = block_partition(obs, 16)

    blocks = blocks[4*15:-2*15]

    exponent = 2
    # encodings = [((block.float() / 255 / 16 / 16).sum()**exponent).item() for block in blocks]
    # encodings = [hash(((block.float() / 255 / 16 / 16).sum()**exponent).item()) % 255 for block in blocks]

    asymmetric = torch.linspace(0.5, 1.5, 16*16*3)**3
    # encodings = [((block.flatten().float() @ asymmetric / 16 / 16 / 3 / 255) - 0.5).item() for block in blocks]
    encodings = [((block.flatten().float() @ asymmetric / 16 / 16 / 3 / 255)).item() for block in blocks]

    tuples = set([tuple(block.flatten().tolist()) for block in blocks])
    # blocks_seen.update(tuples)
    # sorted_ = sorted(list(blocks_seen))
    sorted_ = sorted(list(tuples))
    blocks = [torch.tensor(block).reshape(16, 16, 3) for block in sorted_]

    return observation.tolist(), encodings, [block.tolist() for block in blocks]


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
        'Dash':      [0, 0, 1, 0, 0, 0, 0, 0, 0],
        'RightDash': [0, 0, 1, 0, 0, 0, 0, 1, 0],
        'LeftJump':  [0, 0, 0, 0, 0, 0, 1, 0, 1],
        'RightJump': [0, 0, 0, 0, 0, 0, 0, 1, 1]
    }

    def request_process(self, request):
        request_name = request["Request"]
        client_id = request["ClientId"]

        if request_name == "Reset":
            if environment := Server.environments.get(client_id):
                environment.render(close=True)
                environment.close()

            environment = retro.make(game='SuperMarioBros-Nes')
            observation = environment.reset()

            Server.environments[client_id] = environment
            Server.blocks_seen[client_id] = set()

            observation, encodings, blocks = observation_prepare(observation, Server.blocks_seen[client_id])

            return {
                'Observation': observation,
                'BlockEncodings': encodings,
                'Blocks': blocks
            }

        elif request_name == "Action":
            commitment_interval = request["CommitmentInterval"]
            action = Server.actions[request["Action"]]

            environment = Server.environments[client_id]
            blocks_seen = Server.blocks_seen[client_id]

            # action = environment.action_space.sample()
            unknown = [0, 0, 0, 0, 0, 1, 0, 0, 0]
            unknown = [0, 0, 0, 0, 1, 0, 0, 0, 0]
            unknown = [0, 0, 0, 1, 0, 0, 0, 0, 0]
            unknown = [0, 0, 1, 0, 0, 0, 0, 0, 0]
            unknown = [0, 1, 0, 0, 0, 0, 0, 0, 0]
            unknown = [1, 0, 0, 0, 0, 0, 0, 0, 0]

            print("ACTION", action)

            for _ in range(commitment_interval):
                observation, reward, is_done, information = environment.step(action)

            observation, encodings, blocks = observation_prepare(observation, blocks_seen)

            return {
                'Observation': observation,
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
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open('index.html') as file:
            Server.html_index_file = file.read()

        response = Server.html_index_file

        self.wfile.write(response.encode())


def run(port=80):
    print("Listening on port", str(port) + ".")

    httpd = http.server.HTTPServer(('', port), Server)
    httpd.serve_forever()


run()
