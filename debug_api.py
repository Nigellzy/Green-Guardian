from perception import DataGovClient
import json

client = DataGovClient()
data = client._get_data("air-temperature")

if data:
    print("Response structure:")
    print(json.dumps(data, indent=2, default=str))
else:
    print("No data returned from API")
