import csv
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Generator, List
import json

from jinja2 import Environment, PackageLoader, select_autoescape

GENERATED_DIR_NAME = 'generated'
SPECS_DIR_NAME = 'specs'
DATA_DIR_NAME = 'data'

FIELD_X_NAME = "x"
FIELD_Y_NAME = "y"
FIELD_CATEGORY_NAME = "category"


class DataFormat(Enum):
    CSV = 'csv'
    JSON = 'json'


class Renderer(Enum):
    CANVAS = 'canvas'
    SVG = 'svg'


@dataclass
class GenerationRequest(object):
    experiment_name: str
    num_points: int
    num_categories: int
    num_attributes: int
    width: int
    height: int
    data_format: DataFormat
    renderer: Renderer


def generate_vega_spec(request: GenerationRequest) -> Dict:
    """
    Generate report vega specification, without data
    """

    data_name = "table"
    xscale_name = "xscale"
    yscale_name = "yscale"

    res: Dict = {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "width": request.width,
        "height": request.height,
        "padding": 5,
        "data": [{
            "name": data_name,
            "values": [
                {"x": 0.05, "y": 0.09, "c": 0.98},
                {"x": 0.04, "y": 0.12, "c": 0.23},
                {"x": 0.01, "y": 0.01, "c": 0.23}
            ]
        }

            # {
            #     "name": "airports",
            #     "url": "data/airports.csv",
            #     "format": {"type": "csv", "parse": "auto"}
            # }

        ],
        "scales": [
            {
                "name": xscale_name,
                "type": "linear",
                "domain": {"data": data_name, "field": FIELD_X_NAME},
                "range": "width",
                "padding": 0.05,
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
            {"orient": "bottom", "scale": xscale_name, "grid": True},
            {"orient": "left", "scale": yscale_name, "grid": True}
        ],
        "marks": [
            {
                "name": "marks",
                "type": "symbol",
                "from": {"data": data_name},
                "encode": {
                    "update": {
                        "x": {"scale": xscale_name, "field": FIELD_X_NAME},
                        "y": {"scale": yscale_name, "field": FIELD_Y_NAME},

                        "shape": {"value": "circle"},
                        "strokeWidth": {"value": 2},
                        "opacity": {"value": 0.5},
                        "stroke": {"value": "#4682b4"},
                        "fill": {"value": "transparent"}
                    }
                },
            }
        ]
    }

    return res


def save_vega_spec(request: GenerationRequest, vega_spec: Dict):
    json_string = json.dumps(vega_spec, indent=2)

    path = Path(__file__).parent.resolve() / '..' / GENERATED_DIR_NAME / SPECS_DIR_NAME / (
            request.experiment_name + '.json')
    with open(path, "w") as file:
        file.write(json_string)


def generate_data(request: GenerationRequest) -> None:
    def generate_one_row(request: GenerationRequest, i: int) -> Dict:

        category = 'category_' + str(random.randint(0, request.num_categories))

        res = {FIELD_CATEGORY_NAME: category,
               FIELD_X_NAME: random.uniform(0, 1),
               FIELD_Y_NAME: random.uniform(0, 1)}

        for i in range(request.num_attributes):
            res["attr_" + str(i)] = random.uniform(0, 1)

        return res

    def generate_rows(request: GenerationRequest) -> Generator[Dict, None, None]:
        for i in range(request.num_points):
            yield generate_one_row(request, i)

    def generate_csv_header_row(request: GenerationRequest) -> List[str]:
        return list(generate_one_row(request, 0).keys())

    out_file_name = (Path(__file__).parent.resolve()
                     / '..'
                     / GENERATED_DIR_NAME
                     / DATA_DIR_NAME
                     / (request.experiment_name + '.' + request.data_format.value))

    if request.data_format == DataFormat.CSV:
        with open(out_file_name, "w") as f:
            writer = csv.writer(f)
            writer.writerow(generate_csv_header_row(request))

        for row in generate_rows(request):
            writer.writerow(row)
    elif request.data_format == DataFormat.JSON:
        with open(out_file_name, "w") as f:
            for row in generate_rows(request):
                print(json.dumps(row), file=f)
    else:
        assert False, "unknown data format " + request.data_format.value


def generate_html(request: GenerationRequest) -> str:
    env = Environment(
        loader=PackageLoader('vis-study'),
        autoescape=select_autoescape()
    )

    template = env.get_template('index.html')
    return template.render(request=request)


def save_html(request: GenerationRequest, html: str) -> None:
    path = Path(__file__).parent.resolve() / '..' / GENERATED_DIR_NAME / (request.experiment_name + '.html')
    with open(path, "w") as file:
        file.write(html)


def generate_all(request: GenerationRequest) -> None:
    generate_data(request)

    vega_spec = generate_vega_spec(request)
    save_vega_spec(request, vega_spec)

    html = generate_html(request)
    save_html(request, html)


if __name__ == "__main__":
    request = GenerationRequest(
        experiment_name="exp1",
        num_points=100,
        num_categories=40,
        width=500,
        height=500,
        data_format=DataFormat.JSON,
        num_attributes=5,
        renderer=Renderer.CANVAS
    )

    generate_all(request)
