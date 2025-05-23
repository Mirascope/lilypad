# UserConsentCreate

UserConsent create model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**privacy_policy_version** | **str** |  | 
**privacy_policy_accepted_at** | **datetime** |  | [optional] 
**tos_version** | **str** |  | 
**tos_accepted_at** | **datetime** |  | [optional] 
**user_uuid** | **str** |  | [optional] 

## Example

```python
from lilypad.models.user_consent_create import UserConsentCreate

# TODO update the JSON string below
json = "{}"
# create an instance of UserConsentCreate from a JSON string
user_consent_create_instance = UserConsentCreate.from_json(json)
# print the JSON string representation of the object
print(UserConsentCreate.to_json())

# convert the object into a dict
user_consent_create_dict = user_consent_create_instance.to_dict()
# create an instance of UserConsentCreate from a dict
user_consent_create_from_dict = UserConsentCreate.from_dict(user_consent_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


