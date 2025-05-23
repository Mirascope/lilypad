# TraceContextModel

Represents the tracing context information provided by Lilypad.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**span_uuid** | **str** |  | [optional] 

## Example

```python
from lilypad.models.trace_context_model import TraceContextModel

# TODO update the JSON string below
json = "{}"
# create an instance of TraceContextModel from a JSON string
trace_context_model_instance = TraceContextModel.from_json(json)
# print the JSON string representation of the object
print(TraceContextModel.to_json())

# convert the object into a dict
trace_context_model_dict = trace_context_model_instance.to_dict()
# create an instance of TraceContextModel from a dict
trace_context_model_from_dict = TraceContextModel.from_dict(trace_context_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


