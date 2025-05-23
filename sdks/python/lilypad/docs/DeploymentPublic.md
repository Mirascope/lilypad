# DeploymentPublic

Deployment public model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**environment_uuid** | **str** |  | 
**function_uuid** | **str** |  | 
**project_uuid** | **str** |  | [optional] 
**is_active** | **bool** |  | [optional] [default to True]
**version_num** | **int** |  | [optional] [default to 1]
**notes** | **str** |  | [optional] 
**activated_at** | **datetime** | Timestamp when the deployment was activated. | [optional] 
**uuid** | **str** |  | 
**organization_uuid** | **str** |  | 
**function** | [**FunctionPublic**](FunctionPublic.md) |  | [optional] 
**environment** | [**EnvironmentPublic**](EnvironmentPublic.md) |  | [optional] 

## Example

```python
from lilypad.models.deployment_public import DeploymentPublic

# TODO update the JSON string below
json = "{}"
# create an instance of DeploymentPublic from a JSON string
deployment_public_instance = DeploymentPublic.from_json(json)
# print the JSON string representation of the object
print(DeploymentPublic.to_json())

# convert the object into a dict
deployment_public_dict = deployment_public_instance.to_dict()
# create an instance of DeploymentPublic from a dict
deployment_public_from_dict = DeploymentPublic.from_dict(deployment_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


