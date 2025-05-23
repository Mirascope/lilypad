# lilypad.GitHubApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**callback**](GitHubApi.md#callback) | **GET** /auth/github/callback | Github Callback


# **callback**
> UserPublic callback(code)

Github Callback

Callback for GitHub OAuth.

Saves the user and organization or retrieves the user after authenticating
with GitHub.

### Example


```python
import lilypad
from lilypad.models.user_public import UserPublic
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
    api_instance = lilypad.GitHubApi(api_client)
    code = 'code_example' # str | 

    try:
        # Github Callback
        api_response = api_instance.callback(code)
        print("The response of GitHubApi->callback:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GitHubApi->callback: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **code** | **str**|  | 

### Return type

[**UserPublic**](UserPublic.md)

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

