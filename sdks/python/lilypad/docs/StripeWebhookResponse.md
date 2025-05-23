# StripeWebhookResponse

Response schema for Stripe webhook events.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** |  | 
**event** | **str** |  | [optional] 
**message** | **str** |  | [optional] 

## Example

```python
from lilypad.models.stripe_webhook_response import StripeWebhookResponse

# TODO update the JSON string below
json = "{}"
# create an instance of StripeWebhookResponse from a JSON string
stripe_webhook_response_instance = StripeWebhookResponse.from_json(json)
# print the JSON string representation of the object
print(StripeWebhookResponse.to_json())

# convert the object into a dict
stripe_webhook_response_dict = stripe_webhook_response_instance.to_dict()
# create an instance of StripeWebhookResponse from a dict
stripe_webhook_response_from_dict = StripeWebhookResponse.from_dict(stripe_webhook_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


