from __future__ import print_function

input_file_name = 'page_1.txt'
lines_to_skip = 0

line_index = 0
requests = []
responses = {}
for line in open(input_file_name):
    line_index += 1
    if line_index < lines_to_skip:
        continue
    header, dlc, _, _, b2, b3, b4, b5, b6 = line.strip().split()
    cmd_id = b2
    if b2 == 'FA':
        cmd_id = b3 + b4
        hex_value = b5 + b6
    else:
        hex_value = b3 + b4
    if header == '10A':
        if not cmd_id in requests:
            requests.append(cmd_id)
    else:
        if not cmd_id in responses:
            responses[cmd_id] = []
        responses[cmd_id].append(str(int(hex_value, 16)))

commands = set(list(requests) + responses.keys())
for cmd in commands:
    if cmd in requests:
        print('{:>4}'.format(cmd), end='')
    else:
        print('----', end='')
    print(': ', end='')
    if cmd in responses:
        print('[{}] {}'.format(cmd, ' '.join(responses[cmd])), end='')
    else:
        print('----', end='')
    print()
#~ print('REQUESTS\n{}'.format('\n'.join(sorted(requests))))
#~ print('RESPONSES\n{}'.format('\n'.join(['{}: {}'.format(k, ','.join(responses[k])) for k in sorted(responses.keys())])))
print('{} lines processed, first {} skipped'.format(line_index, lines_to_skip))