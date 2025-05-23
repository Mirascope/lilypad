# UserOrganizationPublic

UserOrganization public model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role** | [**UserRole**](UserRole.md) |  | 
**user_uuid** | **str** |  | 
**uuid** | **str** |  | 
**organization_uuid** | **str** |  | 
**organization** | [**OrganizationPublic**](OrganizationPublic.md) |  | 

## Example

```python
from lilypad.models.user_organization_public import UserOrganizationPublic

# TODO update the JSON string below
json = "{}"
# create an instance of UserOrganizationPublic from a JSON string
user_organization_public_instance = UserOrganizationPublic.from_json(json)
# print the JSON string representation of the object
print(UserOrganizationPublic.to_json())

# convert the object into a dict
user_organization_public_dict = user_organization_public_instance.to_dict()
# create an instance of UserOrganizationPublic from a dict
user_organization_public_from_dict = UserOrganizationPublic.from_dict(user_organization_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


