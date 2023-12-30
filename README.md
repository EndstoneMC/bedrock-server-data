# bedrock-server-data

Automated repository for metadata and assets related to Minecraft's Bedrock Dedicated Server.

## Structure

- `metadata/`: Contains JSON files with metadata information.
    - `versions.json`: Metadata for the server versions, including download links and checksums.

## Automation

This repository uses GitHub Actions to automatically run the `check_version.py` script daily. If a new version of the
Bedrock Dedicated Server is detected, the `versions.json` file will be updated, and the changes will be committed to
this repository.

## Contributing

If you'd like to contribute or notice any discrepancies, please fork the repository and create a pull request or open an
issue for discussion.

## License

This repository is under the MIT License. See the LICENSE file for more details.
