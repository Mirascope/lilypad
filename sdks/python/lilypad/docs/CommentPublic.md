# CommentPublic

Comment Public Model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | 
**user_uuid** | **str** |  | 
**span_uuid** | **str** |  | 
**parent_comment_uuid** | **str** |  | [optional] 
**updated_at** | **datetime** |  | [optional] 
**is_edited** | **bool** |  | [optional] [default to False]
**uuid** | **str** |  | 
**created_at** | **datetime** |  | 

## Example

```python
from lilypad.models.comment_public import CommentPublic

# TODO update the JSON string below
json = "{}"
# create an instance of CommentPublic from a JSON string
comment_public_instance = CommentPublic.from_json(json)
# print the JSON string representation of the object
print(CommentPublic.to_json())

# convert the object into a dict
comment_public_dict = comment_public_instance.to_dict()
# create an instance of CommentPublic from a dict
comment_public_from_dict = CommentPublic.from_dict(comment_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


