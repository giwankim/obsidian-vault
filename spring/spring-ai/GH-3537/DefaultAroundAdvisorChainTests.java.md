# Location
spring-ai-client-chat/src/test/java/org/springframework/ai/chat/client/advisor/DefaultAroundAdvisorChainTests.java
# Coverage

| Category          | Tests                                                                                                                                                                                                                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Null validation   | `whenObservationRegistryIsNullThenThrow`, `whenAdvisorIsNullThenThrow`, `whenAdvisorListIsNullThenThrow`, `whenAdvisorListContainsNullElementsThenThrow`                                                                                                                                                                        |
| Observation       | `getObservationConventionIsNullThenUseDefault`, getObservationRegistry, `whenCopyingChainThenObservationRegistryIsPreserved`                                                                                                                                                                                                    |
| Advisor retrieval | `getCallAdvisors`, `getStreamAdvisors`(verifies original list is unchanged after execution)                                                                                                                                                                                                                                     |
| `copy()` behavior | `whenAFterAdvisorIsNullThenThrowException`, `whenAdvisorNotInChainThenThrowException`, `whenAdvisorIsLastInChainThenReturnEmptyChain`, `whenAdvisorIsFirstInChainThenReturnChainWithRemainingAdvisors`, `whenAdvisorIsInMiddleOfChainThenReturnChainWithRemainingAdvisors`, `whenCopyingChainThenOriginalChainRemainsUnchanged` |

| Category           | Tests   | Description                                                                                   |
| ------------------ | ------- | --------------------------------------------------------------------------------------------- |
| Null Validation    | 4 tests | Lines 49-77: Verifies null checks for registry, single advisor, list, and null elements       |
| Default Convention | 1 test  | Lines 79-85: Null observation convention falls back to default                                |
| Registry Access    | 1 test  | Lines 87-92: getObservationRegistry() returns correct instance                                |
| Advisor Retrieval  | 2 tests | Lines 94-134: getCallAdvisors()/getStreamAdvisors() return original list even after execution |
| Copy Method        | 6 tests | Lines 136-246: Comprehensive copy() method testing                                            |
# Notable
Tests verify that `getCallAdvisors()/getStreamAdvisors()` return consistent results even after `nextCall()/nextStream()` mutate the internal deques--this is why `originalCallAdvisors/originalStreamAdvisors` exists.
# Notable Test Patterns
## Immutability verification (lines 107-112, 129-133)
```java
chain.nextCall(...) // Execute chain (pops from deque)
assertThat(chain.getCallAdvisors()).containsExactlyInAnyOrder(...); // Still has all advisors
```
This confirms that `originalCallAdvisors` preserves the full list regardless of execution state.
## Copy operation tests verify
- Null advisor throws `IllegalArgumentException`
- Missing advisor throws with advisor name in message
- Last advisor returns empty chain
- First/middle advisor returns
- Original chain unchanged after copy
- ObservationRegistry preserved in copied chain
## Test Helper
```java
private CallAdvisor createMockAdvisor(String name, int order) {
	// Creates anonymous CallAdvisor that delegates to chain.nextCall()
}
```
## Observations
1. Good coverage of edge cases and error conditions
2. No streaming-specific copy tests - the `copy()` method only supports `CallAdvisorChain`, not `StreamAdvisorChain`
3. Uses both Mockito mocks and anonymous implementations depending on test needs
