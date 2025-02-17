def get_nest_data():
    try:
        # Move these to environment variables or config file for security
        projectID = 'templog-450802'
        oauth2_client_id = '1000000000000-0000000000000000000000000000000.apps.googleusercontent.com'
        oauth2_client_secret = 'GOCSPX-00000000000000000000000000000000'
        refreshToken = '1//0000000000000000000000000000000-0000000000000000000000000000000000000000'
        
        # Get new access token
        get_access_token_url = "https://oauth2.googleapis.com/token"  # Updated URL
        get_access_token_data = {
            "client_id": oauth2_client_id,
            "client_secret": oauth2_client_secret,
            "refresh_token": refreshToken,
            "grant_type": "refresh_token"
        }

        get_access_token_response = requests.post(
            get_access_token_url, 
            data=get_access_token_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        if not get_access_token_response.ok:
            return f"Token Error Response: {get_access_token_response.text}"
            
        access_token = get_access_token_response.json().get("access_token")

        # Get Nest data with new access token
        get_nest_data_url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{projectID}/devices"
        get_nest_data_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        data_response = requests.get(get_nest_data_url, headers=get_nest_data_headers)
        if not data_response.ok:
            return f"Nest Data Error Response: {data_response.text}"
            
        devices = data_response.json().get('devices', [])
        temperatures = []
        
        for device in devices:
            if 'traits' in device and 'sdm.devices.traits.Temperature' in device['traits']:
                temp_celsius = device['traits']['sdm.devices.traits.Temperature']['ambientTemperatureCelsius']
                temp_fahrenheit = (temp_celsius * 9/5) + 32
                device_name = device.get('traits', {}).get('sdm.devices.traits.Info', {}).get('customName', 'Unknown Device')
                temperatures.append({
                    'name': device_name,
                    'temperature': round(temp_fahrenheit, 1)
                })
        
        return temperatures
    except Exception as e:
        print(f"Error getting Nest data: {str(e)}")
        return f"Error getting Nest data: {str(e)}"
