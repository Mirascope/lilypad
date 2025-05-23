# SpanMoreDetails

Span more details model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uuid** | **str** |  | 
**project_uuid** | **str** |  | 
**function_uuid** | **str** |  | [optional] 
**display_name** | **str** |  | 
**provider** | **str** |  | 
**model** | **str** |  | 
**scope** | [**Scope**](Scope.md) |  | 
**input_tokens** | **float** |  | [optional] 
**output_tokens** | **float** |  | [optional] 
**duration_ms** | **float** |  | [optional] 
**signature** | **str** |  | [optional] 
**code** | **str** |  | [optional] 
**arg_values** | **object** |  | [optional] 
**output** | **str** |  | [optional] 
**messages** | [**List[MessageParam]**](MessageParam.md) |  | 
**data** | **object** |  | 
**cost** | **float** |  | [optional] 
**template** | **str** |  | [optional] 
**status** | **str** |  | [optional] 
**events** | [**List[Event]**](Event.md) |  | [optional] 
**tags** | [**List[TagPublic]**](TagPublic.md) |  | [optional] 
**session_id** | **str** |  | [optional] 
**span_id** | **str** |  | 
**response** | **object** |  | [optional] 
**response_model** | **object** |  | [optional] 

## Example

```python
from lilypad.models.span_more_details import SpanMoreDetails

# TODO update the JSON string below
json = "{}"
# create an instance of SpanMoreDetails from a JSON string
span_more_details_instance = SpanMoreDetails.from_json(json)
# print the JSON string representation of the object
print(SpanMoreDetails.to_json())

# convert the object into a dict
span_more_details_dict = span_more_details_instance.to_dict()
# create an instance of SpanMoreDetails from a dict
span_more_details_from_dict = SpanMoreDetails.from_dict(span_more_details_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


