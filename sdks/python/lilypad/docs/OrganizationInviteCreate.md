# OrganizationInviteCreate

OrganizationInvite create model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invited_by** | **str** |  | 
**email** | **str** |  | 
**expires_at** | **datetime** |  | [optional] 
**token** | **str** |  | [optional] 
**resend_email_id** | **str** |  | [optional] 
**organization_uuid** | **str** |  | [optional] 

## Example

```python
from lilypad.models.organization_invite_create import OrganizationInviteCreate

# TODO update the JSON string below
json = "{}"
# create an instance of OrganizationInviteCreate from a JSON string
organization_invite_create_instance = OrganizationInviteCreate.from_json(json)
# print the JSON string representation of the object
print(OrganizationInviteCreate.to_json())

# convert the object into a dict
organization_invite_create_dict = organization_invite_create_instance.to_dict()
# create an instance of OrganizationInviteCreate from a dict
organization_invite_create_from_dict = OrganizationInviteCreate.from_dict(organization_invite_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


