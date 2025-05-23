# PlaygroundErrorResponse

Standard structure for playground error responses.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | [**PlaygroundErrorDetail**](PlaygroundErrorDetail.md) |  | 

## Example

```python
from lilypad.models.playground_error_response import PlaygroundErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of PlaygroundErrorResponse from a JSON string
playground_error_response_instance = PlaygroundErrorResponse.from_json(json)
# print the JSON string representation of the object
print(PlaygroundErrorResponse.to_json())

# convert the object into a dict
playground_error_response_dict = playground_error_response_instance.to_dict()
# create an instance of PlaygroundErrorResponse from a dict
playground_error_response_from_dict = PlaygroundErrorResponse.from_dict(playground_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


