# CommentCreate

Comment Create Model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | 
**span_uuid** | **str** |  | 
**parent_comment_uuid** | **str** |  | [optional] 

## Example

```python
from lilypad.models.comment_create import CommentCreate

# TODO update the JSON string below
json = "{}"
# create an instance of CommentCreate from a JSON string
comment_create_instance = CommentCreate.from_json(json)
# print the JSON string representation of the object
print(CommentCreate.to_json())

# convert the object into a dict
comment_create_dict = comment_create_instance.to_dict()
# create an instance of CommentCreate from a dict
comment_create_from_dict = CommentCreate.from_dict(comment_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


