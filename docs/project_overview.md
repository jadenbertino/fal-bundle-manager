# Resource Bundles Manager

Fal’s Serverless GPU product allows users to deploy their own AI apps by using our Python SDK. As part of packaging their app, users can include local files (e.g. YAML configs, safe tensors, precompiled binaries). Since each deployment produces a build, we call the associated files for each build a “resource bundle”.

## Objective

The objective of this exercise is to build a toy system that manages resource bundles.

## Deliverables

- Deliver two components:
  - A server component that exposes the necessary APIs and stores the data
  - A CLI tool that allows users to create, list, and download bundles
- Use Python as the programming language. For state storage you can use local files or Redis, we don’t need anything complex there.

## Requirements

### CLI
- **create** command that takes in a list of paths to files or directories, does the upload and returns a bundle ID
- **list** command that lists the available bundles, showing:
  - Bundle ID
  - Number of files
  - Total size
  - Creation date
- **download** command that takes a bundle ID and returns the bundled files in an archive format 
  (tar/tar.gz/zip works)

### Server
- Manages state
- Stores the files locally

### Efficiency Requirements
- The solution should be efficient in terms of storage and bandwidth:
  - It should not upload files already uploaded in a previous bundle
  - It should not store the same file multiple times on disk

## Live Programming Session

After you are done, we would like to have a roughly 1.5-hour session where we will ask you to 
implement an additional feature. The aim of this is to see how you work in real-time. 
It’s fine to use AI tools, we all do.
