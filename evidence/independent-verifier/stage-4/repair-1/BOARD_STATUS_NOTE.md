# Preserved post-seal shared-task status correction

After preparation commit `f4addfc743c6c5ffb7e9d9b1ccf41d89572c57a5` and inspection seal `4464a5d76554612982285c31137d76abd4a0edac`, the first shared-card status command used capitalized `Completed`. The CLI returned1:

```
error: unknown status "Completed" (want pending|in_progress|blocked|completed)
```

The same agent-scoped command with lowercase `completed` then returned0 and displayed `#27 Completed`:

```
/Applications/Band.app/Contents/MacOS/jam --profile default --session nw-final-independent-verifier work room-status a679827f-443c-4eac-a10f-7d8f79b5bdbc 27 completed
```

A later read-only board filter looked for a numeric id/uid27 and printed an empty list; this is an incorrect diagnostic filter, not evidence that the task is absent. The successful setter response establishes the recorded completion. Original tool outputs remain in the room. No service, graded path, earlier evidence, candidate result or coverage row was changed by these operations. Card27 is completed only for preparation; new current execution remains held. This successor note is outside the earlier audit's explicitly scoped file manifest.
