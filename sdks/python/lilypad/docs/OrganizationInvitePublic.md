# OrganizationInvitePublic

OrganizationInvite public model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invited_by** | **str** |  | 
**email** | **str** |  | 
**expires_at** | **datetime** |  | [optional] 
**uuid** | **str** |  | 
**organization_uuid** | **str** |  | 
**user** | [**UserPublic**](UserPublic.md) |  | 
**resend_email_id** | **str** |  | 
**invite_link** | **str** |  | [optional] 

## Example

```python
from lilypad.models.organization_invite_public import OrganizationInvitePublic

# TODO update the JSON string below
json = "{}"
# create an instance of OrganizationInvitePublic from a JSON string
organization_invite_public_instance = OrganizationInvitePublic.from_json(json)
# print the JSON string representation of the object
print(OrganizationInvitePublic.to_json())

# convert the object into a dict
organization_invite_public_dict = organization_invite_public_instance.to_dict()
# create an instance of OrganizationInvitePublic from a dict
organization_invite_public_from_dict = OrganizationInvitePublic.from_dict(organization_invite_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


