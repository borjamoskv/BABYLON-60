
# AskRequest

RAG query: search BABYLON-60 memory and synthesize an answer.

## Properties

Name | Type
------------ | -------------
`query` | string
`project` | string
`k` | number
`temperature` | number
`maxTokens` | number
`systemPrompt` | string

## Example

```typescript
import type { AskRequest } from ''

const example = {
  "query": null,
  "project": null,
  "k": null,
  "temperature": null,
  "maxTokens": null,
  "systemPrompt": null,
} satisfies AskRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as AskRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


