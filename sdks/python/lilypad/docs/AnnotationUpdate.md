# AnnotationUpdate

Annotation update model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**label** | [**Label**](Label.md) |  | [optional] 
**reasoning** | **str** |  | [optional] 
**type** | [**EvaluationType**](EvaluationType.md) |  | [optional] 
**data** | **object** |  | [optional] 
**assigned_to** | **str** |  | [optional] 

## Example

```python
from lilypad.models.annotation_update import AnnotationUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of AnnotationUpdate from a JSON string
annotation_update_instance = AnnotationUpdate.from_json(json)
# print the JSON string representation of the object
print(AnnotationUpdate.to_json())

# convert the object into a dict
annotation_update_dict = annotation_update_instance.to_dict()
# create an instance of AnnotationUpdate from a dict
annotation_update_from_dict = AnnotationUpdate.from_dict(annotation_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


