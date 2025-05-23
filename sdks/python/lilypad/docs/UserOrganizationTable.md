# UserOrganizationTable

UserOrganization table.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uuid** | **str** |  | [optional] 
**created_at** | **datetime** |  | [optional] 
**organization_uuid** | **str** |  | 
**role** | [**UserRole**](UserRole.md) |  | 
**user_uuid** | **str** |  | 

## Example

```python
from lilypad.models.user_organization_table import UserOrganizationTable

# TODO update the JSON string below
json = "{}"
# create an instance of UserOrganizationTable from a JSON string
user_organization_table_instance = UserOrganizationTable.from_json(json)
# print the JSON string representation of the object
print(UserOrganizationTable.to_json())

# convert the object into a dict
user_organization_table_dict = user_organization_table_instance.to_dict()
# create an instance of UserOrganizationTable from a dict
user_organization_table_from_dict = UserOrganizationTable.from_dict(user_organization_table_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


