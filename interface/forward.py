
import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

import uuid


class Element:
    def to_element(object):
        import numbers

        if isinstance(object, Element):
            return object
        elif isinstance(object, str):
            return String(object)
        elif isinstance(object, numbers.Number):
            return Number(object)
        elif isinstance(object, list):
            return List(object)
        elif isinstance(object, dict):
            return Dictionary(object)
        # elif isinstance(object, matplotlib.axes.Axes):
        #     return FileImage()
        else:
            print("\n\n>", object, "\n\n")
            1 / 0


    def event_process(self, event):
        if isinstance(self, List):
            for element in self.value:
                if element.event_process(event):
                    return

        elif isinstance(self, Dictionary):
            for key, value1 in self.value:
                if key.event_process(event):
                    return
                elif value1.event_process(event):
                    return


class String(Element):
    def __init__(self, value):
        self.value = value

    def json(self):
        return {"Type": "String",
                "Value": self.value}

class Number(Element):
    def __init__(self, value):
        self.value = value

    def json(self):
        return {"Type": "Number",
                "Value": str(self.value)}

class Dictionary(Element):
    def __init__(self, value):
        self.value = value
        self.value = [(Element.to_element(key), Element.to_element(value1))
                      for key, value1 in value.items()]

    def json(self):
        return {"Type": "Dictionary",
                "Value": [(key.json(), value1.json())
                          for key, value1 in self.value]}

class List(Element):
    def __init__(self, value):
        self.value = [Element.to_element(value1) for value1 in value]

    def json(self):
        return {"Type": "List",
                "Value": [value1.json() for value1 in self.value]}

class Array(Element):
    def __init__(self, data, number_format=[]):
        self.data = data

    def json(self):
        return {"Type": "Array2D",
                "Value": self.data}

class Button(Element):
    def __init__(self, label, on_click, enabled=True):
        self.label = label
        self.on_click = on_click
        self.enabled = enabled

        self.id = str(uuid.uuid4())

    def json(self):
        return {
            "Type": "Button",
            "Value": self.label,
            "Id": self.id,
            "IsEnabled": self.enabled
        }

    def event_process(self, event):
        if event['Id'] == self.id:
            self.on_click()

            return True

class NumberInput(Element):
    def __init__(self, label, minimum, maximum, value, on_change):
        self.label = label
        self.minimum = minimum
        self.maximum = maximum
        self.value = value
        self.on_change = on_change

        self.id = str(uuid.uuid4())

    def json(self):
        return {
            "Type": "NumberInput",
            "Value": self.value,
            "Id": self.id,
            "Minimum": minimum,
            "Maximum": maximum
        }


class FileImage(Element):
    def __init__(self, file, elements=[], dpi=2*75, display_scale=1):
        self.file = file
        self.elements = elements
        self.display_scale = display_scale

        # self.file = f"/tmp/{uuid.uuid4()}.png"
        # import shutil
        # shutil.copyfile(file, self.file)

        import PIL.Image
        image = PIL.Image.open(file)
        height, width = image.size
        height_dpi, width_dpi = image.info['dpi']
        self.shape = height * 75 / height_dpi, width * 75 / width_dpi

        # print("\n\ndpi\n\n", PIL.Image.open(file).info)

    def json(self):
        with open(self.file, 'rb') as file:
            data = file.read()

        import base64
        encoded = base64.b64encode(data).decode()
        url_encoded = f"data:image/png;base64,{encoded}"

        self.json_cached = {"Type": "Image",
                            "Value": url_encoded,
                            "Shape": self.shape,
                            "DisplayScale": self.display_scale,
                            "Elements": [element.json() for element in self.elements]}

        return self.json_cached


class Image(Element):
    def __init__(self, array, elements=[], display_scale=1, color_map=None):
        if isinstance(array, torch.Tensor):
            self.array = array.detach().cpu().numpy()
        elif isinstance(array, list):
            self.array = np.array(array or [[0]])
        elif isinstance(array, np.ndarray):
            if len(array.shape) > 1:
                self.array = array
            else:
                self.array = np.array([[0]])
        else:
            1 / 0

        self.elements = elements
        self.json_cached = None
        self.display_scale = display_scale
        self.color_map = color_map

        self.count = 0

    def json(self):
        self.count += 1
        # print(f"\nJSON {self.count} {self.json_cached}\n", flush=True)
        if self.json_cached:
            return self.json_cached

        else:
            file_name = f"/tmp/{uuid.uuid4()}.png"

            if self.color_map == 'Grayscale':
                plt.imsave(file_name, self.array, cmap='gray')
            else:
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

class Region(Element):
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

class Graphics(Element):
    def __init__(self, elements):
        self.elements = elements

