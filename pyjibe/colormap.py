from matplotlib.colors import LinearSegmentedColormap

colors = ["#FF807D", "#FFD37D", "#D9FF7D", "#7DFF82"]

cm_rating = LinearSegmentedColormap.from_list("gor", colors, N=100)
cm_rating.set_under("#DCDCDC")
