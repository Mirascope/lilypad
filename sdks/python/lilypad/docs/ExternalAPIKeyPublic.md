# ExternalAPIKeyPublic

Response model for a secret.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**service_name** | **str** |  | 
**masked_api_key** | **str** | Partially masked API key | 

## Example

```python
from lilypad.models.external_api_key_public import ExternalAPIKeyPublic

# TODO update the JSON string below
json = "{}"
# create an instance of ExternalAPIKeyPublic from a JSON string
external_api_key_public_instance = ExternalAPIKeyPublic.from_json(json)
# print the JSON string representation of the object
print(ExternalAPIKeyPublic.to_json())

# convert the object into a dict
external_api_key_public_dict = external_api_key_public_instance.to_dict()
# create an instance of ExternalAPIKeyPublic from a dict
external_api_key_public_from_dict = ExternalAPIKeyPublic.from_dict(external_api_key_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


