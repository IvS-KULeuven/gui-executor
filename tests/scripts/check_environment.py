import os

test_env = os.environ["TEST_ENVIRONMENT"]

if test_env != "this-is-just-a-test-variable":
    raise ValueError(f"Not the correct content for the TEST_ENVIRONMENT, {test_env}")

print(test_env)
