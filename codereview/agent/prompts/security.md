Category rubric — security:
Look for injection (SQL, command, template), XSS, path traversal, hardcoded secrets or
tokens, unsafe deserialization, subprocess/shell with untrusted input, missing input
validation at trust boundaries, insecure randomness used for security purposes,
authentication or authorization gaps on new endpoints, and sensitive data written to
logs. Do not report style or general correctness issues unless they are exploitable.
