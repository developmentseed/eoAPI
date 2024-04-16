# 3DEP Data Mesh Architecture

## Diagrams

These visualizations are make using [mermaid.js](https://mermaid.js.org/) using [text-based markdown syntax](https://mermaid.js.org/syntax/flowchart.html?id=flowcharts-basic-syntax) converted to PDF. To recreate PDFs install [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) using command `npm install -g @mermaid-js/mermaid-cli` (required node.js installed locally) and run command `mmdc -i input.mmd -o output.svg`.

## Implementation

* [jupyter/docker-stacks](https://github.com/jupyter/docker-stacks) for "Ready-to-run Docker images containing Jupyter applications"
    * [all-spark-notebook](https://quay.io/repository/jupyter/all-spark-notebook) container image on Red Hat's quay.io

# Data used

* [USGS-lidar on AWS Opendata](https://aws.amazon.com/marketplace/pp/prodview-647e3hzk3b3jc?sr=0-2&ref_=beagle&applicationId=AWSMPContessa#overview)
    * [USGS-lidar on AWS Opendata](https://registry.opendata.aws/usgs-lidar/)
* [NOAA Coastal Lidar on AWS S3](https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/index.html#entwine/stac/)
