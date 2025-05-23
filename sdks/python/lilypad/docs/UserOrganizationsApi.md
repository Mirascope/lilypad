# lilypad.UserOrganizationsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**user_organization**](UserOrganizationsApi.md#user_organization) | **POST** /ee/user-organizations | Create User Organization
[**user_organization_0**](UserOrganizationsApi.md#user_organization_0) | **PATCH** /ee/user-organizations/{user_organization_uuid} | Update User Organization
[**user_organizations**](UserOrganizationsApi.md#user_organizations) | **GET** /ee/user-organizations | Get User Organizations
[**user_organizations_0**](UserOrganizationsApi.md#user_organizations_0) | **DELETE** /ee/user-organizations/{user_organization_uuid} | Delete User Organizations
[**users_by_organization**](UserOrganizationsApi.md#users_by_organization) | **GET** /ee/user-organizations/users | Get Users By Organization


# **user_organization**
> UserPublic user_organization(create_user_organization_token)

Create User Organization

Create user organization

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.create_user_organization_token import CreateUserOrganizationToken
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
    api_instance = lilypad.UserOrganizationsApi(api_client)
    create_user_organization_token = lilypad.CreateUserOrganizationToken() # CreateUserOrganizationToken | 

    try:
        # Create User Organization
        api_response = api_instance.user_organization(create_user_organization_token)
        print("The response of UserOrganizationsApi->user_organization:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UserOrganizationsApi->user_organization: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_user_organization_token** | [**CreateUserOrganizationToken**](CreateUserOrganizationToken.md)|  | 

### Return type

[**UserPublic**](UserPublic.md)

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

# **user_organization_0**
> UserOrganizationTable user_organization_0(user_organization_uuid, user_organization_update)

Update User Organization

Updates user organization

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.user_organization_table import UserOrganizationTable
from lilypad.models.user_organization_update import UserOrganizationUpdate
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
    api_instance = lilypad.UserOrganizationsApi(api_client)
    user_organization_uuid = 'user_organization_uuid_example' # str | 
    user_organization_update = lilypad.UserOrganizationUpdate() # UserOrganizationUpdate | 

    try:
        # Update User Organization
        api_response = api_instance.user_organization_0(user_organization_uuid, user_organization_update)
        print("The response of UserOrganizationsApi->user_organization_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UserOrganizationsApi->user_organization_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_organization_uuid** | **str**|  | 
 **user_organization_update** | [**UserOrganizationUpdate**](UserOrganizationUpdate.md)|  | 

### Return type

[**UserOrganizationTable**](UserOrganizationTable.md)

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

# **user_organizations**
> List[UserOrganizationTable] user_organizations()

Get User Organizations

Get all user organizations.

### Example

* Api Key Authentication (APIKeyHeader):
* OAuth Authentication (OAuth2PasswordBearer):

```python
import lilypad
from lilypad.models.user_organization_table import UserOrganizationTable
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
    api_instance = lilypad.UserOrganizationsApi(api_client)

    try:
        # Get User Organizations
        api_response = api_instance.user_organizations()
        print("The response of UserOrganizationsApi->user_organizations:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UserOrganizationsApi->user_organizations: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[UserOrganizationTable]**](UserOrganizationTable.md)

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

# **user_organizations_0**
> bool user_organizations_0(user_organization_uuid)

Delete User Organizations

Delete user organization by uuid

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
    api_instance = lilypad.UserOrganizationsApi(api_client)
    user_organization_uuid = 'user_organization_uuid_example' # str | 

    try:
        # Delete User Organizations
        api_response = api_instance.user_organizations_0(user_organization_uuid)
        print("The response of UserOrganizationsApi->user_organizations_0:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UserOrganizationsApi->user_organizations_0: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_organization_uuid** | **str**|  | 

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

# **users_by_organization**
> List[UserPublic] users_by_organization()

Get Users By Organization

Get all users of an organization.

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
    api_instance = lilypad.UserOrganizationsApi(api_client)

    try:
        # Get Users By Organization
        api_response = api_instance.users_by_organization()
        print("The response of UserOrganizationsApi->users_by_organization:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UserOrganizationsApi->users_by_organization: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[UserPublic]**](UserPublic.md)

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

