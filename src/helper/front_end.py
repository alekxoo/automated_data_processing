import sys
import time

def update_loading_bar():
    # Display a simple loading bar
    total_bar_length = 50
    for i in range(total_bar_length + 1):
        sys.stdout.write('\r')
        sys.stdout.write(f"[{'=' * i}{' ' * (total_bar_length - i)}] {i * 2}%")
        sys.stdout.flush()
        time.sleep(0.01)  # Simulate processing time


def color_status(val):
    if val == 'FAIL':
        color = 'red'
    elif val == 'PASS':
        color = 'green'
    else:
        color = 'black'
    return f'color: {color}'

def highlight_status(status):
    if status == 'PASS':
        return 'background-color: green'
    elif status == 'FAIL':
        return 'background-color: red'
    else:
        return ''