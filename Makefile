.PHONY: build clean publish

build:
	python -m build

clean:
	rm -rf build dist *.egg-info

publish: build
	@echo "Tag the commit with vX.Y.Z and push to GitHub to trigger the release workflow."
