# PlaygroundParameters

Playground parameters model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**arg_values** | [**Dict[str, ArgValuesValue]**](ArgValuesValue.md) |  | 
**arg_types** | **Dict[str, str]** |  | 
**provider** | [**Provider**](Provider.md) |  | 
**model** | **str** |  | 
**prompt_template** | **str** |  | 
**call_params** | [**CommonCallParams**](CommonCallParams.md) |  | 

## Example

```python
from lilypad.models.playground_parameters import PlaygroundParameters

# TODO update the JSON string below
json = "{}"
# create an instance of PlaygroundParameters from a JSON string
playground_parameters_instance = PlaygroundParameters.from_json(json)
# print the JSON string representation of the object
print(PlaygroundParameters.to_json())

# convert the object into a dict
playground_parameters_dict = playground_parameters_instance.to_dict()
# create an instance of PlaygroundParameters from a dict
playground_parameters_from_dict = PlaygroundParameters.from_dict(playground_parameters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


