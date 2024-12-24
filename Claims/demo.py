import os

# Replace 'MY_ENV_VAR' with the name of the environment variable you want to print
env_var_name = 'MESSAGE'

# Get the value of the environment variable
env_var_value = os.getenv(env_var_name)

# Check if the environment variable exists
if env_var_value is not None:
    print(f"The value of {env_var_name} is: {env_var_value}")
else:
    print(f"The environment variable {env_var_name} is not set.")
