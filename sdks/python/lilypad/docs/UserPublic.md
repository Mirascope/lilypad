# UserPublic

User public model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**first_name** | **str** |  | 
**last_name** | **str** |  | [optional] 
**email** | **str** |  | 
**active_organization_uuid** | **str** |  | [optional] 
**keys** | **Dict[str, str]** |  | [optional] 
**uuid** | **str** |  | 
**access_token** | **str** |  | [optional] 
**user_organizations** | [**List[UserOrganizationPublic]**](UserOrganizationPublic.md) |  | [optional] 
**scopes** | **List[str]** |  | [optional] 
**user_consents** | [**UserConsentPublic**](UserConsentPublic.md) |  | [optional] 

## Example

```python
from lilypad.models.user_public import UserPublic

# TODO update the JSON string below
json = "{}"
# create an instance of UserPublic from a JSON string
user_public_instance = UserPublic.from_json(json)
# print the JSON string representation of the object
print(UserPublic.to_json())

# convert the object into a dict
user_public_dict = user_public_instance.to_dict()
# create an instance of UserPublic from a dict
user_public_from_dict = UserPublic.from_dict(user_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


