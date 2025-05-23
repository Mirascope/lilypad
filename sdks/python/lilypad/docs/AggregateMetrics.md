# AggregateMetrics

Aggregated metrics for spans

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_cost** | **float** |  | 
**total_input_tokens** | **float** |  | 
**total_output_tokens** | **float** |  | 
**average_duration_ms** | **float** |  | 
**span_count** | **int** |  | 
**start_date** | **datetime** |  | 
**end_date** | **datetime** |  | 
**function_uuid** | **str** |  | 

## Example

```python
from lilypad.models.aggregate_metrics import AggregateMetrics

# TODO update the JSON string below
json = "{}"
# create an instance of AggregateMetrics from a JSON string
aggregate_metrics_instance = AggregateMetrics.from_json(json)
# print the JSON string representation of the object
print(AggregateMetrics.to_json())

# convert the object into a dict
aggregate_metrics_dict = aggregate_metrics_instance.to_dict()
# create an instance of AggregateMetrics from a dict
aggregate_metrics_from_dict = AggregateMetrics.from_dict(aggregate_metrics_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


