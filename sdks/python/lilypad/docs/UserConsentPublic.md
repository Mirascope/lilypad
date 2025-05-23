# UserConsentPublic

UserConsent public model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**privacy_policy_version** | **str** | Last updated date of the privacy policy accepted | [optional] [default to '2025-04-04']
**privacy_policy_accepted_at** | **datetime** |  | 
**tos_version** | **str** | Last updated date of the terms of service accepted | [optional] [default to '2025-04-04']
**tos_accepted_at** | **datetime** |  | 
**uuid** | **str** |  | 

## Example

```python
from lilypad.models.user_consent_public import UserConsentPublic

# TODO update the JSON string below
json = "{}"
# create an instance of UserConsentPublic from a JSON string
user_consent_public_instance = UserConsentPublic.from_json(json)
# print the JSON string representation of the object
print(UserConsentPublic.to_json())

# convert the object into a dict
user_consent_public_dict = user_consent_public_instance.to_dict()
# create an instance of UserConsentPublic from a dict
user_consent_public_from_dict = UserConsentPublic.from_dict(user_consent_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


