# lilypad.SettingsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**settings_client**](SettingsApi.md#settings_client) | **GET** /settings | Get Settings Client


# **settings_client**
> SettingsPublic settings_client()

Get Settings Client

Get the configuration.

### Example


```python
import lilypad
from lilypad.models.settings_public import SettingsPublic
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
    api_instance = lilypad.SettingsApi(api_client)

    try:
        # Get Settings Client
        api_response = api_instance.settings_client()
        print("The response of SettingsApi->settings_client:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SettingsApi->settings_client: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**SettingsPublic**](SettingsPublic.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

