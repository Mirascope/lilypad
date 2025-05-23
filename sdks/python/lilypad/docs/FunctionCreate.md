# FunctionCreate

Function create model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**project_uuid** | **str** |  | [optional] 
**version_num** | **int** |  | [optional] 
**name** | **str** |  | 
**signature** | **str** |  | 
**code** | **str** |  | 
**hash** | **str** |  | 
**dependencies** | [**Dict[str, DependencyInfo]**](DependencyInfo.md) |  | [optional] 
**arg_types** | **Dict[str, str]** |  | [optional] 
**archived** | **datetime** |  | [optional] 
**custom_id** | **str** |  | [optional] 
**prompt_template** | **str** |  | [optional] 
**provider** | **str** |  | [optional] 
**model** | **str** |  | [optional] 
**call_params** | [**CommonCallParams**](CommonCallParams.md) |  | [optional] 
**is_versioned** | **bool** |  | [optional] 

## Example

```python
from lilypad.models.function_create import FunctionCreate

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionCreate from a JSON string
function_create_instance = FunctionCreate.from_json(json)
# print the JSON string representation of the object
print(FunctionCreate.to_json())

# convert the object into a dict
function_create_dict = function_create_instance.to_dict()
# create an instance of FunctionCreate from a dict
function_create_from_dict = FunctionCreate.from_dict(function_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


