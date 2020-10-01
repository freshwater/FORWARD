
import torch
import matplotlib.pyplot as plt
import matplotlib

import uuid

class State:
    def __init__(self, element):
        self.state = {}
        self.element = element

    # def json(self):

    def event_process(self, event):
        if event['Type'] == "Button_OnClick":
            self.state[event['Id']].on_click()

    def payload_format(self, data):
        data_payload = []
        for element in data:
            if isinstance(element, Element):
                pass

            if isinstance(element, matplotlib.figure.Figure):
                file_id = uuid.uuid4()
                file_name = f"/tmp/{file_id}.png"

                element.savefig(file_name)
                data_payload.append({"Type": "Image",
                                    "Value": f"{file_id}.png"})

            elif isinstance(element, Image):
                data_payload.append(element.json())

            elif isinstance(element, Button):
                self.state[element.id] = element
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

            elif isinstance(element, str):
                data_payload.append({"Type": "String",
                                     "Value": element})

            elif isinstance(element, list):
                if isinstance(element[0], list):
                    data_payload.append({"Type": "Array2D",
                                         "Value": element})

                elif isinstance(element[0], Image):
                    data_payload.append({"Type": "ForwardList",
                                         "Value": self.payload_format(element)})

                elif isinstance(element[0], Button):
                    data_payload.append({"Type": "ForwardList",
                                         "Value": self.payload_format(element)})

            elif isinstance(element, dict):
                data_payload.append({"Type": "ForwardDictionary",
                                     "Value": [(key if isinstance(key, (str, int)) else key.json(),
                                                value if isinstance(value, (str, int)) else value.json())
                                               for key, value in element.items()]})

            else:
                print(">>>>>>>>>>>>", type(element))

        return data_payload


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
        else:
            print("]]]]]]]]]]]]]]]]", object)


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

        self.height = len(data)
        self.width = len(data[0])

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


class Image(Element):
    def __init__(self, array, elements=[], display_scale=1, color_map=None):
        if isinstance(array, torch.Tensor):
            self.array = array.detach().cpu().numpy()
        else:
            self.array = array

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

    def json0(self):
        file_id = uuid.uuid4()
        file_name = f"/tmp/{file_id}.png"

        plt.imsave(file_name, self.array)

        return {"Type": "Image",
                "Value": f"{file_id}.png",
                "Shape": self.array.shape,
                "Elements": [element.json() for element in self.elements]}

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

