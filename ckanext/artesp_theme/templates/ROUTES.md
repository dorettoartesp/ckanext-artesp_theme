# ARTESP CKAN Theme Extension Routes

This document provides a comprehensive overview of all URL routes used in the ARTESP CKAN theme extension, mapping each route to its corresponding template file.

## Table of Contents

1. [Home and Static Pages](#home-and-static-pages)
2. [Dataset Routes](#dataset-routes)
3. [Organization Routes](#organization-routes)
4. [Group Routes](#group-routes)
5. [User Routes](#user-routes)
6. [Admin Routes](#admin-routes)
7. [Custom ARTESP Routes](#custom-artesp-routes)

## Home and Static Pages

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/` | `home/index.html` | Homepage of the CKAN portal | `home.index` (CKAN core) |
| `/about` | `home/about.html` | About page for the portal | `home.about` (CKAN core) |
| `/about-ckan` | `static/about_ckan.html` | Information about CKAN software | `artesp_theme.about_ckan` |
| `/terms` | `static/terms.html` | Terms of use for the portal | `artesp_theme.terms` |
| `/privacy` | `static/privacy.html` | Privacy policy for the portal | `artesp_theme.privacy` |
| `/contact` | `static/contact.html` | Contact information page | `artesp_theme.contact` |

## Dataset Routes

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/dataset` | `package/search.html` | Dataset search page | `dataset.search` (CKAN core) |
| `/dataset/new` | `package/new.html` | Create new dataset form | `dataset.new` (CKAN core) |
| `/dataset/{id}` | `package/read.html` | View a specific dataset | `dataset.read` (CKAN core) |
| `/dataset/edit/{id}` | `package/edit.html` | Edit a specific dataset | `dataset.edit` (CKAN core) |
| `/dataset/delete/{id}` | `package/confirm_delete.html` | Confirm dataset deletion | `dataset.delete` (CKAN core) |
| `/dataset/resources/{id}` | `package/resources.html` | List resources for a dataset | `dataset.resources` (CKAN core) |
| `/dataset/groups/{id}` | `package/group_list.html` | List groups for a dataset | `dataset.groups` (CKAN core) |
| `/dataset/followers/{id}` | `package/followers.html` | List followers of a dataset | `dataset.followers` (CKAN core) |
| `/dataset/activity/{id}` | `package/activity.html` | Activity stream for a dataset | `dataset.activity` (CKAN core) |

### Resource Routes

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/dataset/new_resource/{id}` | `package/new_resource.html` | Add a new resource to a dataset | `dataset.new_resource` (CKAN core) |
| `/dataset/{dataset_id}/resource/{resource_id}` | `package/resource_read.html` | View a specific resource | `resource.read` (CKAN core) |
| `/dataset/{dataset_id}/resource_edit/{resource_id}` | `package/resource_edit.html` | Edit a specific resource | `resource.edit` (CKAN core) |
| `/dataset/{dataset_id}/resource_delete/{resource_id}` | `package/confirm_delete_resource.html` | Confirm resource deletion | `resource.delete` (CKAN core) |
| `/dataset/{dataset_id}/resource/{resource_id}/views` | `package/resource_views.html` | List views for a resource | `resource.views` (CKAN core) |
| `/dataset/{dataset_id}/resource/{resource_id}/view/{view_id}` | `package/resource_view.html` | View a specific resource view | `resource.view` (CKAN core) |

## Organization Routes

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/organization` | `organization/index.html` | List all organizations | `organization.index` (CKAN core) |
| `/organization/new` | `organization/new.html` | Create new organization form | `organization.new` (CKAN core) |
| `/organization/{id}` | `organization/read.html` | View a specific organization | `organization.read` (CKAN core) |
| `/organization/about/{id}` | `organization/about.html` | About page for an organization | `organization.about` (CKAN core) |
| `/organization/edit/{id}` | `organization/edit.html` | Edit a specific organization | `organization.edit` (CKAN core) |
| `/organization/delete/{id}` | `organization/confirm_delete.html` | Confirm organization deletion | `organization.delete` (CKAN core) |
| `/organization/members/{id}` | `organization/members.html` | List members of an organization | `organization.members` (CKAN core) |
| `/organization/member_new/{id}` | `organization/member_new.html` | Add a new member to an organization | `organization.member_new` (CKAN core) |
| `/organization/bulk_process/{id}` | `organization/bulk_process.html` | Bulk process datasets in an organization | `organization.bulk_process` (CKAN core) |

## Group Routes

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/group` | `group/index.html` | List all groups | `group.index` (CKAN core) |
| `/group/new` | `group/new.html` | Create new group form | `group.new` (CKAN core) |
| `/group/{id}` | `group/read.html` | View a specific group | `group.read` (CKAN core) |
| `/group/about/{id}` | `group/about.html` | About page for a group | `group.about` (CKAN core) |
| `/group/edit/{id}` | `group/edit.html` | Edit a specific group | `group.edit` (CKAN core) |
| `/group/delete/{id}` | `group/confirm_delete.html` | Confirm group deletion | `group.delete` (CKAN core) |
| `/group/members/{id}` | `group/members.html` | List members of a group | `group.members` (CKAN core) |
| `/group/member_new/{id}` | `group/member_new.html` | Add a new member to a group | `group.member_new` (CKAN core) |

## User Routes

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/user` | `user/list.html` | List all users | `user.index` (CKAN core) |
| `/user/register` | `user/new.html` | User registration form | `user.register` (CKAN core) |
| `/user/login` | `user/login.html` | User login form | `user.login` (CKAN core) |
| `/user/logout` | `user/logout.html` | User logout | `user.logout` (CKAN core) |
| `/user/reset` | `user/request_reset.html` | Request password reset | `user.request_reset` (CKAN core) |
| `/user/reset/{id}` | `user/perform_reset.html` | Perform password reset | `user.perform_reset` (CKAN core) |
| `/user/{id}` | `user/read.html` | View a specific user profile | `user.read` (CKAN core) |
| `/user/edit/{id}` | `user/edit.html` | Edit a specific user | `user.edit` (CKAN core) |
| `/user/delete/{id}` | `user/confirm_delete.html` | Confirm user deletion | `user.delete` (CKAN core) |
| `/user/activity/{id}` | `user/activity_stream.html` | Activity stream for a user | `user.activity` (CKAN core) |
| `/dashboard` | `user/dashboard.html` | User dashboard | `dashboard.index` (CKAN core) |
| `/dashboard/datasets` | `user/dashboard_datasets.html` | User's datasets | `dashboard.datasets` (CKAN core) |
| `/dashboard/organizations` | `user/dashboard_organizations.html` | User's organizations | `dashboard.organizations` (CKAN core) |
| `/dashboard/groups` | `user/dashboard_groups.html` | User's groups | `dashboard.groups` (CKAN core) |
| `/user/api-tokens` | `user/api_tokens.html` | Manage API tokens | `user.api_tokens` (CKAN core) |

## Admin Routes

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/ckan-admin` | `admin/index.html` | Admin dashboard | `admin.index` (CKAN core) |
| `/ckan-admin/config` | `admin/config.html` | Site configuration | `admin.config` (CKAN core) |
| `/ckan-admin/trash` | `admin/trash.html` | Trash (deleted items) | `admin.trash` (CKAN core) |

## Custom ARTESP Routes

These routes are specific to the ARTESP CKAN theme extension and are defined in the `controllers.py` file.

| URL Pattern | Template File | Description | Controller/Blueprint Function |
|-------------|---------------|-------------|------------------------------|
| `/about-ckan` | `static/about_ckan.html` | Information about CKAN software | `artesp_theme.about_ckan` |
| `/terms` | `static/terms.html` | Terms of use for the portal | `artesp_theme.terms` |
| `/privacy` | `static/privacy.html` | Privacy policy for the portal | `artesp_theme.privacy` |
| `/contact` | `static/contact.html` | Contact information page | `artesp_theme.contact` |

## Notes

1. All custom routes are defined in the `controllers.py` file and registered through the `artesp_theme` Blueprint.
2. Standard CKAN routes are overridden by providing template files with the same path as the original CKAN templates.
3. The ARTESP theme extends many of the core CKAN templates to customize the appearance and functionality while maintaining the same URL structure.
4. All routes are accessible through the `h.url_for()` helper function in templates, which generates the correct URL based on the route name.

For more information about CKAN routing, refer to the [CKAN documentation](https://docs.ckan.org/en/latest/contributing/frontend/index.html).
