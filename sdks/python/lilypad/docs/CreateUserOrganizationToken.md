# CreateUserOrganizationToken

Create user organization token model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**token** | **str** |  | 

## Example

```python
from lilypad.models.create_user_organization_token import CreateUserOrganizationToken

# TODO update the JSON string below
json = "{}"
# create an instance of CreateUserOrganizationToken from a JSON string
create_user_organization_token_instance = CreateUserOrganizationToken.from_json(json)
# print the JSON string representation of the object
print(CreateUserOrganizationToken.to_json())

# convert the object into a dict
create_user_organization_token_dict = create_user_organization_token_instance.to_dict()
# create an instance of CreateUserOrganizationToken from a dict
create_user_organization_token_from_dict = CreateUserOrganizationToken.from_dict(create_user_organization_token_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


