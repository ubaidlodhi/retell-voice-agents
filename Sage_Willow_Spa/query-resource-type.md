# QueryResourceTypes

# Package: resources

# Namespace: ResourceTypesService

# Method link: https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/query-resource-types.md

## Permission Scopes:
Read Bookings - Public Data: SCOPE.DC-BOOKINGS.READ-BOOKINGS-PUBLIC

## Introduction

Retrieves up to 100 resource types, given the provided filtering, paging, and sorting.

To learn about working with Query methods, see:
- [API Query Language](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/data-retrieval/about-the-wix-api-query-language.md)
- [Sorting and Paging](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/data-retrieval/about-sorting-and-paging.md)

---

## REST API

### Schema

```
 Method: queryResourceTypes
 Description: Retrieves up to 100 resource types, given the provided filtering, paging, and sorting.  To learn about working with Query methods, see: - [API Query Language](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/data-retrieval/about-the-wix-api-query-language.md) - [Sorting and Paging](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/data-retrieval/about-sorting-and-paging.md)
 URL: https://www.wixapis.com/bookings/v2/resources/resource-types/query
 Method: POST
 Method parameters:
   param name: query | type: CursorQuery   
     - name: cursorPaging | type: CursorPaging | description: Cursor token pointing to a page of results. Not used in the first request. Following requests use the cursor token and not `filter` or `sort`. 
        - name: limit | type: integer | description: Number of items to load. 
        - name: cursor | type: string | description: Pointer to the next or previous page in the list of results.  You can get the relevant cursor token from the `pagingMetadata` object in the previous call's response. Not relevant for the first request. 
        - name: filter | type: object | description: Filter object in the following format: `"filter" : { "fieldName1": "value1", "fieldName2":{"$operator":"value2"} }` Example of operators: `$eq`, `$ne`, `$lt`, `$lte`, `$gt`, `$gte`, `$in`, `$hasSome`, `$hasAll`, `$startsWith`, `$contains` 
        - name: sort | type: array<Sorting> | description: Sort object in the following format: `[{"fieldName":"sortField1","order":"ASC"},{"fieldName":"sortField2","order":"DESC"}]` 
           - name: fieldName | type: string | description: Name of the field to sort by. 
           - name: order | type: SortOrder | description: Sort order. 
                 - enum: ASC, DESC
 Return type: QueryResourceTypesResponse
  - name: resourceTypes | type: array<ResourceType> | description: Retrieved resource types. 
     - name: id | type: string | description: Resource type GUID. 
     - name: revision | type: string | description: Revision number, which increments by 1 each time the resource type is updated. To prevent conflicting changes, the current revision must be passed when updating the resource type. 
     - name: createdDate | type: string | description: Time in `YYYY-MM-DDThh:mm:ss.sssZ` format the resource type was created. 
     - name: updatedDate | type: string | description: Time in `YYYY-MM-DDThh:mm:ss.sssZ` format the resource type was last updated. 
     - name: name | type: string | description: Name of the resource type. For example, `meeting room`. The name must be unique per site. 
     - name: extendedFields | type: ExtendedFields | description: Extensions enabling users to save custom data related to the resource type. 
        - name: namespaces | type: object | description: Extended field data. Each key corresponds to the namespace of the app that created the extended fields. The value of each key is structured according to the schema defined when the extended fields were configured.  You can only access fields for which you have the appropriate permissions.  Learn more about [extended fields](https://dev.wix.com/docs/rest/articles/getting-started/extended-fields.md). 
  - name: pagingMetadata | type: CursorPagingMetadata | description: Paging metadata. 
     - name: count | type: integer | description: Number of items returned in the response. 
     - name: cursors | type: Cursors | description: Offset that was requested. 
        - name: next | type: string | description: Cursor pointing to next page in the list of results. 
        - name: prev | type: string | description: Cursor pointing to previous page in the list of results. 
     - name: hasNext | type: boolean | description: Indicates if there are more results after the current page. If `true`, another page of results can be retrieved. If `false`, this is the last page. 


```

### Examples

### Query resource types with a filter.
Query resource types, providing a filter to select only the ones starting with a specific value.

```curl
curl -X POST \
'https://www.wixapis.com/bookings/v2/resources/resource-types/query' \
-H 'Authorization: <AUTH>' \
-d '{
  "query": {
    "filter": {
      "name": {
        "$startsWith": "meeting"
      }
    },
    "cursorPaging": {
      "cursor": null,
      "limit": 10
    }
  }
}'
```

### Query resource types.
Query resource types, providing a limit to the number of results returned.

```curl
curl -X POST \
'https://www.wixapis.com/bookings/v2/resources/resource-types/query' \
-H 'Authorization: <AUTH>' \
-d '{
  "query": {
    "cursorPaging": {
      "cursor": null,
      "limit": 10
    }
  }
}'
```

---

## JavaScript SDK

### Schema

```
 Method: wixClientAdmin.resources.ResourceTypesService.queryResourceTypes(query)
 Description: Retrieves up to 100 resource types, given the provided filtering, paging, and sorting.  To learn about working with Query methods, see: - [API Query Language](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/data-retrieval/about-the-wix-api-query-language.md) - [Sorting and Paging](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/data-retrieval/about-sorting-and-paging.md)
 Required parameters: query
 Method parameters: 
   param name: query | type: ResourceTypeQuery   | required: true
     - name: cursorPaging | type: CursorPaging | description: Cursor token pointing to a page of results. Not used in the first request. Following requests use the cursor token and not `filter` or `sort`. 
        - name: limit | type: integer | description: Number of items to load. 
        - name: cursor | type: string | description: Pointer to the next or previous page in the list of results.  You can get the relevant cursor token from the `pagingMetadata` object in the previous call's response. Not relevant for the first request. 
        - name: filter | type: object | description: Filter object in the following format: `"filter" : { "fieldName1": "value1", "fieldName2":{"$operator":"value2"} }` Example of operators: `$eq`, `$ne`, `$lt`, `$lte`, `$gt`, `$gte`, `$in`, `$hasSome`, `$hasAll`, `$startsWith`, `$contains` 
        - name: sort | type: array<Sorting> | description: Sort object in the following format: `[{"fieldName":"sortField1","order":"ASC"},{"fieldName":"sortField2","order":"DESC"}]` 
           - name: fieldName | type: string | description: Name of the field to sort by. 
           - name: order | type: SortOrder | description: Sort order. 
                 - enum: ASC, DESC
 Return type: PROMISE<QueryResourceTypesResponse>
  - name: resourceTypes | type: array<ResourceType> | description: Retrieved resource types. 
     - name: _id | type: string | description: Resource type GUID. 
     - name: revision | type: string | description: Revision number, which increments by 1 each time the resource type is updated. To prevent conflicting changes, the current revision must be passed when updating the resource type. 
     - name: _createdDate | type: Date | description: Time in `YYYY-MM-DDThh:mm:ss.sssZ` format the resource type was created. 
     - name: _updatedDate | type: Date | description: Time in `YYYY-MM-DDThh:mm:ss.sssZ` format the resource type was last updated. 
     - name: name | type: string | description: Name of the resource type. For example, `meeting room`. The name must be unique per site. 
     - name: extendedFields | type: ExtendedFields | description: Extensions enabling users to save custom data related to the resource type. 
        - name: namespaces | type: object | description: Extended field data. Each key corresponds to the namespace of the app that created the extended fields. The value of each key is structured according to the schema defined when the extended fields were configured.  You can only access fields for which you have the appropriate permissions.  Learn more about [extended fields](https://dev.wix.com/docs/rest/articles/getting-started/extended-fields.md). 
  - name: pagingMetadata | type: CursorPagingMetadata | description: Paging metadata. 
     - name: count | type: integer | description: Number of items returned in the response. 
     - name: cursors | type: Cursors | description: Offset that was requested. 
        - name: next | type: string | description: Cursor pointing to next page in the list of results. 
        - name: prev | type: string | description: Cursor pointing to previous page in the list of results. 
     - name: hasNext | type: boolean | description: Indicates if there are more results after the current page. If `true`, another page of results can be retrieved. If `false`, this is the last page. 


```

### Examples

### queryResourceTypes
```javascript
import { resourceTypes } from '@wix/bookings';

async function queryResourceTypes(query) {
  const response = await resourceTypes.queryResourceTypes(query);
};
```

### queryResourceTypes (with elevated permissions)
```javascript
import { resourceTypes } from '@wix/bookings';
import { auth } from '@wix/essentials';

async function myQueryResourceTypesMethod(query) {
  const elevatedQueryResourceTypes = auth.elevate(resourceTypes.queryResourceTypes);
  const response = await elevatedQueryResourceTypes(query);
}
```

### queryResourceTypes (self-hosted)
Self-hosted SDK calls require you to [create a client](https://dev.wix.com/docs/sdk/articles/work-with-the-sdk/about-the-wix-client.md).

```javascript
import { createClient } from '@wix/sdk';
import { resourceTypes } from '@wix/bookings';
// Import the auth strategy for the relevant access type
// Import the relevant host module if needed

const myWixClient = createClient ({
  modules: { resourceTypes },
  // Include the auth strategy and host as relevant
});


async function queryResourceTypes(query) {
  const response = await myWixClient.resourceTypes.queryResourceTypes(query);
};
```

---