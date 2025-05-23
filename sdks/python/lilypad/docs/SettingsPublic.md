# SettingsPublic


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**remote_client_url** | **str** |  | 
**remote_api_url** | **str** |  | 
**github_client_id** | **str** |  | 
**google_client_id** | **str** |  | 
**environment** | **str** |  | 
**experimental** | **bool** |  | 

## Example

```python
from lilypad.models.settings_public import SettingsPublic

# TODO update the JSON string below
json = "{}"
# create an instance of SettingsPublic from a JSON string
settings_public_instance = SettingsPublic.from_json(json)
# print the JSON string representation of the object
print(SettingsPublic.to_json())

# convert the object into a dict
settings_public_dict = settings_public_instance.to_dict()
# create an instance of SettingsPublic from a dict
settings_public_from_dict = SettingsPublic.from_dict(settings_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


