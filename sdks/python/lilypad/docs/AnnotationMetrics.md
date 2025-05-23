# AnnotationMetrics

Annotation metrics model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_uuid** | **str** |  | 
**total_count** | **int** |  | 
**success_count** | **int** |  | 

## Example

```python
from lilypad.models.annotation_metrics import AnnotationMetrics

# TODO update the JSON string below
json = "{}"
# create an instance of AnnotationMetrics from a JSON string
annotation_metrics_instance = AnnotationMetrics.from_json(json)
# print the JSON string representation of the object
print(AnnotationMetrics.to_json())

# convert the object into a dict
annotation_metrics_dict = annotation_metrics_instance.to_dict()
# create an instance of AnnotationMetrics from a dict
annotation_metrics_from_dict = AnnotationMetrics.from_dict(annotation_metrics_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


