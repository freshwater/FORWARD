
import http.server

import json
import time
import torch
import retro


class Server(http.server.BaseHTTPRequestHandler):
    with open('index.html') as file:
        html_index_file = file.read()

    environments = {}

    actions = {
        'Left':      [0, 0, 0, 0, 0, 0, 1, 0, 0],
        'Right':     [0, 0, 0, 0, 0, 0, 0, 1, 0],
        'Jump':      [0, 0, 0, 0, 0, 0, 0, 0, 1],
        'None':      [0, 0, 0, 0, 0, 0, 0, 0, 0],
        'Crouch':    [0, 0, 0, 0, 0, 1, 0, 0, 0],
        'Dash':      [0, 0, 0, 1, 0, 0, 0, 0, 0],
        'RightDash': [0, 0, 0, 1, 0, 0, 0, 1, 0],
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

            return {
                'Observation': observation.tolist()
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

            for _ in range(commitment_interval):
                observation, reward, is_done, information = environment.step(action)

            return {
                'Observation': observation.tolist()
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
