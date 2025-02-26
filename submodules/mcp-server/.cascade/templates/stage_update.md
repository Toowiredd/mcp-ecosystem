# Stage Update Template

```
Cascade Stage {N} Complete: {Stage Name} ✓

- {Completed Item 1}
- {Completed Item 2}
- {Completed Item 3}
- {Completed Item 4}

Automatically proceeding to Stage {N+1}: {Next Stage Name}...
```

## Usage Instructions

1. Replace {N} with current stage number
2. Replace {Stage Name} with completed stage name
3. List all completed items with bullet points
4. Include checkmark (✓) after stage name
5. Indicate next stage at the bottom

## Example

```
Cascade Stage 1 Complete: Security Foundation ✓

- Implemented request validation with Pydantic models
- Added rate limiting (10/min for updates, 30/min for queries)
- Enhanced error handling with custom exceptions
- Improved WebSocket security with message validation

Automatically proceeding to Stage 2: Docker Security Configuration...
```
