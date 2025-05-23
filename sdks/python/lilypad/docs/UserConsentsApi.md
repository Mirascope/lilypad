# lilypad.UserConsentsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**user_consent**](UserConsentsApi.md#user_consent) | **POST** /user-consents | Post User Consent
[**user_consent_0**](UserConsentsApi.md#user_consent_0) | **PATCH** /user-consents/{user_consent_uuid} | Update User Consent


# **user_consent**
> UserConsentPublic user_consent(user_consent_create)

Post User Consent

Store user consent.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.user_consent_create import UserConsentCreate
from lilypad.models.user_consent_public import UserConsentPublic
from lilypad.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = lilypad.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with lilypad.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = lilypad.UserConsentsApi(api_client)
    user_consent_create = lilypad.UserConsentCreate() # UserConsentCreate | 

    try:
        # Post User Consent
        api_response = api_instance.user_consent(user_consent_create)
        print("The response of UserConsentsApi->user_consent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UserConsentsApi->user_consent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_consent_create** | [**UserConsentCreate**](UserConsentCreate.md)|  | 

### Return type

[**UserConsentPublic**](UserConsentPublic.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader), [OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **user_consent_0**
> UserConsentPublic user_consent_0(user_consent_uuid, user_consent_update)

Update User Consent

Update user consent.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.user_consent_public import UserConsentPublic
from lilypad.models.user_consent_update import UserConsentUpdate
from lilypad.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = lilypad.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKeyHeader
configuration.api_key['APIKeyHeader'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKeyHeader'] = 'Bearer'

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with lilypad.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = lilypad.UserConsentsApi(api_client)
    user_consent_uuid = 'user_consent_uuid_example' # str | 
    user_consent_update = lilypad.UserConsentUpdate() # UserConsentUpdate | 

    try:
        # Update User Consent
        api_response = api_instance.user_consent_0(user_consent_uuid, user_consent_update)
        print("The response of UserConsentsApi->user_consent_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UserConsentsApi->user_consent_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_consent_uuid** | **str**|  | 
 **user_consent_update** | [**UserConsentUpdate**](UserConsentUpdate.md)|  | 

### Return type

[**UserConsentPublic**](UserConsentPublic.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader), [OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

