# lilypad.EnvironmentsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**active_deployment**](EnvironmentsApi.md#active_deployment) | **GET** /projects/{project_uuid}/environments/{environment_uuid}/deployment | Get Active Deployment
[**deployment_history**](EnvironmentsApi.md#deployment_history) | **GET** /projects/{project_uuid}/environments/{environment_uuid}/history | Get Deployment History
[**environment**](EnvironmentsApi.md#environment) | **POST** /environments | Create Environment
[**environment_0**](EnvironmentsApi.md#environment_0) | **GET** /environments/{environment_uuid} | Get Environment
[**environment_1**](EnvironmentsApi.md#environment_1) | **DELETE** /environments/{environment_uuid} | Delete Environment
[**environment_function**](EnvironmentsApi.md#environment_function) | **GET** /projects/{project_uuid}/environments/{environment_uuid}/function | Get Environment Function
[**environments**](EnvironmentsApi.md#environments) | **GET** /environments | Get Environments
[**function**](EnvironmentsApi.md#function) | **POST** /projects/{project_uuid}/environments/{environment_uuid}/deploy | Deploy Function


# **active_deployment**
> DeploymentPublic active_deployment(project_uuid, environment_uuid)

Get Active Deployment

Get active deployment for an environment.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.deployment_public import DeploymentPublic
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
    api_instance = lilypad.EnvironmentsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    environment_uuid = 'environment_uuid_example' # str | 

    try:
        # Get Active Deployment
        api_response = api_instance.active_deployment(project_uuid, environment_uuid)
        print("The response of EnvironmentsApi->active_deployment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->active_deployment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **environment_uuid** | **str**|  | 

### Return type

[**DeploymentPublic**](DeploymentPublic.md)

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

# **deployment_history**
> List[DeploymentPublic] deployment_history(project_uuid, environment_uuid)

Get Deployment History

Get deployment history for an environment.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.deployment_public import DeploymentPublic
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
    api_instance = lilypad.EnvironmentsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    environment_uuid = 'environment_uuid_example' # str | 

    try:
        # Get Deployment History
        api_response = api_instance.deployment_history(project_uuid, environment_uuid)
        print("The response of EnvironmentsApi->deployment_history:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->deployment_history: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **environment_uuid** | **str**|  | 

### Return type

[**List[DeploymentPublic]**](DeploymentPublic.md)

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

# **environment**
> EnvironmentPublic environment(environment_create)

Create Environment

Create a new environment.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.environment_create import EnvironmentCreate
from lilypad.models.environment_public import EnvironmentPublic
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
    api_instance = lilypad.EnvironmentsApi(api_client)
    environment_create = lilypad.EnvironmentCreate() # EnvironmentCreate | 

    try:
        # Create Environment
        api_response = api_instance.environment(environment_create)
        print("The response of EnvironmentsApi->environment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->environment: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **environment_create** | [**EnvironmentCreate**](EnvironmentCreate.md)|  | 

### Return type

[**EnvironmentPublic**](EnvironmentPublic.md)

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

# **environment_0**
> EnvironmentPublic environment_0(environment_uuid)

Get Environment

Get environment by UUID.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.environment_public import EnvironmentPublic
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
    api_instance = lilypad.EnvironmentsApi(api_client)
    environment_uuid = 'environment_uuid_example' # str | 

    try:
        # Get Environment
        api_response = api_instance.environment_0(environment_uuid)
        print("The response of EnvironmentsApi->environment_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->environment_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **environment_uuid** | **str**|  | 

### Return type

[**EnvironmentPublic**](EnvironmentPublic.md)

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

# **environment_1**
> bool environment_1(environment_uuid)

Delete Environment

Delete an environment.

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
    api_instance = lilypad.EnvironmentsApi(api_client)
    environment_uuid = 'environment_uuid_example' # str | 

    try:
        # Delete Environment
        api_response = api_instance.environment_1(environment_uuid)
        print("The response of EnvironmentsApi->environment_1:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->environment_1: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **environment_uuid** | **str**|  | 

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

# **environment_function**
> FunctionPublic environment_function(project_uuid, environment_uuid)

Get Environment Function

Get the currently active function for an environment.

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
    api_instance = lilypad.EnvironmentsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    environment_uuid = 'environment_uuid_example' # str | 

    try:
        # Get Environment Function
        api_response = api_instance.environment_function(project_uuid, environment_uuid)
        print("The response of EnvironmentsApi->environment_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->environment_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **environment_uuid** | **str**|  | 

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

# **environments**
> List[EnvironmentPublic] environments()

Get Environments

Get all environments for a project.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.environment_public import EnvironmentPublic
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
    api_instance = lilypad.EnvironmentsApi(api_client)

    try:
        # Get Environments
        api_response = api_instance.environments()
        print("The response of EnvironmentsApi->environments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->environments: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[EnvironmentPublic]**](EnvironmentPublic.md)

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

# **function**
> DeploymentPublic function(project_uuid, environment_uuid, function_uuid, notes=notes)

Deploy Function

Deploy a function to an environment.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.deployment_public import DeploymentPublic
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
    api_instance = lilypad.EnvironmentsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    environment_uuid = 'environment_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 
    notes = 'notes_example' # str |  (optional)

    try:
        # Deploy Function
        api_response = api_instance.function(project_uuid, environment_uuid, function_uuid, notes=notes)
        print("The response of EnvironmentsApi->function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnvironmentsApi->function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **environment_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 
 **notes** | **str**|  | [optional] 

### Return type

[**DeploymentPublic**](DeploymentPublic.md)

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

