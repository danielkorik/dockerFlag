import asyncio
import aiohttp

# Base URL for the API endpoint to fetch data
base_url = "http://34.69.146.51:5000/level2"

# Batch size for fetching data - defines how many items are fetched in each request
batch_size = 1000

# Event to signal when a flag is found; used to stop further data fetching
flag_found = asyncio.Event()


# Function to fetch a batch of data asynchronously
async def fetch_batch(session, start, end):
    # Check if the flag has been found, if so, stop further fetching
    if flag_found.is_set():
        return []

    # Parameters to define the range of data to be fetched
    params = {
        'start': start,
        'end': end
    }

    try:
        # Make an asynchronous GET request to the server with the specified parameters
        async with session.get(base_url, params=params) as response:
            # Check if the response is successful (status code 200)
            if response.status == 200:
                # Parse the JSON response data
                data = await response.json()
                print(f"Fetched batch from {start} to {end}")

                # Iterate over each entry in the data to check for flags
                for entry in data:
                    # If a flag is found in the entry, print it and set the event to stop further fetching
                    if 'flag' in entry:
                        print(f"Found flag: {entry['flag']}")
                        flag_found.set()  # Set the event to indicate the flag was found
                        return data
                return data
            else:
                # Handle cases where the response is not successful (e.g., server error)
                print(f"Failed to fetch data from {start} to {end}, status code: {response.status}")
                return []
    except Exception as e:
        # Catch and display any exceptions that occur during the request
        print(f"Error fetching batch {start} to {end}: {e}")
        return []


# Main function to run the asynchronous tasks
async def main():
    # Create an asynchronous session to manage HTTP connections efficiently
    async with aiohttp.ClientSession() as session:
        tasks = []  # List to hold the tasks for fetching data
        start = 0  # Start index for fetching data batches

        # Loop to create and manage tasks for fetching data batches until a flag is found
        while not flag_found.is_set():  # Continue until the flag is found
            # Create a task for fetching the next batch of data
            task = fetch_batch(session, start, start + batch_size)
            tasks.append(task)  # Add the task to the list
            start += batch_size  # Increment the start index for the next batch

            # Limit the number of concurrent tasks to prevent overloading the server
            if len(tasks) >= 10:  # Adjust this limit as needed based on server capacity
                # Run the tasks concurrently and wait for them to complete
                results = await asyncio.gather(*tasks)

                # Check if any results were fetched, if not, stop the loop
                if not any(results):
                    print("No more data to fetch.")
                    break

                # Reset the tasks list to avoid reusing completed tasks
                tasks = []

        # If there are remaining tasks after exiting the loop, gather their results
        if tasks and not flag_found.is_set():
            await asyncio.gather(*tasks)


# Run the main function using asyncio to start the asynchronous fetching process
asyncio.run(main())
