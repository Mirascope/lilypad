# APIKeyPublic

API key public model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**expires_at** | **datetime** |  | [optional] 
**project_uuid** | **str** |  | 
**environment_uuid** | **str** |  | [optional] 
**uuid** | **str** |  | 
**key_hash** | **str** |  | 
**user** | [**UserPublic**](UserPublic.md) |  | 
**project** | [**ProjectPublic**](ProjectPublic.md) |  | 
**environment** | [**EnvironmentPublic**](EnvironmentPublic.md) |  | 

## Example

```python
from lilypad.models.api_key_public import APIKeyPublic

# TODO update the JSON string below
json = "{}"
# create an instance of APIKeyPublic from a JSON string
api_key_public_instance = APIKeyPublic.from_json(json)
# print the JSON string representation of the object
print(APIKeyPublic.to_json())

# convert the object into a dict
api_key_public_dict = api_key_public_instance.to_dict()
# create an instance of APIKeyPublic from a dict
api_key_public_from_dict = APIKeyPublic.from_dict(api_key_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


