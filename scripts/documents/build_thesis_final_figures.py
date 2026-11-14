"""Current safe diagram-generation entry point; retained old assets are read only.

The former fixed viewport could clip the left swimlane frame. Delegate all
current diagram generation to the measured-bounds renderer and a new directory.
Screenshot evidence and previous review derivatives are never overwritten.
"""
from build_thesis_border_figures import main
if __name__=='__main__':main()
