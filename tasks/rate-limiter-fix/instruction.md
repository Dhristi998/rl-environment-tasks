# Make the rate limiter's test suite pass

The project in `/app/ratelimiter/` has a failing test suite. Run it with:

    cd /app/ratelimiter && python3 -m pytest -q

Make all the tests pass by fixing the library code. Do not modify, delete or
skip anything in `/app/ratelimiter/tests/`. Your fix will also be checked
against additional tests that you cannot see.
