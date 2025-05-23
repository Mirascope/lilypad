# PlaygroundSuccessResponse

Standard structure for successful playground execution responses.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | **object** |  | 
**trace_context** | [**TraceContextModel**](TraceContextModel.md) |  | [optional] 

## Example

```python
from lilypad.models.playground_success_response import PlaygroundSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of PlaygroundSuccessResponse from a JSON string
playground_success_response_instance = PlaygroundSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(PlaygroundSuccessResponse.to_json())

# convert the object into a dict
playground_success_response_dict = playground_success_response_instance.to_dict()
# create an instance of PlaygroundSuccessResponse from a dict
playground_success_response_from_dict = PlaygroundSuccessResponse.from_dict(playground_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


