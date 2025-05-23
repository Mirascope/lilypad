# AudioPart

Image part model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**media_type** | **str** |  | 
**audio** | **str** |  | 

## Example

```python
from lilypad.models.audio_part import AudioPart

# TODO update the JSON string below
json = "{}"
# create an instance of AudioPart from a JSON string
audio_part_instance = AudioPart.from_json(json)
# print the JSON string representation of the object
print(AudioPart.to_json())

# convert the object into a dict
audio_part_dict = audio_part_instance.to_dict()
# create an instance of AudioPart from a dict
audio_part_from_dict = AudioPart.from_dict(audio_part_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


