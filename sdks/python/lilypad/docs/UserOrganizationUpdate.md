# UserOrganizationUpdate

UserOrganization update model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**role** | [**UserRole**](UserRole.md) |  | 

## Example

```python
from lilypad.models.user_organization_update import UserOrganizationUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of UserOrganizationUpdate from a JSON string
user_organization_update_instance = UserOrganizationUpdate.from_json(json)
# print the JSON string representation of the object
print(UserOrganizationUpdate.to_json())

# convert the object into a dict
user_organization_update_dict = user_organization_update_instance.to_dict()
# create an instance of UserOrganizationUpdate from a dict
user_organization_update_from_dict = UserOrganizationUpdate.from_dict(user_organization_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


