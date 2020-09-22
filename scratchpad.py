
def r2():
    import multiprocessing as mp
    import retro

    def dispatch(connection):
        while not connection.closed:
            request = connection.recv()
            method, kwargs = request[0], request[1]

            if method == '__init__':
                environment = retro.make(**kwargs)
                connection.send(None)

            elif method == 'close':
                environment.close()
                connection.send(None)
                connection.close()

            elif method == 'print':
                print(environment)
                connection.send(None)

            elif method == '[get_attribute]':
                result = environment.__getattribute__(kwargs['attribute'])
                connection.send(result)

            else:
                result = environment.__getattribute__(method)(**kwargs)
                connection.send(result)

    connections = []
    processes = []
    for _ in range(5):
        parent_connection, child_connection = mp.Pipe()
        process = mp.Process(target=dispatch, args=[child_connection])
        process.start()

        connections.append(parent_connection)
        processes.append(process)

    for connection in connections:
        connection.send(['__init__', {'game': 'SuperMarioBros-Nes'}])
        connection.recv()
        connection.send(['print', {}])
        connection.recv()

    for connection in connections:
        connection.send(['reset', {}])
        connection.recv()
        connection.send(['step', {'a': [0, 0, 0, 0, 0, 0, 0, 1, 0]}])
        print('recv:', connection.recv()[0].shape)

    for connection in connections:
        connection.send(['[get_attribute]', {'attribute': 'observation_space'}])
        connection.recv()
        connection.send(['close', {}])
        connection.recv()

    for process in processes:
        process.join()


def r1():
    import multiprocessing as mp
    import retro

    def dispatch(connection):
        while request := connection.recv():
            print(request)
            connection.send("YO")

        connection.close()


    def dispatch(connection):
        while not connection.closed:
            request = connection.recv()
            method, kwargs = request[0], request[1]

            if method == '__init__':
                environment = retro.make(**kwargs)
                connection.send(None)

            elif method == 'close':
                environment.close()
                connection.send(None)
                connection.close()

            elif method == 'print':
                print(environment)
                connection.send(None)

            elif method == '[get_attribute]':
                connection.send(environment.__getattribute__(kwargs['attribute']))

            else:
                result = environment.__getattribute__(method)(**kwargs)
                connection.send(result)


    parent_connection, child_connection = mp.Pipe()
    process = mp.Process(target=dispatch, args=[child_connection])

    print(">")
    process.start()
    parent_connection.send(['__init__', {'game': 'SuperMarioBros-Nes'}])
    print("__init__>", parent_connection.recv())

    parent_connection.send(['print', {}])
    print("print>", parent_connection.recv())

    parent_connection.send(['[get_attribute]', {'attribute': 'observation_space'}])
    print("[get_attribute]>", parent_connection.recv())

    parent_connection.send(['close', {}])
    print("close>", parent_connection.recv())
    print(">")

    process.join()

r2()