"""Test utilities for exporter tests."""

from typing import Any


def extract_transport_data(transport_result: Any) -> dict[str, Any]:
    """Extract data from transport result for snapshot testing."""
    if hasattr(transport_result, "__dict__"):
        result = {}
        for key, value in transport_result.__dict__.items():
            if not key.startswith("_"):
                if hasattr(value, "__dict__"):
                    result[key] = extract_transport_data(value)
                elif isinstance(value, (list, tuple)):
                    result[key] = [
                        extract_transport_data(item)
                        if hasattr(item, "__dict__")
                        else item
                        for item in value
                    ]
                else:
                    result[key] = value
        return result
    return transport_result


def extract_otlp_span_data(otlp_span: Any) -> dict[str, Any]:
    """Extract data from OTLP span for snapshot testing."""
    return {
        "trace_id": otlp_span.trace_id if hasattr(otlp_span, "trace_id") else None,
        "span_id": otlp_span.span_id if hasattr(otlp_span, "span_id") else None,
        "parent_span_id": otlp_span.parent_span_id
        if hasattr(otlp_span, "parent_span_id")
        else None,
        "name": otlp_span.name if hasattr(otlp_span, "name") else None,
        "kind": otlp_span.kind if hasattr(otlp_span, "kind") else None,
        "start_time_unix_nano": otlp_span.start_time_unix_nano
        if hasattr(otlp_span, "start_time_unix_nano")
        else None,
        "end_time_unix_nano": otlp_span.end_time_unix_nano
        if hasattr(otlp_span, "end_time_unix_nano")
        else None,
        "attributes": [
            {"key": attr.key, "value": extract_attribute_value(attr.value)}
            for attr in (
                otlp_span.attributes
                if hasattr(otlp_span, "attributes") and otlp_span.attributes
                else []
            )
        ],
        "status": {
            "code": otlp_span.status.code
            if hasattr(otlp_span, "status") and otlp_span.status
            else None,
            "message": otlp_span.status.message
            if hasattr(otlp_span, "status")
            and otlp_span.status
            and hasattr(otlp_span.status, "message")
            else None,
        }
        if hasattr(otlp_span, "status") and otlp_span.status
        else None,
    }


def extract_attribute_value(value: Any) -> dict[str, Any]:
    """Extract attribute value for snapshot testing."""
    if hasattr(value, "string_value"):
        return {"string_value": value.string_value}
    elif hasattr(value, "int_value"):
        return {"int_value": value.int_value}
    elif hasattr(value, "double_value"):
        return {"double_value": value.double_value}
    elif hasattr(value, "bool_value"):
        return {"bool_value": value.bool_value}
    return {"unknown": str(value)}


def extract_resource_spans_data(resource_spans_list: list) -> list[dict[str, Any]]:
    """Extract data from resource spans list for snapshot testing."""
    result = []
    for rs in resource_spans_list:
        resource_data = {
            "resource": {
                "attributes": [
                    {"key": attr.key, "value": extract_attribute_value(attr.value)}
                    for attr in (
                        rs.resource.attributes
                        if hasattr(rs.resource, "attributes") and rs.resource.attributes
                        else []
                    )
                ]
                if hasattr(rs, "resource")
                else []
            },
            "scope_spans": [],
        }

        if hasattr(rs, "scope_spans"):
            for ss in rs.scope_spans:
                scope_data = {
                    "scope": {
                        "name": ss.scope.name if hasattr(ss.scope, "name") else None,
                        "version": ss.scope.version
                        if hasattr(ss.scope, "version")
                        else None,
                    }
                    if hasattr(ss, "scope")
                    else None,
                    "spans": [
                        extract_otlp_span_data(span)
                        for span in (ss.spans if hasattr(ss, "spans") else [])
                    ],
                }
                resource_data["scope_spans"].append(scope_data)

        result.append(resource_data)

    return result
