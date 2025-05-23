# OrganizationPublic

Organization public model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**uuid** | **str** |  | 

## Example

```python
from lilypad.models.organization_public import OrganizationPublic

# TODO update the JSON string below
json = "{}"
# create an instance of OrganizationPublic from a JSON string
organization_public_instance = OrganizationPublic.from_json(json)
# print the JSON string representation of the object
print(OrganizationPublic.to_json())

# convert the object into a dict
organization_public_dict = organization_public_instance.to_dict()
# create an instance of OrganizationPublic from a dict
organization_public_from_dict = OrganizationPublic.from_dict(organization_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


