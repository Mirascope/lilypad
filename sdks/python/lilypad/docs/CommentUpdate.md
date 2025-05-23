# CommentUpdate

Comment Update Model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | [optional] 
**is_edited** | **bool** |  | [optional] 

## Example

```python
from lilypad.models.comment_update import CommentUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of CommentUpdate from a JSON string
comment_update_instance = CommentUpdate.from_json(json)
# print the JSON string representation of the object
print(CommentUpdate.to_json())

# convert the object into a dict
comment_update_dict = comment_update_instance.to_dict()
# create an instance of CommentUpdate from a dict
comment_update_from_dict = CommentUpdate.from_dict(comment_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


