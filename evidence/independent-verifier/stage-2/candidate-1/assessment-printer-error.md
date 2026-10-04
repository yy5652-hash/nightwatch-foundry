# Preserved verifier aggregation error

The first `assess.py --cleanup` invocation completed source capture, the four zero-code cleanup operations and coverage/summary writes, then its final stdout printer raised `TypeError: dict() got multiple values for keyword argument 'failed'`. This exact error was observed in the tool result. The print field was renamed `failed_ids`; a new aggregation invocation completed. This note records a verifier error, not a retained service-failure log or a service defect.
