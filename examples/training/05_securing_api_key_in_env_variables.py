from nearmap import NEARMAP
import os

# Steps:
# 1.) Create an environment variable called "NEARMAP_API_KEY" and provide your api key as a value
# - Open Command Prompt
# - Run: setx NEARMAP_API_KEY "MY_API_KEY_GOES_HERE"
# - Run: refreshenv

api_key = os.environ.get("NEARMAP_API_KEY")
print(api_key)

nearmap = NEARMAP(api_key)
print(nearmap.api_key)

