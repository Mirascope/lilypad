# ExternalAPIKeyUpdate

Request model for updating a secret.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**api_key** | **str** | New API key | 

## Example

```python
from lilypad.models.external_api_key_update import ExternalAPIKeyUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of ExternalAPIKeyUpdate from a JSON string
external_api_key_update_instance = ExternalAPIKeyUpdate.from_json(json)
# print the JSON string representation of the object
print(ExternalAPIKeyUpdate.to_json())

# convert the object into a dict
external_api_key_update_dict = external_api_key_update_instance.to_dict()
# create an instance of ExternalAPIKeyUpdate from a dict
external_api_key_update_from_dict = ExternalAPIKeyUpdate.from_dict(external_api_key_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


