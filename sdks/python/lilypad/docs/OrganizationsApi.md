# lilypad.OrganizationsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**license**](OrganizationsApi.md#license) | **GET** /ee/organizations/license | Get License
[**organization**](OrganizationsApi.md#organization) | **POST** /organizations | Create Organization
[**organization_0**](OrganizationsApi.md#organization_0) | **DELETE** /organizations | Delete Organization
[**organization_1**](OrganizationsApi.md#organization_1) | **PATCH** /organizations | Update Organization


# **license**
> LicenseInfo license()

Get License

Get the license information for the organization

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.license_info import LicenseInfo
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
    api_instance = lilypad.OrganizationsApi(api_client)

    try:
        # Get License
        api_response = api_instance.license()
        print("The response of OrganizationsApi->license:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OrganizationsApi->license: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**LicenseInfo**](LicenseInfo.md)

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

# **organization**
> OrganizationPublic organization(organization_create)

Create Organization

Create an organization.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.organization_create import OrganizationCreate
from lilypad.models.organization_public import OrganizationPublic
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
    api_instance = lilypad.OrganizationsApi(api_client)
    organization_create = lilypad.OrganizationCreate() # OrganizationCreate | 

    try:
        # Create Organization
        api_response = api_instance.organization(organization_create)
        print("The response of OrganizationsApi->organization:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OrganizationsApi->organization: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **organization_create** | [**OrganizationCreate**](OrganizationCreate.md)|  | 

### Return type

[**OrganizationPublic**](OrganizationPublic.md)

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

# **organization_0**
> UserPublic organization_0()

Delete Organization

Delete an organization.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

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
    api_instance = lilypad.OrganizationsApi(api_client)

    try:
        # Delete Organization
        api_response = api_instance.organization_0()
        print("The response of OrganizationsApi->organization_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OrganizationsApi->organization_0: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**UserPublic**](UserPublic.md)

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

# **organization_1**
> OrganizationPublic organization_1(organization_update)

Update Organization

Update an organization.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.organization_public import OrganizationPublic
from lilypad.models.organization_update import OrganizationUpdate
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
    api_instance = lilypad.OrganizationsApi(api_client)
    organization_update = lilypad.OrganizationUpdate() # OrganizationUpdate | 

    try:
        # Update Organization
        api_response = api_instance.organization_1(organization_update)
        print("The response of OrganizationsApi->organization_1:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OrganizationsApi->organization_1: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **organization_update** | [**OrganizationUpdate**](OrganizationUpdate.md)|  | 

### Return type

[**OrganizationPublic**](OrganizationPublic.md)

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

