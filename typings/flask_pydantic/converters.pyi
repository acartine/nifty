"""
This type stub file was generated by pyright.
"""

from typing import Type
from pydantic import BaseModel
from werkzeug.datastructures import ImmutableMultiDict

def convert_query_params(
    query_params: ImmutableMultiDict, model: Type[BaseModel]
) -> dict:
    """
    group query parameters into lists if model defines them

    :param query_params: flasks request.args
    :param model: query parameter's model
    :return: resulting parameters
    """
    ...
