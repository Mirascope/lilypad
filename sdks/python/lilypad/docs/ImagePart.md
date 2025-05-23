# ImagePart

Image part model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**media_type** | **str** |  | 
**image** | **str** |  | 
**detail** | **str** |  | 

## Example

```python
from lilypad.models.image_part import ImagePart

# TODO update the JSON string below
json = "{}"
# create an instance of ImagePart from a JSON string
image_part_instance = ImagePart.from_json(json)
# print the JSON string representation of the object
print(ImagePart.to_json())

# convert the object into a dict
image_part_dict = image_part_instance.to_dict()
# create an instance of ImagePart from a dict
image_part_from_dict = ImagePart.from_dict(image_part_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


