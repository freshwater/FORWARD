
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

import uuid

class Module:
    def __init__(self):
        self.interfaces = []

    def user_state_preservation_mode(self):
        return 'SinglePageSingleSession'

    def application(self, path):
        # path, parameters = path_deconstruct(path)
        parameters = {}

        if path == '/':
            return self.interface(parameters)

        elif path == '/b':
            return self.interface2(parameters)

    def event_process(self, event):
        for element in reversed(self.interfaces):
            element.event_process(event)

    def inspection_process(self, request):
        for element in reversed(self.interfaces):
            if result := element.inspection_process(request):
                return result

    def interface_json(self):
        # Each interface call can produce completely new objects.
        interface_raw = self.interface()
        interface_typed = Element.to_element(interface_raw)

        # Keep older event handlers in case the user interacts multiple
        # times with the same frame before getting a new frame.
        self.interfaces.append(interface_typed)
        if len(self.interfaces) > 20:
            self.interfaces.pop(0)

        return interface_typed.json()


class Element:
    def to_element(object):
        import numbers

        if isinstance(object, Element):
            return object
        elif isinstance(object, str):
            return String(object)
        elif isinstance(object, numbers.Number):
            return Number(object)
        elif isinstance(object, (list, tuple)):
            return List(object)
        elif isinstance(object, dict):
            return Dictionary(object)
        elif isinstance(object, pd.DataFrame):
            return Dataset(object)
        else:
            print("\n\n>", object, "\n\n")
            1 / 0


    def event_process(self, event):
        if isinstance(self, List):
            for element in self.value:
                if element.event_process(event):
                    return True

        elif isinstance(self, Dictionary):
            for key, value1 in self.value:
                if key.event_process(event):
                    return True
                elif value1.event_process(event):
                    return True

    def inspection_process(self, request):
        if isinstance(self, List):
            for element in self.value:
                if result := element.inspection_process(request):
                    return result

        elif isinstance(self, Dictionary):
            for key, value1 in self.value:
                if result := key.inspection_process(request):
                    return result
                elif result := value1.inspection_process(request):
                    return result


    def rasterize(self):
        return self


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

class Dataset(Element):
    def __init__(self, dataset):
        self.value = dataset

    def json(self):
        return {"Type": "Array2D",
                "Value": self.value.values.tolist()}


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

class ApplicationSettings(Element):
    def __init__(self, settings):
        self.settings = settings

        for key, value in settings.items():
            if key == 'Thumbnail':
                self.settings[key] = Element.to_element(value).rasterize().json()

    def json(self):
        return {
            "Type": "ApplicationSettings",
            "Value": self.settings
        }

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

class SelectionList(Element):
    def __init__(self, options, selected_option, on_change, is_enabled=True):
        self.options = options
        self.selected_option = selected_option
        self.on_change = on_change
        self.is_enabled = is_enabled

        self.id = str(uuid.uuid4())

    def json(self):
        return {
            "Type": "SelectionList",
            "Value": self.options,
            "SelectedValue": self.selected_option,
            "Id": self.id,
            "IsEnabled": self.is_enabled
        }

    def event_process(self, event):
        if event['Id'] == self.id:
            self.on_change(event['Value'])

            return True

class CheckList(Element):
    def __init__(self, options, selected_options, on_check):
        self.options = options
        self.selected_options = selected_options
        self.on_check = on_check

        self.id = str(uuid.uuid4())

    def json(self):
        return {
            "Type": "CheckList",
            "Value": self.options,
            "SelectedValue": self.selected_options,
            "Id": self.id
        }

    def event_process(self, event):
        if event['Id'] == self.id:
            self.on_check(event['Key'], event['Value'])

            return True

class NumberInput(Element):
    def __init__(self, value, on_change, minimum=None, maximum=None):
        # self.label = label
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
            # "Label": self.label,
            "Minimum": self.minimum,
            "Maximum": self.maximum
        }

    def event_process(self, event):
        if event['Id'] == self.id:
            self.on_change(int(event['Value']))

            return True


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
    def __init__(self, array, elements=[], display_scale=1, color_map=None, inspect_form=None):
        self.raw_data = inspect_form if inspect_form is not None else array
        self.instance_id = str(uuid.uuid4())

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

    def inspection_process(self, request):
        if request['InstanceId'] == self.instance_id:
            return {"Type": "Inspection",
                    "Value": np.array(self.raw_data).tolist()}

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
                                "InstanceId": self.instance_id,
                                "Value": url_encoded,
                                "Shape": self.array.shape,
                                "DisplayScale": self.display_scale,
                                "Elements": [element.json() for element in self.elements]}

            return self.json_cached


class ArrayPlot3D(Element):
    def __init__(self, array, _sequence_hacks_much_spooky_do_not_use=False):
        array = np.array(array)

        self._sequence_hacks_much_spooky_do_not_use = _sequence_hacks_much_spooky_do_not_use

        if np.max(array) == np.min(array):
            array.fill(1)
            rescaled = array
        else:
            rescaled = (array - np.min(array)) / (np.max(array) - np.min(array))

        rescaled = (255*rescaled).astype(np.uint8)
        self.shape = rescaled.shape

        if _sequence_hacks_much_spooky_do_not_use == "secr3tcode":
            self.value_references = [str(hash(slice_.data.tobytes())) for slice_ in rescaled]

            import base64
            self.array = None
            self.encoded = base64.b64encode(rescaled[-1].data).decode()
        else:
            self.array = rescaled.tolist()
            self.encoded = None

    def json(self):
        import json

        if self._sequence_hacks_much_spooky_do_not_use != "secr3tcode":
            return {"Type": "ArrayPlot3D",
                    "Value": self.array,
                    "Shape": self.shape}
        else:
            return {"Type": "ArrayPlot3D",
                    "ValueReferences": self.value_references,
                    "ValueReferencesEncodedInsert": {
                        self.value_references[-1]: self.encoded
                    },
                    "Shape": self.shape}

class Audio(Element):
    def __init__(self, signal):
        self.signal = signal

    def json(self):
        return {
            "Type": "Audio",
            "Value": self.signal
        }


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

