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
    x_scale_name = "xscale"
    y_scale_name = "yscale"
    color_scale_name = "color"

    res: Dict = {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "width": request.width,
        "height": request.height,
        "padding": 5,
        "data": [{
            "name": data_name,
            "url": generate_relative_path_to_data(request),
            "format": {"type": request.data_format.value, "parse": "auto"}
        }
        ],
        "scales": [
            {
                "name": x_scale_name,
                "type": "linear",
                "domain": {"data": data_name, "field": FIELD_X_NAME},
                "range": "width",
                "padding": 0.05,
            },
            {
                "name": y_scale_name,
                "type": "linear",
                "domain": {"data": data_name, "field": FIELD_Y_NAME},
                "nice": True,
                "range": "height"
            },
            {
                "name": color_scale_name,
                "type": "ordinal",
                "range": {"scheme": "category10"},
                "domain": {"data": data_name, "field": FIELD_CATEGORY_NAME}
            }
        ],
        "axes": [
            {"orient": "bottom", "scale": x_scale_name, "grid": True},
            {"orient": "left", "scale": y_scale_name, "grid": True}
        ],
        "marks": [
            {
                "name": "marks",
                "type": "symbol",
                "from": {"data": data_name},
                "encode": {
                    "update": {
                        "x": {"scale": x_scale_name, "field": FIELD_X_NAME},
                        "y": {"scale": y_scale_name, "field": FIELD_Y_NAME},

                        "shape": {"value": "circle"},
                        "strokeWidth": {"value": 2},
                        "opacity": {"value": 0.5},
                        "stroke": {"value": "#FF0000", "scale": color_scale_name, "field": FIELD_CATEGORY_NAME},
                        "fill": {"value": "transparent"}
                    }
                },
            }
        ]
    }

    return res


def save_vega_spec(request: GenerationRequest, vega_spec: Dict):
    json_string = json.dumps(vega_spec, indent=2)

    path = Path(__file__).parent.resolve() / '..' / GENERATED_DIR_NAME / generate_relative_path_to_spec(request)
    with open(path, "w") as file:
        file.write(json_string)


def generate_data(request: GenerationRequest) -> None:
    # noinspection PyUnusedLocal
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
                     / generate_relative_path_to_data(request))

    if request.data_format == DataFormat.CSV:
        with open(out_file_name, "w") as f:
            writer = csv.writer(f)
            writer.writerow(generate_csv_header_row(request))

        for row in generate_rows(request):
            writer.writerow(row)
    elif request.data_format == DataFormat.JSON:
        rows = list(generate_rows(request))
        with open(out_file_name, "w") as f:
            f.write(json.dumps(rows))
    else:
        assert False, "unknown data format " + request.data_format.value


def generate_html(request: GenerationRequest) -> str:
    env = Environment(
        loader=PackageLoader('vis-study'),
        autoescape=select_autoescape()
    )

    template = env.get_template('index.html')
    return template.render(
        request=request,
        path_to_data=generate_relative_path_to_data(request),
        path_to_spec=generate_relative_path_to_spec(request)
    )


def generate_relative_path_to_html(request: GenerationRequest) -> str:
    return request.experiment_name + ".html"


def generate_relative_path_to_data(request: GenerationRequest) -> str:
    return DATA_DIR_NAME + "/" + request.experiment_name + '_data.json'


def generate_relative_path_to_spec(request: GenerationRequest) -> str:
    return SPECS_DIR_NAME + "/" + request.experiment_name + '_spec.json'


def save_html(request: GenerationRequest, html: str) -> None:
    path = Path(__file__).parent.resolve() / '..' / GENERATED_DIR_NAME / generate_relative_path_to_html(request)
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
        num_categories=4,
        width=500,
        height=500,
        data_format=DataFormat.JSON,
        num_attributes=5,
        renderer=Renderer.CANVAS
    )

    generate_all(request)
