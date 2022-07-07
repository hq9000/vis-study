from dataclasses import dataclass
from enum import Enum
from typing import Dict

FIELD_X_NAME = "x"
FIELD_Y_NAME = "y"


class DataFormat(Enum):
    CSV = 'csv'
    JSON = 'json'


@dataclass
class GenerationRequest(object):
    experiment_name: str
    num_points: int
    num_categories: int
    num_attributes: int
    width: int
    height: int
    data_format: DataFormat


def generate_vega_spec(request: GenerationRequest) -> Dict:

    data_name = "table"
    xscale_name = "scale"
    yscale_name = "yscale"

    res: Dict = {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "width": request.width,
        "height": request.height,
        "padding": 5,
        "data": {
            "name": data_name,
            "url": ('data/'
                    + request.experiment_name
                    + '.'
                    + request.data_format.value),
            "format": request.data_format.value
        },
        "scales": [
            {
                "name": xscale_name,
                "type": "linear",
                "domain": {"data": data_name, "field": FIELD_X_NAME},
                "range": "width",
                "padding": 0.05,
                "round": False
            },
            {
                "name": yscale_name,
                "type": "linear",
                "domain": {"data": data_name, "field": FIELD_Y_NAME},
                "nice": True,
                "range": "height"
            }
        ],
        "axes": [
            {"orient": "bottom", "scale": xscale_name},
            {"orient": "left", "scale": yscale_name}
        ],
        "marks": [
            {
                "type": "rect",
                "from": {"data": data_name},
                "encode": {
                    "enter": {
                        "x": {"scale": xscale_name, "field": FIELD_X_NAME},
                        "width": {"scale": "xscale", "band": 1},
                        "y": {"scale": "yscale", "field": "amount"},
                        "y2": {"scale": "yscale", "value": 0}
                    },
                    "update": {
                        "fill": {"value": "steelblue"}
                    },
                    "hover": {
                        "fill": {"value": "red"}
                    }
                }
            }
        ]
    }

    return res
