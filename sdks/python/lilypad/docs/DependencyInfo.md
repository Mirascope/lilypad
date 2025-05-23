# DependencyInfo

Dependency information.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version** | **str** |  | 
**extras** | **List[str]** |  | 

## Example

```python
from lilypad.models.dependency_info import DependencyInfo

# TODO update the JSON string below
json = "{}"
# create an instance of DependencyInfo from a JSON string
dependency_info_instance = DependencyInfo.from_json(json)
# print the JSON string representation of the object
print(DependencyInfo.to_json())

# convert the object into a dict
dependency_info_dict = dependency_info_instance.to_dict()
# create an instance of DependencyInfo from a dict
dependency_info_from_dict = DependencyInfo.from_dict(dependency_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


