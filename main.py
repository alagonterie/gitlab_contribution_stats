from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from json import dump

from gitlab import Gitlab
from tqdm import tqdm

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


def process_merge_request(merge_request, progress):
    user_contributions = defaultdict(lambda: defaultdict(dict))

    author = merge_request.author['username']
    if author in exclude_author_usernames:
        progress.update(1)
        return user_contributions

    user_contributions[author].setdefault(
        'merge_requests',
        {
            'count': 0,
            'percentage': 0.0
        }
    )
    user_contributions[author]['merge_requests']['count'] += 1

    total_additions = 0
    total_deletions = 0
    changes = merge_request.changes()
    for c in changes['changes']:
        diff_lines = c['diff'].split('\n')
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        total_additions += additions
        total_deletions += deletions

    user_contributions[author]['changes'] = {
        'added_lines': total_additions,
        'deleted_lines': total_deletions,
        'total_lines': total_additions + total_deletions
    }

    # Iterate over notes in a merge request
    for note in merge_request.notes.list(all=True):
        note_author = note.author['username']
        if note_author in exclude_author_usernames:
            continue

        user_contributions[note_author].setdefault(
            'comments',
            {
                'count': 0,
                'percentage': 0.0
            }
        )
        user_contributions[note_author]['comments']['count'] += 1

    progress.update(1)
    return user_contributions


def main():
    # GitLab setup
    gl = Gitlab(gitlab_url, private_token=gitlab_private_token)
    project = gl.projects.get(gitlab_project_id)

    # Get total number of merge requests for progress calculation
    print('Fetching Merge Requests. This may take a while...')
    merge_requests = project.mergerequests.list(all=True, state='merged')
    total_merge_requests = len(merge_requests)
    total_comments = 0
    total_changes = {
        'added_lines': 0,
        'deleted_lines': 0,
        'total_lines': 0
    }

    user_contributions = defaultdict(lambda: defaultdict(dict))
    top_contributors = defaultdict(list)

    with tqdm(desc='Processing Merge Requests', total=total_merge_requests) as progress:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_merge_request, merge_request, progress) for merge_request in merge_requests]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    for user, contributions in result.items():
                        for category, contribution in contributions.items():
                            if category in ['merge_requests', 'comments']:
                                user_contributions[user][category].setdefault('count', 0)
                                user_contributions[user][category]['count'] += contribution.get('count', 0)
                                if category == 'comments':
                                    total_comments += contribution.get('count', 0)
                            elif category == 'changes':
                                for change_type in ['added_lines', 'deleted_lines', 'total_lines']:
                                    old_value = user_contributions[user][category].get(change_type, 0)
                                    user_contributions[user][category][change_type] = old_value + contribution.get(change_type, 0)
                                    total_changes[change_type] += contribution.get(change_type, 0)
                except Exception as exc:
                    print(f'\nAn exception occurred: {exc}')

    # Compute top contributors and percentage
    for user, contributions in user_contributions.items():
        for category, contribution in contributions.items():
            if category == 'changes':
                for change_type in ['added_lines', 'deleted_lines', 'total_lines']:
                    if contribution[change_type] > 0:
                        percentage = round(contribution[change_type] / total_changes[change_type], percentage_decimals)
                        user_contributions[user][category][change_type + '_percentage'] = percentage
            elif category in ['merge_requests', 'comments']:
                if contribution['count'] > 0:
                    total_count = total_comments if category == 'comments' else total_merge_requests
                    percentage = round(contribution['count'] / total_count, percentage_decimals)
                    user_contributions[user][category]['percentage'] = percentage

            top_contributors[category].append(
                {
                    user: contributions[category]
                }
            )

    for category in top_contributors.keys():
        top_contributors[category] = sorted(
            top_contributors[category],
            key=lambda x: x[list(x.keys())[0]]['total_lines'] if category == 'changes' else x[list(x.keys())[0]]['count'],
            reverse=True
        )[:top_n]

    # Write data to file
    print(f'Writing results to {output_file_name}...')
    with open(output_file_name, 'w') as file:
        dump(
            {
                'project_id': gitlab_project_id,
                'top_contributors': {k: [dict(c) for c in v] for k, v in top_contributors.items()},
                'user_contributions': {k: dict(v) for k, v in user_contributions.items()}
            },
            file
        )


if __name__ == '__main__':
    main()
