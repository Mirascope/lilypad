# lilypad.AnnotationsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**annotation**](AnnotationsApi.md#annotation) | **DELETE** /ee/projects/{project_uuid}/annotations/{annotation_uuid} | Delete Annotation
[**annotation_0**](AnnotationsApi.md#annotation_0) | **PATCH** /ee/projects/{project_uuid}/annotations/{annotation_uuid} | Update Annotation
[**annotation_1**](AnnotationsApi.md#annotation_1) | **GET** /ee/projects/{project_uuid}/spans/{span_uuid}/generate-annotation | Generate Annotation
[**annotation_metrics_by_function**](AnnotationsApi.md#annotation_metrics_by_function) | **GET** /ee/projects/{project_uuid}/functions/{function_uuid}/annotations/metrics | Get Annotation Metrics By Function
[**annotations**](AnnotationsApi.md#annotations) | **POST** /ee/projects/{project_uuid}/annotations | Create Annotations
[**annotations_by_functions**](AnnotationsApi.md#annotations_by_functions) | **GET** /ee/projects/{project_uuid}/functions/{function_uuid}/annotations | Get Annotations By Functions
[**annotations_by_project**](AnnotationsApi.md#annotations_by_project) | **GET** /ee/projects/{project_uuid}/annotations | Get Annotations By Project
[**annotations_by_spans**](AnnotationsApi.md#annotations_by_spans) | **GET** /ee/projects/{project_uuid}/spans/{span_uuid}/annotations | Get Annotations By Spans


# **annotation**
> bool annotation(annotation_uuid, project_uuid)

Delete Annotation

Delete an annotation.

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
    api_instance = lilypad.AnnotationsApi(api_client)
    annotation_uuid = 'annotation_uuid_example' # str | 
    project_uuid = 'project_uuid_example' # str | 

    try:
        # Delete Annotation
        api_response = api_instance.annotation(annotation_uuid, project_uuid)
        print("The response of AnnotationsApi->annotation:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotation: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **annotation_uuid** | **str**|  | 
 **project_uuid** | **str**|  | 

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

# **annotation_0**
> AnnotationPublic annotation_0(annotation_uuid, project_uuid, annotation_update)

Update Annotation

Update an annotation.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.annotation_public import AnnotationPublic
from lilypad.models.annotation_update import AnnotationUpdate
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
    api_instance = lilypad.AnnotationsApi(api_client)
    annotation_uuid = 'annotation_uuid_example' # str | 
    project_uuid = 'project_uuid_example' # str | 
    annotation_update = lilypad.AnnotationUpdate() # AnnotationUpdate | 

    try:
        # Update Annotation
        api_response = api_instance.annotation_0(annotation_uuid, project_uuid, annotation_update)
        print("The response of AnnotationsApi->annotation_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotation_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **annotation_uuid** | **str**|  | 
 **project_uuid** | **str**|  | 
 **annotation_update** | [**AnnotationUpdate**](AnnotationUpdate.md)|  | 

### Return type

[**AnnotationPublic**](AnnotationPublic.md)

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

# **annotation_1**
> object annotation_1(span_uuid, project_uuid)

Generate Annotation

Stream function.

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
    api_instance = lilypad.AnnotationsApi(api_client)
    span_uuid = 'span_uuid_example' # str | 
    project_uuid = 'project_uuid_example' # str | 

    try:
        # Generate Annotation
        api_response = api_instance.annotation_1(span_uuid, project_uuid)
        print("The response of AnnotationsApi->annotation_1:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotation_1: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **span_uuid** | **str**|  | 
 **project_uuid** | **str**|  | 

### Return type

**object**

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

# **annotation_metrics_by_function**
> AnnotationMetrics annotation_metrics_by_function(function_uuid, project_uuid)

Get Annotation Metrics By Function

Get annotation metrics by function.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.annotation_metrics import AnnotationMetrics
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
    api_instance = lilypad.AnnotationsApi(api_client)
    function_uuid = 'function_uuid_example' # str | 
    project_uuid = 'project_uuid_example' # str | 

    try:
        # Get Annotation Metrics By Function
        api_response = api_instance.annotation_metrics_by_function(function_uuid, project_uuid)
        print("The response of AnnotationsApi->annotation_metrics_by_function:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotation_metrics_by_function: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **function_uuid** | **str**|  | 
 **project_uuid** | **str**|  | 

### Return type

[**AnnotationMetrics**](AnnotationMetrics.md)

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

# **annotations**
> List[AnnotationPublic] annotations(project_uuid, annotation_create)

Create Annotations

Create an annotation.

Args:
    project_uuid: The project UUID.
    annotations_service: The annotation service.
    project_service: The project service.
    annotations_create: The annotation create model.

Returns:
    AnnotationPublic: The created annotation.

Raises:
    HTTPException: If the span has already been assigned to a user and has
    not been labeled yet.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.annotation_create import AnnotationCreate
from lilypad.models.annotation_public import AnnotationPublic
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
    api_instance = lilypad.AnnotationsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    annotation_create = [lilypad.AnnotationCreate()] # List[AnnotationCreate] | 

    try:
        # Create Annotations
        api_response = api_instance.annotations(project_uuid, annotation_create)
        print("The response of AnnotationsApi->annotations:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotations: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **annotation_create** | [**List[AnnotationCreate]**](AnnotationCreate.md)|  | 

### Return type

[**List[AnnotationPublic]**](AnnotationPublic.md)

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

# **annotations_by_functions**
> List[AnnotationPublic] annotations_by_functions(project_uuid, function_uuid)

Get Annotations By Functions

Get annotations by functions.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.annotation_public import AnnotationPublic
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
    api_instance = lilypad.AnnotationsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 

    try:
        # Get Annotations By Functions
        api_response = api_instance.annotations_by_functions(project_uuid, function_uuid)
        print("The response of AnnotationsApi->annotations_by_functions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotations_by_functions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 

### Return type

[**List[AnnotationPublic]**](AnnotationPublic.md)

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

# **annotations_by_project**
> List[AnnotationPublic] annotations_by_project(project_uuid)

Get Annotations By Project

Get annotations by project.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.annotation_public import AnnotationPublic
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
    api_instance = lilypad.AnnotationsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 

    try:
        # Get Annotations By Project
        api_response = api_instance.annotations_by_project(project_uuid)
        print("The response of AnnotationsApi->annotations_by_project:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotations_by_project: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 

### Return type

[**List[AnnotationPublic]**](AnnotationPublic.md)

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

# **annotations_by_spans**
> List[AnnotationPublic] annotations_by_spans(project_uuid, span_uuid)

Get Annotations By Spans

Get annotations by functions.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.annotation_public import AnnotationPublic
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
    api_instance = lilypad.AnnotationsApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    span_uuid = 'span_uuid_example' # str | 

    try:
        # Get Annotations By Spans
        api_response = api_instance.annotations_by_spans(project_uuid, span_uuid)
        print("The response of AnnotationsApi->annotations_by_spans:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnnotationsApi->annotations_by_spans: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **span_uuid** | **str**|  | 

### Return type

[**List[AnnotationPublic]**](AnnotationPublic.md)

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

