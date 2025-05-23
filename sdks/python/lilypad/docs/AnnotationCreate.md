# AnnotationCreate

Annotation create model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**span_uuid** | **str** |  | [optional] 
**project_uuid** | **str** |  | [optional] 
**function_uuid** | **str** |  | [optional] 
**label** | [**Label**](Label.md) |  | [optional] 
**reasoning** | **str** |  | [optional] 
**type** | [**EvaluationType**](EvaluationType.md) |  | [optional] 
**data** | **object** |  | [optional] 
**assigned_to** | **List[str]** |  | [optional] 
**assignee_email** | **List[str]** |  | [optional] 

## Example

```python
from lilypad.models.annotation_create import AnnotationCreate

# TODO update the JSON string below
json = "{}"
# create an instance of AnnotationCreate from a JSON string
annotation_create_instance = AnnotationCreate.from_json(json)
# print the JSON string representation of the object
print(AnnotationCreate.to_json())

# convert the object into a dict
annotation_create_dict = annotation_create_instance.to_dict()
# create an instance of AnnotationCreate from a dict
annotation_create_from_dict = AnnotationCreate.from_dict(annotation_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


