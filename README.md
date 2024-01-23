# fw-pipeline-io

## Summary
This python package uses various Flywheel tools, like the CLI and SDK, to
help with the rapid development of gears that are meant to run in a pipeline. In its
current phase, it is meant to be used in conjunction with a specialized gear 
template, so that all gears handle input and outputs in a consistent and simple manner.

## Requirements
Some modules require the Flywheel CLI to be installed and configured. For python
package dependencies, see [pyproject.toml](pyproject.toml).

If using this package in a Docker image/Flywheel gear, ensure that the Dockerfile
copies the executable from your gear repository similarly as follows:

```
    COPY ./fw '/usr/local/bin/'"
```

Please also check that the .dockerignore file does not exclude the CLI executable 
file `fw` from being copied into the Docker image.

## Cite

## License 
[MIT License](LICENSE)

## FAQ

[FAQ.md](FAQ.md)

## Contributing

[For more information about how to get started contributing to that gear,
checkout [CONTRIBUTING.md](CONTRIBUTING.md).]
<!-- markdownlint-disable-file -->
