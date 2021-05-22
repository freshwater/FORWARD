
import flask

import os
import uuid
import json

import retro_module

app = flask.Flask(__name__)

class Server:
    files_cache = {}
    modules = {}

    @app.route('/', methods=['POST'])
    def request_process():
        request = flask.request.get_json()

        request_name = request["Request"]
        client_id = request["ClientId"]

        if request_name == "Initial":
            # Server.modules[client_id] = retro_module.Active()
            Server.modules[client_id] = retro_module.RetroModule2()

            return {
                'Data': Server.modules[client_id].interface_json()
            }

        elif request_name == "Event":
            Server.modules[client_id].event_process(request)

            return {
                'Data': Server.modules[client_id].interface_json()
            }

        elif request_name == "Inspection":
            return Server.modules[client_id].inspection_process(request)

        elif request['ResourceType'] == '.bk2 Replay Data':
            pass
        elif request['ResourceType'] == '.json Action Sequence':
            pass
        elif request['ResourceType'] == '.mp4 Replay Video':
            pass

        else:
            raise NotImplementedError(request)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def do_GET(path):
        path = '/' + path
        print(">>", path, flush=True)

        content_types = {
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.html': 'text/html',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm'
        }

        # SinglePageSingleSession
        #   a | b |
        #   c | | d
        ## SinglePageMultipleSession ?
        ##   a | b |
        ##   a | | b
        ## MultiplePageSingleSession ?
        ##   a | a |
        ##   b | | b
        # MultiplePageMultipleSession
        #   a | a |
        #   a | | a

        # if user_state_preservation_mode == 'None':
        #    pass
        # elif user_state_preservation_mode == 'CrossPageSessionOnly':
        #    pass
        # elif user_state_preservation_mode == 'UserOnly':
        #    pass
        # elif user_state_preservation_mode == 'CrossPageSessionAndUser':
        #    pass
        # elif user_state_preservation_mode == 'KeyPreservedState':
        #    pass

        import os.path
        extension = os.path.splitext(path)[1]

        if path == '/':
            if not Server.files_cache.get('/server_directory/index.html'):
                with open('/server_directory/index.html', 'rb') as file:
                    Server.files_cache['/server_directory/index.html'] = file.read()

            return Server.files_cache['/server_directory/index.html']

        elif path == '/favicon.ico':
            return "WE DONT HAVE IT".encode()

        elif extension in ['.js', '.css', '.html', '.gif'] or (extension == '.png' and '/textures/' in path):
            if not Server.files_cache.get(path):
                with open('/server_directory' + path, 'rb') as file:
                    Server.files_cache[path] = file.read()

            return flask.Response(Server.files_cache[path], headers={'Content-Type': content_types[extension]})

        elif extension == '.png':
            with open('/tmp' + path, 'rb') as file:
                return flask.Response(file.read(), headers={
                    'Content-Type': content_types[extension],
                    'Cache-Control': 'max-age=3'
                })

        elif extension in ['.bk2', '.json', '.mp4', '.mkv', '.webm']:
            assert None, None

            if not os.path.exists('/tmp' + path):
                self.send_response(404)
            else:
                self.send_response(200)
                self.send_header('Content-Type', content_types[extension])
                self.send_header('Content-Disposition', 'attachment')
                self.end_headers()

                with open('/tmp' + path, 'rb') as file:
                    self.wfile.write(file.read())
