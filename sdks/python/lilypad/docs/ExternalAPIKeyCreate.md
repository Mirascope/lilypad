# ExternalAPIKeyCreate

Request model for creating a secret.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**service_name** | **str** |  | 
**api_key** | **str** | New API key | 

## Example

```python
from lilypad.models.external_api_key_create import ExternalAPIKeyCreate

# TODO update the JSON string below
json = "{}"
# create an instance of ExternalAPIKeyCreate from a JSON string
external_api_key_create_instance = ExternalAPIKeyCreate.from_json(json)
# print the JSON string representation of the object
print(ExternalAPIKeyCreate.to_json())

# convert the object into a dict
external_api_key_create_dict = external_api_key_create_instance.to_dict()
# create an instance of ExternalAPIKeyCreate from a dict
external_api_key_create_from_dict = ExternalAPIKeyCreate.from_dict(external_api_key_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


