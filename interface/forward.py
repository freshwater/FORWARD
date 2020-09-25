


def payload_format(data):
    import matplotlib
    import torch
    import numbers

    data_payload = []
    for element in data:
        if isinstance(element, matplotlib.figure.Figure):
            file_id = uuid.uuid4()
            file_name = f"/tmp/{file_id}.png"
            element.savefig(file_name)
            data_payload.append(["Image", f"{file_id}.png"])

        elif isinstance(element, np.ndarray):
            data_payload.append(["Array2D", element.tolist()])

        elif isinstance(element, torch.Tensor):
            data_payload.append(["Array2D", element.tolist()])
            print("SHAPE", element.shape)

        elif isinstance(element, numbers.Integral):
            data_payload.append(["Number", int(element)])

        elif isinstance(element, numbers.Number):
            data_payload.append(["Number", float(element)])

        elif isinstance(element, list):
            if isinstance(element[0], list):
                data_payload.append(["Array2D", element])

        else:
            print(">>>>>>>>>>>>", type(element))

    return data_payload



class Array:
    def __init__(self, data, number_format):
        self.data = data

    def representation():
        for row in data:
            for column in row:
                pass


class Region:
    def __init__(self, geometry, color=[0.5, 0.5, 0.5, 1.0], label="", label_color=[1, 1, 1, 1]):
        pass

class Raster:
    def __init__(self, data, elements=[]):
        pass

class Graphics:
    def __init__(self, elements):
        self.elements = elements


import numpy as np

Raster(data=np.random.rand(20, 20),
       elements=[
           Region(geometry=[[0, 0], [5, 5]],
                  color=[1, 0, 0, 0.5],
                  label="HEY!")
       ])


