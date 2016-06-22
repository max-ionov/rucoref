import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import numpy as np

from math import sqrt

SPINE_COLOR = 'gray'

def latexify(fig_width=None, fig_height=None, columns=1):
    """Set up matplotlib's RC params for LaTeX plotting.
    Call this before plotting a figure.

    Parameters
    ----------
    fig_width : float, optional, inches
    fig_height : float,  optional, inches
    columns : {1, 2}
    """

    # code adapted from http://www.scipy.org/Cookbook/Matplotlib/LaTeX_Examples

    # Width and max height in inches for IEEE journals taken from
    # computer.org/cms/Computer.org/Journal%20templates/transactions_art_guide.pdf

    assert(columns in [1,2])

    if fig_width is None:
        fig_width = 3.39 if columns==1 else 6.9 # width in inches

    if fig_height is None:
        golden_mean = (sqrt(5)-1.0)/2.0    # Aesthetic ratio
        fig_height = fig_width*golden_mean # height in inches

    MAX_HEIGHT_INCHES = 8.0
    if fig_height > MAX_HEIGHT_INCHES:
        print("WARNING: fig_height too large:" + fig_height +
              "so will reduce to" + str(MAX_HEIGHT_INCHES) + "inches.")
        fig_height = MAX_HEIGHT_INCHES

    params = {'backend': 'ps',
              'text.latex.preamble': ['\usepackage{gensymb}'],
              'axes.labelsize': 8, # fontsize for x and y labels (was 10)
              'axes.titlesize': 8,
              'text.fontsize': 8, # was 10
              'legend.fontsize': 8, # was 10
              'xtick.labelsize': 8,
              'ytick.labelsize': 8,
              'text.usetex': True,
              'figure.figsize': [fig_width,fig_height],
              'font.family': 'serif'
    }

    matplotlib.rcParams.update(params)


def format_axes(ax):

    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)

    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(SPINE_COLOR)
        ax.spines[spine].set_linewidth(0.5)

    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_tick_params(direction='out', color=SPINE_COLOR)

    return ax

def plot_feature_distribution(distribution, bins, class_names, x_label='Feature value', filename='plot.pdf'):
    fig = plt.figure()

    ax = plt.gca()
    ax.set_xlabel(x_label)
    ax.set_ylabel("Density")
    plt.tight_layout()
    format_axes(ax)

    normed = True

    true_hist = np.histogram(distribution[class_names[1]], bins, normed=normed)
    false_hist = np.histogram(distribution[class_names[0]], bins, normed=normed)

    w = 0.3

    true_x = [item for item in range(len(true_hist[0]))]
    false_x = [item+w for item in range(len(false_hist[0]))]

    ax.set_xticks([item + float(w) for item in true_x])
    ax.set_xticklabels(true_x)

    rects1 = plt.bar(false_x, false_hist[0], w, color='0.3')
    rects2 = plt.bar(true_x, true_hist[0], w, color='0.7')
    plt.legend((rects1, rects2), class_names, loc='upper right')

    plt.savefig("{}.pdf".format(filename))
    plt.show()
    plt.close()

def plot_learning_curve(train_sizes, train_scores, test_scores, filename='learning_curve_plot', score_name="Score"):
    ax = plt.gca()
    ax.set_xlabel("Training examples")
    ax.set_ylabel(score_name)

    plt.tight_layout()
    format_axes(ax)

    ax.set_xticks(train_sizes)

    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                     train_scores_mean + train_scores_std, alpha=0.1,
                     color="r")
    plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                     test_scores_mean + test_scores_std, alpha=0.1, color="g")

    plot_train = plt.plot(train_sizes, [float(sum(row))/len(row) for row in train_scores],
                          color='r',
                         label='Training score')
    plot_test = plt.plot(train_sizes, [float(sum(row))/len(row) for row in test_scores],
                         color='g',
                        label='Cross-validation score')

    plt.legend(loc='lower right')

    plt.savefig("{}.pdf".format(filename))
    #plt.show()
    #plt.close()

    return ax

def plot_confusion_matrix():
    pass