# UserConsentUpdate

UserConsent update model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**privacy_policy_version** | **str** |  | [optional] 
**privacy_policy_accepted_at** | **datetime** |  | [optional] 
**tos_version** | **str** |  | [optional] 
**tos_accepted_at** | **datetime** |  | [optional] 

## Example

```python
from lilypad.models.user_consent_update import UserConsentUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of UserConsentUpdate from a JSON string
user_consent_update_instance = UserConsentUpdate.from_json(json)
# print the JSON string representation of the object
print(UserConsentUpdate.to_json())

# convert the object into a dict
user_consent_update_dict = user_consent_update_instance.to_dict()
# create an instance of UserConsentUpdate from a dict
user_consent_update_from_dict = UserConsentUpdate.from_dict(user_consent_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


