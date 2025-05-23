# TagPublic

Tag Public Model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**project_uuid** | **str** |  | [optional] 
**name** | **str** |  | 
**uuid** | **str** |  | 
**created_at** | **datetime** |  | 
**organization_uuid** | **str** |  | 

## Example

```python
from lilypad.models.tag_public import TagPublic

# TODO update the JSON string below
json = "{}"
# create an instance of TagPublic from a JSON string
tag_public_instance = TagPublic.from_json(json)
# print the JSON string representation of the object
print(TagPublic.to_json())

# convert the object into a dict
tag_public_dict = tag_public_instance.to_dict()
# create an instance of TagPublic from a dict
tag_public_from_dict = TagPublic.from_dict(tag_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


