# SpanPublic

Span public model

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**span_id** | **str** |  | 
**function_uuid** | **str** |  | [optional] 
**type** | [**SpanType**](SpanType.md) |  | [optional] 
**cost** | **float** |  | [optional] 
**scope** | [**Scope**](Scope.md) |  | 
**input_tokens** | **float** |  | [optional] 
**output_tokens** | **float** |  | [optional] 
**duration_ms** | **float** |  | [optional] 
**data** | **object** |  | [optional] 
**parent_span_id** | **str** |  | [optional] 
**session_id** | **str** |  | [optional] 
**uuid** | **str** |  | 
**project_uuid** | **str** |  | 
**display_name** | **str** |  | [optional] 
**function** | [**FunctionPublic**](FunctionPublic.md) |  | 
**annotations** | [**List[AnnotationPublic]**](AnnotationPublic.md) |  | 
**child_spans** | [**List[SpanPublic]**](SpanPublic.md) |  | 
**created_at** | **datetime** |  | 
**status** | **str** |  | [optional] 
**tags** | [**List[TagPublic]**](TagPublic.md) |  | 
**score** | **float** |  | [optional] 

## Example

```python
from lilypad.models.span_public import SpanPublic

# TODO update the JSON string below
json = "{}"
# create an instance of SpanPublic from a JSON string
span_public_instance = SpanPublic.from_json(json)
# print the JSON string representation of the object
print(SpanPublic.to_json())

# convert the object into a dict
span_public_dict = span_public_instance.to_dict()
# create an instance of SpanPublic from a dict
span_public_from_dict = SpanPublic.from_dict(span_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


