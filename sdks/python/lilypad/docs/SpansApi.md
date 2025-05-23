# lilypad.SpansApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**aggregates_by_function_uuid**](SpansApi.md#aggregates_by_function_uuid) | **GET** /projects/{project_uuid}/functions/{function_uuid}/spans/metadata | Get Aggregates By Function Uuid
[**aggregates_by_project_uuid**](SpansApi.md#aggregates_by_project_uuid) | **GET** /projects/{project_uuid}/spans/metadata | Get Aggregates By Project Uuid
[**span**](SpansApi.md#span) | **GET** /spans/{span_uuid} | Get Span
[**span_0**](SpansApi.md#span_0) | **PATCH** /spans/{span_uuid} | Update Span
[**span_by_span_id**](SpansApi.md#span_by_span_id) | **GET** /projects/{project_uuid}/spans/{span_id} | Get Span By Span Id
[**spans**](SpansApi.md#spans) | **DELETE** /projects/{project_uuid}/spans/{span_uuid} | Delete Spans
[**spans_by_function_uuid_paginated**](SpansApi.md#spans_by_function_uuid_paginated) | **GET** /projects/{project_uuid}/functions/{function_uuid}/spans/paginated | Get Spans By Function Uuid Paginated
[**traces**](SpansApi.md#traces) | **GET** /projects/{project_uuid}/spans | Search Traces


# **aggregates_by_function_uuid**
> List[AggregateMetrics] aggregates_by_function_uuid(project_uuid, function_uuid, time_frame)

Get Aggregates By Function Uuid

Get aggregated span by function uuid.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.aggregate_metrics import AggregateMetrics
from lilypad.models.time_frame import TimeFrame
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
    api_instance = lilypad.SpansApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 
    time_frame = lilypad.TimeFrame() # TimeFrame | 

    try:
        # Get Aggregates By Function Uuid
        api_response = api_instance.aggregates_by_function_uuid(project_uuid, function_uuid, time_frame)
        print("The response of SpansApi->aggregates_by_function_uuid:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->aggregates_by_function_uuid: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 
 **time_frame** | [**TimeFrame**](.md)|  | 

### Return type

[**List[AggregateMetrics]**](AggregateMetrics.md)

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

# **aggregates_by_project_uuid**
> List[AggregateMetrics] aggregates_by_project_uuid(project_uuid, time_frame)

Get Aggregates By Project Uuid

Get aggregated span by project uuid.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.aggregate_metrics import AggregateMetrics
from lilypad.models.time_frame import TimeFrame
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
    api_instance = lilypad.SpansApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    time_frame = lilypad.TimeFrame() # TimeFrame | 

    try:
        # Get Aggregates By Project Uuid
        api_response = api_instance.aggregates_by_project_uuid(project_uuid, time_frame)
        print("The response of SpansApi->aggregates_by_project_uuid:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->aggregates_by_project_uuid: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **time_frame** | [**TimeFrame**](.md)|  | 

### Return type

[**List[AggregateMetrics]**](AggregateMetrics.md)

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

# **span**
> SpanMoreDetails span(span_uuid)

Get Span

Get span by uuid.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.span_more_details import SpanMoreDetails
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
    api_instance = lilypad.SpansApi(api_client)
    span_uuid = 'span_uuid_example' # str | 

    try:
        # Get Span
        api_response = api_instance.span(span_uuid)
        print("The response of SpansApi->span:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->span: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **span_uuid** | **str**|  | 

### Return type

[**SpanMoreDetails**](SpanMoreDetails.md)

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

# **span_0**
> SpanMoreDetails span_0(span_uuid, span_update)

Update Span

Update span by uuid.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.span_more_details import SpanMoreDetails
from lilypad.models.span_update import SpanUpdate
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
    api_instance = lilypad.SpansApi(api_client)
    span_uuid = 'span_uuid_example' # str | 
    span_update = lilypad.SpanUpdate() # SpanUpdate | 

    try:
        # Update Span
        api_response = api_instance.span_0(span_uuid, span_update)
        print("The response of SpansApi->span_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->span_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **span_uuid** | **str**|  | 
 **span_update** | [**SpanUpdate**](SpanUpdate.md)|  | 

### Return type

[**SpanMoreDetails**](SpanMoreDetails.md)

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

# **span_by_span_id**
> SpanMoreDetails span_by_span_id(project_uuid, span_id)

Get Span By Span Id

Get span by project_uuid and span_id.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.span_more_details import SpanMoreDetails
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
    api_instance = lilypad.SpansApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    span_id = 'span_id_example' # str | 

    try:
        # Get Span By Span Id
        api_response = api_instance.span_by_span_id(project_uuid, span_id)
        print("The response of SpansApi->span_by_span_id:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->span_by_span_id: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **span_id** | **str**|  | 

### Return type

[**SpanMoreDetails**](SpanMoreDetails.md)

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

# **spans**
> bool spans(project_uuid, span_uuid)

Delete Spans

Delete spans by UUID.

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
    api_instance = lilypad.SpansApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    span_uuid = 'span_uuid_example' # str | 

    try:
        # Delete Spans
        api_response = api_instance.spans(project_uuid, span_uuid)
        print("The response of SpansApi->spans:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->spans: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **span_uuid** | **str**|  | 

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

# **spans_by_function_uuid_paginated**
> PaginatedSpanPublic spans_by_function_uuid_paginated(project_uuid, function_uuid, limit=limit, offset=offset, order=order)

Get Spans By Function Uuid Paginated

Get spans for a function with pagination (new, non-breaking).

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.paginated_span_public import PaginatedSpanPublic
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
    api_instance = lilypad.SpansApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    function_uuid = 'function_uuid_example' # str | 
    limit = 50 # int |  (optional) (default to 50)
    offset = 0 # int |  (optional) (default to 0)
    order = desc # str |  (optional) (default to desc)

    try:
        # Get Spans By Function Uuid Paginated
        api_response = api_instance.spans_by_function_uuid_paginated(project_uuid, function_uuid, limit=limit, offset=offset, order=order)
        print("The response of SpansApi->spans_by_function_uuid_paginated:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->spans_by_function_uuid_paginated: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **function_uuid** | **str**|  | 
 **limit** | **int**|  | [optional] [default to 50]
 **offset** | **int**|  | [optional] [default to 0]
 **order** | **str**|  | [optional] [default to desc]

### Return type

[**PaginatedSpanPublic**](PaginatedSpanPublic.md)

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

# **traces**
> List[SpanPublic] traces(project_uuid, query_string=query_string, time_range_start=time_range_start, time_range_end=time_range_end, limit=limit, scope=scope, type=type)

Search Traces

Search for traces in OpenSearch.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.scope import Scope
from lilypad.models.span_public import SpanPublic
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
    api_instance = lilypad.SpansApi(api_client)
    project_uuid = 'project_uuid_example' # str | 
    query_string = 'query_string_example' # str |  (optional)
    time_range_start = 56 # int |  (optional)
    time_range_end = 56 # int |  (optional)
    limit = 100 # int |  (optional) (default to 100)
    scope = lilypad.Scope() # Scope |  (optional)
    type = 'type_example' # str |  (optional)

    try:
        # Search Traces
        api_response = api_instance.traces(project_uuid, query_string=query_string, time_range_start=time_range_start, time_range_end=time_range_end, limit=limit, scope=scope, type=type)
        print("The response of SpansApi->traces:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpansApi->traces: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_uuid** | **str**|  | 
 **query_string** | **str**|  | [optional] 
 **time_range_start** | **int**|  | [optional] 
 **time_range_end** | **int**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 100]
 **scope** | [**Scope**](.md)|  | [optional] 
 **type** | **str**|  | [optional] 

### Return type

[**List[SpanPublic]**](SpanPublic.md)

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

