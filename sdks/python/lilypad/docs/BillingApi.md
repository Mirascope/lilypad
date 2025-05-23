# lilypad.BillingApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**webhook**](BillingApi.md#webhook) | **POST** /webhooks/stripe | Stripe Webhook


# **webhook**
> StripeWebhookResponse webhook(stripe_signature=stripe_signature)

Stripe Webhook

Handle Stripe webhook events.

This endpoint receives webhook events from Stripe and updates the billing records.

### Example


```python
import lilypad
from lilypad.models.stripe_webhook_response import StripeWebhookResponse
from lilypad.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = lilypad.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with lilypad.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = lilypad.BillingApi(api_client)
    stripe_signature = 'stripe_signature_example' # str |  (optional)

    try:
        # Stripe Webhook
        api_response = api_instance.webhook(stripe_signature=stripe_signature)
        print("The response of BillingApi->webhook:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BillingApi->webhook: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **stripe_signature** | **str**|  | [optional] 

### Return type

[**StripeWebhookResponse**](StripeWebhookResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

