# lilypad.FunctionsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**deployed_function_by_names**](FunctionsApi.md#deployed_function_by_names) | **GET** /projects/{project_uuid}/functions/name/{function_name}/environments | Get Deployed Function By Names
[**function**](FunctionsApi.md#function) | **GET** /projects/{project_uuid}/functions/{function_uuid} | Get Function
[**function_0**](FunctionsApi.md#function_0) | **DELETE** /projects/{project_uuid}/functions/{function_uuid} | Archive Function
[**function_1**](FunctionsApi.md#function_1) | **PATCH** /projects/{project_uuid}/functions/{function_uuid} | Update Function
[**function_by_hash**](FunctionsApi.md#function_by_hash) | **GET** /projects/{project_uuid}/functions/hash/{function_hash} | Get Function By Hash
[**function_by_version**](FunctionsApi.md#function_by_version) | **GET** /projects/{project_uuid}/functions/name/{function_name}/version/{version_num} | Get Function By Version
[**functions**](FunctionsApi.md#functions) | **GET** /projects/{project_uuid}/functions | Get Functions
[**functions_by_name**](FunctionsApi.md#functions_by_name) | **GET** /projects/{project_uuid}/functions/name/{function_name} | Get Functions By Name
[**functions_by_name_0**](FunctionsApi.md#functions_by_name_0) | **DELETE** /projects/{project_uuid}/functions/names/{function_name} | Archive Functions By Name
[**latest_version_unique_function_names**](FunctionsApi.md#latest_version_unique_function_names) | **GET** /projects/{project_uuid}/functions/metadata/names/versions | Get Latest Version Unique Function Names
[**new_function**](FunctionsApi.md#new_function) | **POST** /projects/{project_uuid}/functions | Create New Function
[**playground**](FunctionsApi.md#playground) | **POST** /ee/projects/{project_uuid}/functions/{function_uuid}/playground | Run Function in Playground
[**unique_function_names**](FunctionsApi.md#unique_function_names) | **GET** /projects/{project_uuid}/functions/metadata/names | Get Unique Function Names
[**versioned_function**](FunctionsApi.md#versioned_function) | **POST** /projects/{project_uuid}/versioned-functions | Create Versioned Function


# **deployed_function_by_names**
> FunctionPublic deployed_function_by_names(project_uuid, function_name)

Get Deployed Function By Names

Get the deployed function by function name and environment name.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_name = 'function_name_example' # str | 

    try:
        # Get Deployed Function By Names
        api_response = api_instance.deployed_function_by_names(project_uuid, function_name)
        print("The response of FunctionsApi->deployed_function_by_names:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->deployed_function_by_names: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_name** | **str**|  | 

### Return type

[**FunctionPublic**](FunctionPublic.md)

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

# **function**
> FunctionPublic function(project_uuid, function_uuid)

Get Function

Grab function by UUID.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 

    try:
        # Get Function
        api_response = api_instance.function(project_uuid, function_uuid)
        print("The response of FunctionsApi->function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 

### Return type

[**FunctionPublic**](FunctionPublic.md)

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

# **function_0**
> bool function_0(project_uuid, function_uuid)

Archive Function

Archive a function and delete spans by function UUID.

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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 

    try:
        # Archive Function
        api_response = api_instance.function_0(project_uuid, function_uuid)
        print("The response of FunctionsApi->function_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->function_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 

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

# **function_1**
> FunctionPublic function_1(project_uuid, function_uuid, body)

Update Function

Update a function.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 
    body = None # object | 

    try:
        # Update Function
        api_response = api_instance.function_1(project_uuid, function_uuid, body)
        print("The response of FunctionsApi->function_1:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->function_1: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 
 **body** | **object**|  | 

### Return type

[**FunctionPublic**](FunctionPublic.md)

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

# **function_by_hash**
> FunctionPublic function_by_hash(project_uuid, function_hash)

Get Function By Hash

Get function by hash.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_hash = 'function_hash_example' # str | 

    try:
        # Get Function By Hash
        api_response = api_instance.function_by_hash(project_uuid, function_hash)
        print("The response of FunctionsApi->function_by_hash:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->function_by_hash: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_hash** | **str**|  | 

### Return type

[**FunctionPublic**](FunctionPublic.md)

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

# **function_by_version**
> FunctionPublic function_by_version(project_uuid, function_name, version_num)

Get Function By Version

Get function by name.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_name = 'function_name_example' # str | 
    version_num = 56 # int | 

    try:
        # Get Function By Version
        api_response = api_instance.function_by_version(project_uuid, function_name, version_num)
        print("The response of FunctionsApi->function_by_version:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->function_by_version: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_name** | **str**|  | 
 **version_num** | **int**|  | 

### Return type

[**FunctionPublic**](FunctionPublic.md)

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

# **functions**
> List[FunctionPublic] functions(project_uuid)

Get Functions

Grab all functions.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 

    try:
        # Get Functions
        api_response = api_instance.functions(project_uuid)
        print("The response of FunctionsApi->functions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->functions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 

### Return type

[**List[FunctionPublic]**](FunctionPublic.md)

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

# **functions_by_name**
> List[FunctionPublic] functions_by_name(project_uuid, function_name)

Get Functions By Name

Get function by name.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_name = 'function_name_example' # str | 

    try:
        # Get Functions By Name
        api_response = api_instance.functions_by_name(project_uuid, function_name)
        print("The response of FunctionsApi->functions_by_name:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->functions_by_name: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_name** | **str**|  | 

### Return type

[**List[FunctionPublic]**](FunctionPublic.md)

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

# **functions_by_name_0**
> bool functions_by_name_0(project_uuid, function_name)

Archive Functions By Name

Archive a function by name and delete spans by function name.

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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_name = 'function_name_example' # str | 

    try:
        # Archive Functions By Name
        api_response = api_instance.functions_by_name_0(project_uuid, function_name)
        print("The response of FunctionsApi->functions_by_name_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->functions_by_name_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_name** | **str**|  | 

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

# **latest_version_unique_function_names**
> List[FunctionPublic] latest_version_unique_function_names(project_uuid)

Get Latest Version Unique Function Names

Get all unique function names.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 

    try:
        # Get Latest Version Unique Function Names
        api_response = api_instance.latest_version_unique_function_names(project_uuid)
        print("The response of FunctionsApi->latest_version_unique_function_names:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->latest_version_unique_function_names: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 

### Return type

[**List[FunctionPublic]**](FunctionPublic.md)

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

# **new_function**
> FunctionPublic new_function(project_uuid, function_create)

Create New Function

Create a new function version.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_create import FunctionCreate
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_create = lilypad.FunctionCreate() # FunctionCreate | 

    try:
        # Create New Function
        api_response = api_instance.new_function(project_uuid, function_create)
        print("The response of FunctionsApi->new_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->new_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_create** | [**FunctionCreate**](FunctionCreate.md)|  | 

### Return type

[**FunctionPublic**](FunctionPublic.md)

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

# **playground**
> PlaygroundSuccessResponse playground(project_uuid, function_uuid, playground_parameters)

Run Function in Playground

Executes a function with specified parameters in a secure playground environment.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.playground_parameters import PlaygroundParameters
from lilypad.models.playground_success_response import PlaygroundSuccessResponse
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 
    playground_parameters = lilypad.PlaygroundParameters() # PlaygroundParameters | 

    try:
        # Run Function in Playground
        api_response = api_instance.playground(project_uuid, function_uuid, playground_parameters)
        print("The response of FunctionsApi->playground:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->playground: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 
 **playground_parameters** | [**PlaygroundParameters**](PlaygroundParameters.md)|  | 

### Return type

[**PlaygroundSuccessResponse**](PlaygroundSuccessResponse.md)

### Authorization

[APIKeyHeader](../README.md#APIKeyHeader), [OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Function executed successfully. |  -  |
**400** | Bad Request |  -  |
**404** | Function not found |  -  |
**408** | Request Timeout |  -  |
**500** | Internal Server Error |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **unique_function_names**
> List[Optional[str]] unique_function_names(project_uuid)

Get Unique Function Names

Get all unique function names.

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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 

    try:
        # Get Unique Function Names
        api_response = api_instance.unique_function_names(project_uuid)
        print("The response of FunctionsApi->unique_function_names:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->unique_function_names: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 

### Return type

**List[Optional[str]]**

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

# **versioned_function**
> FunctionPublic versioned_function(project_uuid, function_create)

Create Versioned Function

Create a managed function.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.function_create import FunctionCreate
from lilypad.models.function_public import FunctionPublic
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
    api_instance = lilypad.FunctionsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_create = lilypad.FunctionCreate() # FunctionCreate | 

    try:
        # Create Versioned Function
        api_response = api_instance.versioned_function(project_uuid, function_create)
        print("The response of FunctionsApi->versioned_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling FunctionsApi->versioned_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_create** | [**FunctionCreate**](FunctionCreate.md)|  | 

### Return type

[**FunctionPublic**](FunctionPublic.md)

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

