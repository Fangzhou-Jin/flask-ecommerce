"""
Unified JSON response helpers.

Flask-Smorest serializes Schema return values by default;
this module is used for error and message responses to keep API style consistent.
"""

from flask import jsonify


def success_response(data=None, message="Success", status_code=200):
    """Build a success response."""
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error_response(message="An error occurred", status_code=400, errors=None):
    """Build an error response."""
    payload = {"message": message}
    if errors is not None:
        payload["errors"] = errors
    return jsonify(payload), status_code
