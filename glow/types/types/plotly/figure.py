# Standard Library
from typing import Any
import json

# Third-party
from plotly.graph_objs import Figure

# Glow
from glow.types.registry import register_to_json_encodable_summary


@register_to_json_encodable_summary(Figure)
def _plotly_figure_summary(value: Figure, _) -> Any:
    return dict(figure=json.loads(value.to_json()))
