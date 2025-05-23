# MessageParam

Message param model agnostic to providers.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role** | **str** |  | 
**content** | [**List[MessageParamContentInner]**](MessageParamContentInner.md) |  | 

## Example

```python
from lilypad.models.message_param import MessageParam

# TODO update the JSON string below
json = "{}"
# create an instance of MessageParam from a JSON string
message_param_instance = MessageParam.from_json(json)
# print the JSON string representation of the object
print(MessageParam.to_json())

# convert the object into a dict
message_param_dict = message_param_instance.to_dict()
# create an instance of MessageParam from a dict
message_param_from_dict = MessageParam.from_dict(message_param_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


