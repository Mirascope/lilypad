# PaginatedSpanPublic


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[SpanPublic]**](SpanPublic.md) | Current slice of items | 
**limit** | **int** | Requested page size (limit) | 
**offset** | **int** | Requested offset | 
**total** | **int** | Total number of items | 

## Example

```python
from lilypad.models.paginated_span_public import PaginatedSpanPublic

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedSpanPublic from a JSON string
paginated_span_public_instance = PaginatedSpanPublic.from_json(json)
# print the JSON string representation of the object
print(PaginatedSpanPublic.to_json())

# convert the object into a dict
paginated_span_public_dict = paginated_span_public_instance.to_dict()
# create an instance of PaginatedSpanPublic from a dict
paginated_span_public_from_dict = PaginatedSpanPublic.from_dict(paginated_span_public_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


