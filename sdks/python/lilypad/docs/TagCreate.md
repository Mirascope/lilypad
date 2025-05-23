# TagCreate

Tag Create Model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**project_uuid** | **str** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from lilypad.models.tag_create import TagCreate

# TODO update the JSON string below
json = "{}"
# create an instance of TagCreate from a JSON string
tag_create_instance = TagCreate.from_json(json)
# print the JSON string representation of the object
print(TagCreate.to_json())

# convert the object into a dict
tag_create_dict = tag_create_instance.to_dict()
# create an instance of TagCreate from a dict
tag_create_from_dict = TagCreate.from_dict(tag_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


