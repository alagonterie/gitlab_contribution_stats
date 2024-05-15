# GitLab Contribution Stats

This project provides a Python script that fetches, processes, and saves statistics about user contributions to a specific GitLab Project. These contributions include:

- Merge Requests submitted
- Code changes (additions and deletions)
- Comments on Merge Requests

## Requirements

- GitLab python package
- tqdm

## Configuration

You place your configuration options at the beginning of the Python script. For instance:

```python
max_workers = 16
percentage_decimals = 4
top_n = 10

output_file_name = 'gitlab_user_contributions.json'
gitlab_url = 'https://gitlab.com'
gitlab_private_token = ''
gitlab_project_id = '12345678'
exclude_author_usernames = {
  'example-username-1',
  'example-username-2'
}
```

- `max_workers`: It defines the number of threads used during the processing of merge requests;
- `percentage_decimals`: Defines up to which decimal place the percentage contribution of each user is rounded off.
- `top_n`: The script provides statistics for the top `n` contributors in different categories. This configuration option sets `n`.
- `output_file_name`: Name of the file where the output JSON data is stored.
- `gitlab_url`: URL of your GitLab instance (e.g., 'https://gitlab.com')
- `gitlab_private_token`: Your GitLab private token.
- `gitlab_project_id`: Project ID for which statistics are to be fetched.
- `exclude_author_usernames`: A set of usernames to exclude from the statistics.

## Usage

The script will print progress information to the console and write the results to a file specified by the `output_file_name` variable:

```bash
Fetching Merge Requests. This may take a while...
Processing Merge Requests: 100%|██████████| 320/320 [00:30<00:00, 10.45it/s]
Writing results to gitlab_user_contributions.json...
```

The result is a JSON file with detailed statistics for each user and a list of `top_n` contributors in each category.

**Please be aware:** depending on the size of your project and the number of merge requests, the script may run for a while.