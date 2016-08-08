.PHONY: dist

SRC=src/main.py src/resources.py src/level.py
IMG=img/CornerPipe.png img/CrossPipe.png img/EndPipe.png img/StraightPipe.png img/TeePipe.png img/SelectorPanel.png img/FillAnimateCornerPipeTopToLeft.png img/FillAnimateCornerPipeTopToRight.png img/FillAnimateCrossPipeIntoAll.png img/FillAnimateEndPipe.png img/FillAnimateStraightPipe.png img/FillAnimateTeePipeFromTop.png img/FillAnimateTeePipeTopIntoLeft.png img/FillAnimateTeePipeTopIntoRight.png

dist: dist/endless-flow.tgz

dist/endless-flow.tgz: run.sh README.md $(SRC) $(IMG)
	mkdir -p dist
	tar -czf $@ $^
