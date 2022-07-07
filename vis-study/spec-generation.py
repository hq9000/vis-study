from dataclasses import dataclass
from enum import Enum
from typing import Dict


class DataFormat(Enum):
    CSV = 'csv'
    JSON = 'json'


@dataclass
class GenerationRequest(object):
    experiment_name: str
    num_points: int
    num_categories: int
    data_format: DataFormat



def generate_vega_spec(request: GenerationRequest) -> Dict:
    pass
