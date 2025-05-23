# PlaygroundErrorDetail

Detailed information about a playground error.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | [**Type**](Type.md) |  | 
**reason** | **str** | User-friendly description of the error. | 
**details** | **str** |  | [optional] 

## Example

```python
from lilypad.models.playground_error_detail import PlaygroundErrorDetail

# TODO update the JSON string below
json = "{}"
# create an instance of PlaygroundErrorDetail from a JSON string
playground_error_detail_instance = PlaygroundErrorDetail.from_json(json)
# print the JSON string representation of the object
print(PlaygroundErrorDetail.to_json())

# convert the object into a dict
playground_error_detail_dict = playground_error_detail_instance.to_dict()
# create an instance of PlaygroundErrorDetail from a dict
playground_error_detail_from_dict = PlaygroundErrorDetail.from_dict(playground_error_detail_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


