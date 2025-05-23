# AnnotationPublic

Annotation public model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**label** | [**Label**](Label.md) |  | [optional] 
**reasoning** | **str** |  | [optional] 
**type** | [**EvaluationType**](EvaluationType.md) |  | [optional] 
**data** | **object** |  | [optional] 
**assigned_to** | **str** |  | [optional] 
**uuid** | **str** |  | 
**project_uuid** | **str** |  | 
**span_uuid** | **str** |  | 
**function_uuid** | **str** |  | [optional] 
**created_at** | **datetime** |  | 
**span** | [**SpanMoreDetails**](SpanMoreDetails.md) |  | 

## Example

```python
from lilypad.models.annotation_public import AnnotationPublic

# TODO update the JSON string below
json = "{}"
# create an instance of AnnotationPublic from a JSON string
annotation_public_instance = AnnotationPublic.from_json(json)
# print the JSON string representation of the object
print(AnnotationPublic.to_json())

# convert the object into a dict
annotation_public_dict = annotation_public_instance.to_dict()
# create an instance of AnnotationPublic from a dict
annotation_public_from_dict = AnnotationPublic.from_dict(annotation_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


