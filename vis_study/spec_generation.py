import csv
import glob
import os
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Generator, List
import json
import jsons

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

    source_data_name = "table"
    selected_data_name = "selected"

    x_scale_name = "xscale"
    y_scale_name = "yscale"
    color_scale_name = "color"
    size_scale_name = "size"

    tooltip_signal_name = "tooltip"
    clicked_signal_name = "clicked"
    shift_signal_name = "shift"

    tooltip_derived_text_field_name = "tooltip_text"

    size_attribute_name = 'attr_0'

    def generate_tooltip_text_expression(request: GenerationRequest) -> str:
        # return " + ".join(['datum.attr_' + str(i) for i in range(request.num_attributes)])
        res = "'data: '"
        for i in range(request.num_attributes):
            res += " + ' ' + datum.attr_" + str(i)

        return res

    res: Dict = {
        "$schema": "https://vega.github.io/schema/vega/v5.json",
        "width": request.width,
        "height": request.height,
        "padding": 5,
        "data": [
            {
                "name": source_data_name,
                "url": generate_relative_path_to_data_file(request),
                "format": {"type": request.data_format.value, "parse": "auto"},
                "transform": [
                    {
                        "type": "formula",
                        "expr": generate_tooltip_text_expression(request),
                        "as": tooltip_derived_text_field_name
                    }
                ]
            },
            {
                "name": selected_data_name,
                "on": [
                    {"trigger": "!shift", "remove": True},
                    {"trigger": f"!shift && {clicked_signal_name}", "insert": clicked_signal_name},
                    {"trigger": f"{shift_signal_name} && {clicked_signal_name}", "toggle": clicked_signal_name}
                ]
            }
        ],
        "scales": [
            {
                "name": x_scale_name,
                "type": "linear",
                "domain": {"data": source_data_name, "field": FIELD_X_NAME},
                "range": "width",
                "padding": 0.05,
            },
            {
                "name": y_scale_name,
                "type": "linear",
                "domain": {"data": source_data_name, "field": FIELD_Y_NAME},
                "nice": True,
                "range": "height"
            },
            {
                "name": color_scale_name,
                "type": "ordinal",
                "range": {"scheme": "category10"},
                "domain": {"data": source_data_name, "field": FIELD_CATEGORY_NAME}
            },
            {
                "name": size_scale_name,
                "domain": {"data": source_data_name, "field": size_attribute_name},
                "zero": False,
                "range": [10, 1000]
            }
        ],
        "axes": [
            {"orient": "bottom", "scale": x_scale_name, "grid": True},
            {"orient": "left", "scale": y_scale_name, "grid": True}
        ],
        "signals": [
            {
                "name": tooltip_signal_name,
                "value": {},
                "on": [
                    {"events": "symbol:mouseover", "update": "datum"},
                    {"events": "symbol:mouseout", "update": "{}"}
                ]
            },
            {
                "name": "shift", "value": False,
                "on": [
                    {
                        "events": "@legendSymbol:click, @legendLabel:click",
                        "update": "event.shiftKey",
                        "force": True
                    }
                ]
            },
            {
                "name": clicked_signal_name, "value": None,
                "on": [
                    {
                        "events": "@legendSymbol:click, @legendLabel:click",
                        "update": "{value: datum.value}",
                        "force": True
                    }
                ]
            },
        ],
        "marks": [
            {
                "name": "marks",
                "type": "symbol",
                "from": {"data": source_data_name},
                "encode": {
                    "update": {
                        "x": {"scale": x_scale_name, "field": FIELD_X_NAME},
                        "y": {"scale": y_scale_name, "field": FIELD_Y_NAME},
                        "size": {"scale": size_scale_name, "field": size_attribute_name},
                        "shape": {"value": "circle"},
                        "strokeWidth": {"value": 2},
                        "opacity": [
                            {
                                "test": f"!length(data('{selected_data_name}')) || (indata('{selected_data_name}', 'value', datum.{FIELD_CATEGORY_NAME}))",
                                "value": 0.7},
                            {"value": 0.15}
                        ],
                        "stroke": {"value": "#FF0000", "scale": color_scale_name, "field": FIELD_CATEGORY_NAME},
                        "fill": {"value": "transparent", "scale": color_scale_name, "field": FIELD_CATEGORY_NAME}
                    }
                },
            },
            {
                "type": "text",
                "encode": {
                    "enter": {
                        "align": {"value": "center"},
                        "baseline": {"value": "bottom"},
                        "fill": {"value": "#333"}
                    },
                    "update": {
                        "x": {"scale": x_scale_name, "signal": tooltip_signal_name + "." + FIELD_X_NAME, "band": 0.5},
                        "y": {"scale": y_scale_name, "signal": tooltip_signal_name + "." + FIELD_Y_NAME, "offset": -2},
                        "text": {"signal": tooltip_signal_name + "." + tooltip_derived_text_field_name},
                        "fillOpacity": [
                            {"test": f"isNaN({tooltip_signal_name + '.' + FIELD_X_NAME})", "value": 1},
                            {"value": 1}
                        ]
                    }
                }
            }
        ],
        "legends": [
            {
                "stroke": "color",
                "title": "Origin",
                "encode": {
                    "symbols": {
                        "name": "legendSymbol",
                        "interactive": True,
                        "update": {
                            "fill": {"value": "transparent"},
                            "strokeWidth": {"value": 2},
                            "opacity": [
                                {
                                    "test": f"!length(data('{selected_data_name}')) || indata('{selected_data_name}', 'value', datum.value)",
                                    "value": 0.7},
                                {"value": 0.15}
                            ],
                            "size": {"value": 64}
                        }
                    },
                    "labels": {
                        "name": "legendLabel",
                        "interactive": True,
                        "update": {
                            "opacity": [
                                {
                                    "test": f"!length(data('{selected_data_name}')) || indata('{selected_data_name}', 'value', datum.value)",
                                    "value": 1},
                                {"value": 0.25}
                            ]
                        }
                    }
                }
            }
        ]
    }

    return res


def save_vega_spec(request: GenerationRequest, vega_spec: Dict):
    json_string = json.dumps(vega_spec, indent=2)

    path = Path(__file__).parent.resolve() / '..' / GENERATED_DIR_NAME / generate_relative_path_to_spec_file(request)
    with open(path, "w") as file:
        file.write(json_string)


def generate_data(request: GenerationRequest) -> None:
    # noinspection PyUnusedLocal
    def generate_one_row(request: GenerationRequest, i: int) -> Dict:

        category = 'category_' + str(random.randint(0, request.num_categories - 1))

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
                     / generate_relative_path_to_data_file(request))

    if request.data_format == DataFormat.CSV:
        with open(out_file_name, "w") as f:
            writer = csv.writer(f)
            writer.writerow(generate_csv_header_row(request))

            for row in generate_rows(request):
                writer.writerow(row.values())

    elif request.data_format == DataFormat.JSON:
        rows = list(generate_rows(request))
        with open(out_file_name, "w") as f:
            f.write(json.dumps(rows))
    else:
        assert False, "unknown data format " + request.data_format.value


def generate_html(request: GenerationRequest) -> str:
    env = Environment(
        loader=PackageLoader('vis_study'),
        autoescape=select_autoescape()
    )

    template = env.get_template('index.html')

    request_dict = jsons.dump(request)
    return template.render(
        request_object=request,
        request_dict=request_dict,
        path_to_data=generate_relative_path_to_data_file(request),
        path_to_spec=generate_relative_path_to_spec_file(request)
    )


def generate_slug(request: GenerationRequest) -> str:
    return f"points:{request.num_points}_format:{request.data_format.value}_categories:{request.num_categories}_renderer:{request.renderer.value}__{request.experiment_name}"


def generate_relative_path_to_html(request: GenerationRequest) -> str:
    return generate_slug(request) + ".html"


def generate_relative_path_to_data_file(request: GenerationRequest) -> str:
    return DATA_DIR_NAME + "/" + generate_slug(request) + '_data.' + request.data_format.value


def generate_relative_path_to_spec_file(request: GenerationRequest) -> str:
    return SPECS_DIR_NAME + "/" + generate_slug(request) + '_spec.json'


def save_html(request: GenerationRequest, html: str) -> None:
    path = Path(__file__).parent.resolve() / '..' / GENERATED_DIR_NAME / generate_relative_path_to_html(request)
    with open(path, "w") as file:
        file.write(html)


def generate(request: GenerationRequest) -> None:
    generate_data(request)

    vega_spec = generate_vega_spec(request)
    save_vega_spec(request, vega_spec)

    html = generate_html(request)
    save_html(request, html)


def _remove_all_files_by_mask(mask: str) -> None:
    fileList = glob.glob(mask)
    for filePath in fileList:
        os.remove(filePath)


def remove_all_generated_files() -> None:
    generated_files_dir = Path(__file__).parent.resolve() / '..' / GENERATED_DIR_NAME

    _remove_all_files_by_mask(f'{generated_files_dir}/{DATA_DIR_NAME}/*.{DataFormat.JSON.value}')
    _remove_all_files_by_mask(f'{generated_files_dir}/{DATA_DIR_NAME}/*.{DataFormat.CSV.value}')
    _remove_all_files_by_mask(f'{generated_files_dir}/{SPECS_DIR_NAME}/*.json')
    _remove_all_files_by_mask(f'{generated_files_dir}/*.html')