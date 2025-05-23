# lilypad.ExternalAPIKeysApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**external_api_key**](ExternalAPIKeysApi.md#external_api_key) | **POST** /external-api-keys | Store External Api Key
[**external_api_key_0**](ExternalAPIKeysApi.md#external_api_key_0) | **GET** /external-api-keys/{service_name} | Get External Api Key
[**external_api_key_1**](ExternalAPIKeysApi.md#external_api_key_1) | **DELETE** /external-api-keys/{service_name} | Delete External Api Key
[**external_api_key_2**](ExternalAPIKeysApi.md#external_api_key_2) | **PATCH** /external-api-keys/{service_name} | Update External Api Key
[**external_api_keys**](ExternalAPIKeysApi.md#external_api_keys) | **GET** /external-api-keys | List External Api Keys


# **external_api_key**
> ExternalAPIKeyPublic external_api_key(external_api_key_create)

Store External Api Key

Store an external API key for a given service.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.external_api_key_create import ExternalAPIKeyCreate
from lilypad.models.external_api_key_public import ExternalAPIKeyPublic
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
    api_instance = lilypad.ExternalAPIKeysApi(api_client)
    external_api_key_create = lilypad.ExternalAPIKeyCreate() # ExternalAPIKeyCreate | 

    try:
        # Store External Api Key
        api_response = api_instance.external_api_key(external_api_key_create)
        print("The response of ExternalAPIKeysApi->external_api_key:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalAPIKeysApi->external_api_key: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **external_api_key_create** | [**ExternalAPIKeyCreate**](ExternalAPIKeyCreate.md)|  | 

### Return type

[**ExternalAPIKeyPublic**](ExternalAPIKeyPublic.md)

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

# **external_api_key_0**
> ExternalAPIKeyPublic external_api_key_0(service_name)

Get External Api Key

Retrieve an external API key for a given service.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.external_api_key_public import ExternalAPIKeyPublic
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
    api_instance = lilypad.ExternalAPIKeysApi(api_client)
    service_name = 'service_name_example' # str | 

    try:
        # Get External Api Key
        api_response = api_instance.external_api_key_0(service_name)
        print("The response of ExternalAPIKeysApi->external_api_key_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalAPIKeysApi->external_api_key_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **service_name** | **str**|  | 

### Return type

[**ExternalAPIKeyPublic**](ExternalAPIKeyPublic.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader), [OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **external_api_key_1**
> bool external_api_key_1(service_name)

Delete External Api Key

Delete an external API key for a given service.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
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
    api_instance = lilypad.ExternalAPIKeysApi(api_client)
    service_name = 'service_name_example' # str | 

    try:
        # Delete External Api Key
        api_response = api_instance.external_api_key_1(service_name)
        print("The response of ExternalAPIKeysApi->external_api_key_1:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalAPIKeysApi->external_api_key_1: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **service_name** | **str**|  | 

### Return type

**bool**

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader), [OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **external_api_key_2**
> ExternalAPIKeyPublic external_api_key_2(service_name, external_api_key_update)

Update External Api Key

Update users keys.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.external_api_key_public import ExternalAPIKeyPublic
from lilypad.models.external_api_key_update import ExternalAPIKeyUpdate
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
    api_instance = lilypad.ExternalAPIKeysApi(api_client)
    service_name = 'service_name_example' # str | 
    external_api_key_update = lilypad.ExternalAPIKeyUpdate() # ExternalAPIKeyUpdate | 

    try:
        # Update External Api Key
        api_response = api_instance.external_api_key_2(service_name, external_api_key_update)
        print("The response of ExternalAPIKeysApi->external_api_key_2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalAPIKeysApi->external_api_key_2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **service_name** | **str**|  | 
 **external_api_key_update** | [**ExternalAPIKeyUpdate**](ExternalAPIKeyUpdate.md)|  | 

### Return type

[**ExternalAPIKeyPublic**](ExternalAPIKeyPublic.md)

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

# **external_api_keys**
> List[ExternalAPIKeyPublic] external_api_keys()

List External Api Keys

List all external API keys for the user with masked values.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.external_api_key_public import ExternalAPIKeyPublic
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
    api_instance = lilypad.ExternalAPIKeysApi(api_client)

    try:
        # List External Api Keys
        api_response = api_instance.external_api_keys()
        print("The response of ExternalAPIKeysApi->external_api_keys:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExternalAPIKeysApi->external_api_keys: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[ExternalAPIKeyPublic]**](ExternalAPIKeyPublic.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader), [OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

