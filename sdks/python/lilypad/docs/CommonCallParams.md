# CommonCallParams

Common parameters shared across LLM providers.  Note: Each provider may handle these parameters differently or not support them at all. Please check provider-specific documentation for parameter support and behavior.  Attributes:     temperature: Controls randomness in the output (0.0 to 1.0).     max_tokens: Maximum number of tokens to generate.     top_p: Nucleus sampling parameter (0.0 to 1.0).     frequency_penalty: Penalizes frequent tokens (-2.0 to 2.0).     presence_penalty: Penalizes tokens based on presence (-2.0 to 2.0).     seed: Random seed for reproducibility.     stop: Stop sequence(s) to end generation.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**temperature** | **float** |  | [optional] 
**max_tokens** | **int** |  | [optional] 
**top_p** | **float** |  | [optional] 
**frequency_penalty** | **float** |  | [optional] 
**presence_penalty** | **float** |  | [optional] 
**seed** | **int** |  | [optional] 
**stop** | [**Stop**](Stop.md) |  | [optional] 

## Example

```python
from lilypad.models.common_call_params import CommonCallParams

# TODO update the JSON string below
json = "{}"
# create an instance of CommonCallParams from a JSON string
common_call_params_instance = CommonCallParams.from_json(json)
# print the JSON string representation of the object
print(CommonCallParams.to_json())

# convert the object into a dict
common_call_params_dict = common_call_params_instance.to_dict()
# create an instance of CommonCallParams from a dict
common_call_params_from_dict = CommonCallParams.from_dict(common_call_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


