# LicenseInfo

Pydantic model for license validation

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**customer** | **str** |  | 
**license_id** | **str** |  | 
**expires_at** | **datetime** |  | 
**tier** | [**Tier**](Tier.md) |  | 
**organization_uuid** | **str** |  | 
**is_expired** | **bool** | Check if the license has expired | [readonly] 

## Example

```python
from lilypad.models.license_info import LicenseInfo

# TODO update the JSON string below
json = "{}"
# create an instance of LicenseInfo from a JSON string
license_info_instance = LicenseInfo.from_json(json)
# print the JSON string representation of the object
print(LicenseInfo.to_json())

# convert the object into a dict
license_info_dict = license_info_instance.to_dict()
# create an instance of LicenseInfo from a dict
license_info_from_dict = LicenseInfo.from_dict(license_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


