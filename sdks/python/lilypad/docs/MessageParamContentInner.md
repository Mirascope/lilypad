# MessageParamContentInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**media_type** | **str** |  | 
**audio** | **str** |  | 
**text** | **str** |  | 
**image** | **str** |  | 
**detail** | **str** |  | 
**name** | **str** |  | 
**arguments** | **object** |  | 

## Example

```python
from lilypad.models.message_param_content_inner import MessageParamContentInner

# TODO update the JSON string below
json = "{}"
# create an instance of MessageParamContentInner from a JSON string
message_param_content_inner_instance = MessageParamContentInner.from_json(json)
# print the JSON string representation of the object
print(MessageParamContentInner.to_json())

# convert the object into a dict
message_param_content_inner_dict = message_param_content_inner_instance.to_dict()
# create an instance of MessageParamContentInner from a dict
message_param_content_inner_from_dict = MessageParamContentInner.from_dict(message_param_content_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


