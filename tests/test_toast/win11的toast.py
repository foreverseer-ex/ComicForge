"""
Windows 11 Toast 通知测试。

注意：win11toast 库的 update_progress 函数在某些情况下有 bug。
如果遇到 TypeError: Invalid parameter count 错误，这是 win11toast 库本身的 bug。

解决方案：
1. 不使用 update_progress，而是每次重新创建通知（会显示多个通知）
2. 或者修复 win11toast 库的源代码（在 .venv/Lib/site-packages/win11toast.py 中）
3. 或者使用替代库（如 windows-toasts）
"""
from time import sleep
from win11toast import notify

# 由于 update_progress 有 bug，我们改用重新创建通知的方式
# 这会显示多个通知，但至少可以正常工作

# 创建初始进度通知
notify(progress={
    'title': 'YouTube',
    'status': 'Downloading...',
    'value': '0',
    'valueStringOverride': '0/15 videos'
})

# 每次更新都创建新通知（而不是更新现有通知）
# 注意：这会导致显示多个通知，但避免了 update_progress 的 bug
for i in range(1, 15+1):
    sleep(1)
    notify(progress={
        'title': 'YouTube',
        'status': 'Downloading...',
        'value': str(i/15),
        'valueStringOverride': f'{i}/15 videos'
    })

# 完成通知
notify(title='YouTube', body='Completed!')