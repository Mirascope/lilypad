# ProjectPublic

Project Public Model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**uuid** | **str** |  | 
**functions** | [**List[FunctionPublic]**](FunctionPublic.md) |  | [optional] [default to []]
**created_at** | **datetime** |  | 

## Example

```python
from lilypad.models.project_public import ProjectPublic

# TODO update the JSON string below
json = "{}"
# create an instance of ProjectPublic from a JSON string
project_public_instance = ProjectPublic.from_json(json)
# print the JSON string representation of the object
print(ProjectPublic.to_json())

# convert the object into a dict
project_public_dict = project_public_instance.to_dict()
# create an instance of ProjectPublic from a dict
project_public_from_dict = ProjectPublic.from_dict(project_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


