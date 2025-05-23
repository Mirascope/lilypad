# SpanUpdate

Span update model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tags_by_uuid** | **List[str]** |  | [optional] 
**tags_by_name** | **List[str]** |  | [optional] 

## Example

```python
from lilypad.models.span_update import SpanUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of SpanUpdate from a JSON string
span_update_instance = SpanUpdate.from_json(json)
# print the JSON string representation of the object
print(SpanUpdate.to_json())

# convert the object into a dict
span_update_dict = span_update_instance.to_dict()
# create an instance of SpanUpdate from a dict
span_update_from_dict = SpanUpdate.from_dict(span_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


