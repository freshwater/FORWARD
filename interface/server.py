
import http.server

import json
import torch
import numpy as np
import retro

import uuid
import os
import matplotlib.pyplot as plt

import retro_server


class Server(http.server.BaseHTTPRequestHandler):
    # with open('static/index.html') as file:
    #     html_index_file = file.read()

    files_cache = {}
    environments = {}

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

    def request_process(self, request):
        request_name = request["Request"]
        client_id = request["ClientId"]

        if request_name == "AvailableGames":
            return {
                "AvailableGames": Server.games_list
            }

        elif request_name == "ImageUrl":
            image_files_folder = Server.environments[client_id].image_files_folder()
            file_name = f"{image_files_folder}/{uuid.uuid4()}.png"
            frame, _encodings, _blocks, _frame_index = Server.environments[client_id].interface_render()
            plt.imsave("/tmp/" + file_name, np.array(frame).astype(np.uint8))

            return file_name

        elif request_name == "ResourceURL":
            client_id = request['ClientId']
            game = request['Game']

            random_key = uuid.uuid4()

            # todo convenient file name

            if request['ResourceType'] == '.bk2 Replay Data':
                actions_commitment_intervals = Server.environments[client_id].actions_commitment_intervals()
                actions = sum([[action]*interval for action, interval in actions_commitment_intervals], [])

                folder = f'/tmp/{random_key}'
                os.makedirs(folder)

                environment = retro_server.RetroClient(game=game,
                                                       bk2_location=folder,
                                                       actions=actions)

                environment.close()
                print(os.listdir(folder))

                return f'/{random_key}/{os.listdir(folder)[0]}'

            elif request['ResourceType'] == '.json Action Sequence':
                actions_commitment_intervals = Server.environments[client_id].actions_commitment_intervals()
                actions = sum([[action]*interval for action, interval in actions_commitment_intervals], [])

                with open(f'/tmp/{random_key}.json', 'w') as file:
                    file.write(json.dumps(actions))

                return f'/{random_key}.json'

            elif request['ResourceType'] == '.mp4 Replay Video':
                actions_commitment_intervals = Server.environments[client_id].actions_commitment_intervals()
                actions = sum([[action]*interval for action, interval in actions_commitment_intervals], [])

                folder = f'/tmp/{random_key}'
                os.makedirs(folder)

                environment = retro_server.RetroClient(game=game,
                                                       bk2_location=folder,
                                                       actions=actions)

                environment.close()
                print(os.listdir(folder))

                replay_file = f'/tmp/{random_key}/{os.listdir(folder)[0]}'
                import subprocess
                video_being_written = f'/tmp/{random_key}/video_being_written.mp4'
                video_file = f'/tmp/{random_key}/video.mp4'
                # It looks like ffmpeg streams to the file or otherwise takes a bit of time to write it.
                # Use && so that the completed video file only exists after the writing is fully complete.
                # This makes it easier to just poll for the file on the client.
                subprocess.Popen(f'python3 playback_movie.py {replay_file} && mv {video_being_written} {video_file}',
                                 shell=True)

                return f'/{random_key}/video.mp4'


        elif request_name == "Reset":
            game = request["Game"]

            if environment := Server.environments.get(client_id):
                environment.close()

            Server.environments[client_id] = retro_server.RetroClient(game=game)
            frame, encodings, blocks, frame_index = Server.environments[client_id].interface_render()

            import forward
            data = Server.environments[client_id].interface_render2()
            data_payload = forward.payload_format(data)

            return {
                'Observation': frame,
                'BlockEncodings': encodings,
                'Blocks': blocks,
                'FrameIndex': frame_index,
                'Data': data_payload
            }

        elif request_name == "Action":
            action = request["Action"]
            commitment_interval = request["CommitmentInterval"]

            import time
            t0 = time.time()
            Server.environments[client_id].step(action, commitment_interval)
            frame, encodings, blocks, frame_index = Server.environments[client_id].interface_render()
            print("TIME", time.time() - t0)

            import forward
            data = Server.environments[client_id].interface_render2()
            data_payload = forward.payload_format(data)

            return {
                'Observation': frame,
                'BlockEncodings': encodings,
                'Blocks': blocks,
                'FrameIndex': frame_index,
                'Data': data_payload
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

        response = self.request_process(request)

        self.wfile.write(json.dumps(response).encode())


    def do_GET(self):
        print(">>", self.path)

        content_types = {
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.png': 'image/png',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm'
        }

        import os.path

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            if not Server.files_cache.get('static/index.html'):
                with open('static/index.html', 'rb') as file:
                    Server.files_cache['static/index.html'] = file.read()

            self.wfile.write(Server.files_cache['static/index.html'])

        elif (extension := os.path.splitext(self.path)[1]) in ['.js', '.css']:
            self.send_response(200)
            self.send_header('Content-type', content_types[extension])
            self.end_headers()

            if not Server.files_cache.get(self.path):
                with open('/not_tmp' + self.path, 'rb') as file:
                    Server.files_cache[self.path] = file.read()

            self.wfile.write(Server.files_cache[self.path])

        elif self.path == '/favicon.ico':
            self.wfile.write("WE DONT HAVE IT".encode())

        elif os.path.splitext(self.path)[1] == '.png':
            self.send_response(200)
            self.send_header('Content-Type', content_types['.png'])
            self.send_header('Cache-Control', 'max-age=30')
            self.end_headers()

            with open('/tmp' + self.path, 'rb') as file:
                self.wfile.write(file.read())

        elif ((extension := os.path.splitext(self.path)[1])
                in ['.bk2', '.json', '.mp4', '.mkv', '.webm']):

            if not os.path.exists('/tmp' + self.path):
                self.send_response(404)
            else:
                self.send_response(200)
                self.send_header('Content-Type', content_types[extension])
                self.send_header('Content-Disposition', 'attachment')
                self.end_headers()

                with open('/tmp' + self.path, 'rb') as file:
                    self.wfile.write(file.read())


def run(port=80):
    print("Listening on port", str(port) + ".")

    httpd = http.server.HTTPServer(('', port), Server)
    httpd.serve_forever()


run()
