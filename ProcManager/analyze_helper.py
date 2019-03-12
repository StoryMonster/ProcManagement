import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.widgets import Slider
import sys


def draw_subprocesses_by_bar(subprocs):
    fig, ax = plt.subplots()
    items_amount = len(subprocs["pid"])
    rect_amount_per_page = 20 if items_amount >= 20 else items_amount
    plt.ylim((0, max(subprocs["max virtual memory(MB)"])))
    rects = plt.bar(range(rect_amount_per_page), subprocs["max virtual memory(MB)"][0:rect_amount_per_page], tick_label=subprocs["pid"][0:rect_amount_per_page])
    slider_ax= plt.axes([0.1, 0.01, 0.8, 0.03], facecolor='lightgoldenrodyellow')
    max_slider_val = 0 if (items_amount-rect_amount_per_page < 0) else (items_amount-rect_amount_per_page)
    slider = Slider(ax=slider_ax, label="index", valmin=0, valmax=max_slider_val+1, valinit=0, valstep=1)
    def update(_):
        labels = ax.get_xticklabels()
        for i in range(rect_amount_per_page):
            rects[i].set_height(subprocs["max virtual memory(MB)"][slider.val+i])
            labels[i] = subprocs["pid"][slider.val+i]
        ax.set_xticklabels(labels)
        fig.canvas.draw()
    slider.on_changed(update)
    plt.show()

if __name__ == "__main__":
    assert len(sys.argv) == 2, "need one csv file"
    data = pd.read_csv(sys.argv[1])
    draw_subprocesses_by_bar(data[1:])