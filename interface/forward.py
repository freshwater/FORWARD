
import torch
import matplotlib.pyplot as plt
import matplotlib

import uuid


def payload_format(data):
    import numbers

    data_payload = []
    for element in data:
        if isinstance(element, matplotlib.figure.Figure):
            file_id = uuid.uuid4()
            file_name = f"/tmp/{file_id}.png"

            element.savefig(file_name)
            data_payload.append({"Type": "Image",
                                 "Value": f"{file_id}.png"})

        elif isinstance(element, Image):
            data_payload.append(element.json())

        elif isinstance(element, (np.ndarray, torch.Tensor)):
            data_payload.append({"Type": "Array2D",
                                 "Value": element.tolist()})

        elif isinstance(element, numbers.Integral):
            data_payload.append({"Type": "Number",
                                 "Value": int(element)})

        elif isinstance(element, numbers.Number):
            data_payload.append({"Type": "Number",
                                 "Value": float(element)})

        elif isinstance(element, list):
            if isinstance(element[0], list):
                data_payload.append({"Type": "Array2D",
                                     "Value": element})

            elif isinstance(element[0], Image):
                data_payload.append({"Type": "ForwardList",
                                     "Value": payload_format(element)})

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

class Image:
    def __init__(self, array, elements=[], display_scale=1):
        if isinstance(array, torch.Tensor):
            self.array = array.detach().cpu().numpy()
        else:
            self.array = array

        self.elements = elements
        self.json_cached = None
        self.display_scale = display_scale

        self.count = 0

    def json(self):
        self.count += 1
        # print(f"\nJSON {self.count} {self.json_cached}\n", flush=True)
        if self.json_cached:
            return self.json_cached

        else:
            file_name = f"/tmp/{uuid.uuid4()}.png"

            plt.imsave(file_name, self.array)

            with open(file_name, 'rb') as file:
                data = file.read()

            import base64
            encoded = base64.b64encode(data).decode()
            url_encoded = f"data:image/png;base64,{encoded}"

            self.json_cached = {"Type": "Image",
                                "Value": url_encoded,
                                "Shape": self.array.shape,
                                "DisplayScale": self.display_scale,
                                "Elements": [element.json() for element in self.elements]}

            return self.json_cached

    def json0(self):
        file_id = uuid.uuid4()
        file_name = f"/tmp/{file_id}.png"

        plt.imsave(file_name, self.array)

        return {"Type": "Image",
                "Value": f"{file_id}.png",
                "Shape": self.array.shape,
                "Elements": [element.json() for element in self.elements]}

class Region:
    def __init__(self, geometry, color=[0.5, 0.5, 0.5, 1.0], label="", label_color=[1, 1, 0, 1]):
        self.geometry = geometry
        self.label = label
        self.color = color
        self.label_color = label_color

    def json(self):
        return {
            'Geometry': self.geometry,
            'Label': self.label,
            'Color': self.color,
            'LabelColor': self.label_color
        }

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


