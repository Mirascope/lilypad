# EnvironmentPublic

Environment public model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**description** | **str** |  | [optional] 
**is_default** | **bool** |  | [optional] [default to False]
**uuid** | **str** |  | 
**organization_uuid** | **str** |  | 
**created_at** | **datetime** |  | 

## Example

```python
from lilypad.models.environment_public import EnvironmentPublic

# TODO update the JSON string below
json = "{}"
# create an instance of EnvironmentPublic from a JSON string
environment_public_instance = EnvironmentPublic.from_json(json)
# print the JSON string representation of the object
print(EnvironmentPublic.to_json())

# convert the object into a dict
environment_public_dict = environment_public_instance.to_dict()
# create an instance of EnvironmentPublic from a dict
environment_public_from_dict = EnvironmentPublic.from_dict(environment_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


