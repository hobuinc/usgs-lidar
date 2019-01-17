================================================================================
Using Lambda Layers with USGS LiDAR AWS Public Dataset
================================================================================

:author: Howard Butler
:email: howard@hobu.co
:date: 01/18/2019

Introduction
--------------------------------------------------------------------------------

Point clouds are fast becoming a primary geospatial datatype. Much like typical
raster and vector data, point clouds provide measurement and inference of
geophysical properties. While they are not quite raster images and not quite
abstract geography, point clouds represent individual, discrete measurements in
space, and they are commonly created using LiDAR scanners, coincidence matched
imagery, sonar, and radar.

AWS provides one of the most convenient cloud environments to process massive
point cloud data. Products such as `Lambda`_, `Batch`_, and `Elastic Graphics`_
can allow you to take advantage of the scaling infrastructure that AWS can
provide without taking on as much management burden. This post will describe
how to use Lambda in combination with the new USGS LiDAR Public Dataset to
quickly produce an elevation model directly from LiDAR data using the `PDAL`_
open source software.

.. _`Elastic Graphics`: https://aws.amazon.com/ec2/elastic-graphics/
.. _`Lambda`: https://aws.amazon.com/lambda/
.. _`Batch`: https://aws.amazon.com/batch/

USGS Public Dataset
................................................................................

The USGS `3D Elevation Program`_ (3DEP) organizes the national acquisition and
processing of much of the LiDAR elevation content in the United States.
Recently, USGS begun uploading final 3DEP point cloud data into a
``s3://usgs-lidar`` `Requester Pays`_ bucket with 1.4 million tiles `ASPRS
LAS`_ tiles compressed using the `LASzip`_ compression encoding in the
us-west-2 region.  `Hobu, Inc.`_ and the `USACE Cold Regions Research and
Engineering Laboratory`_ collaborated with the AWS Public Datasets team to
organize this data as `Entwine Point Tile`_ (EPT) resources.  You can find out
more about this project on the AWS Public Dataset page.


.. _`Hobu, Inc.`: https://hobu.co
.. _`USACE Cold Regions Research and Engineering Laboratory`: https://www.erdc.usace.army.mil/Locations/CRREL/
.. _`3D Elevation Program`: https://www.usgs.gov/core-science-systems/ngp/3dep
.. _`Requester Pays`: https://docs.aws.amazon.com/AmazonS3/latest/dev/RequesterPaysBuckets.html


Entwine
................................................................................

The open source `Entwine`_ software takes point cloud data and organize them
into single resources called Entwine Point Tiles (EPT). Like their raster- and
vector- tile brethren, EPT provides a simple, deterministic octree tree
structure for clients to access data. EPT also provides implementation
convenience in the form of JSON-based metadata and `LASzip`_-based compressed
encoding. EPT is a lossless data structure that allows software to control the
request pace and resolution of data while being able to predict resource
consumption. This makes it a suitable data structure for supporting
both visualization and exploitation scenarios.



PDAL
................................................................................

`PDAL`_ is open source software for translating, extracting, filtering,
and exploiting geospatial point cloud data. Its latest version
includes a reader for EPT data called `readers.ept`_, and we will use it
in combination with Lamda to read a small section of point cloud data,
use PDAL's filtering operations to remove vegetation, and output
a `digital terrain model`_ for a region.

.. _`readers.ept`: https://pdal.io/stages/readers.ept.html
.. _`digital terrain model`: https://en.wikipedia.org/wiki/Digital_elevation_model

AWS recently introduced the `Lambda Layer
<https://aws.amazon.com/blogs/aws/new-for-aws-lambda-use-any-programming-language-and-share-common-components/>`__
concept to allow developers to stack and version Lambda functionality. For this
exercise, we are taking advantage of a public `PDAL Lambda Layer`_ the PDAL
development team maintains that provides all of the basic library functionality
we will need. Atop that, we will use a Python Lambda function to call PDAL on
for our requested area.


.. _`PDAL Lambda Layer`: https://github.com/PDAL/lambda


Scenario
--------------------------------------------------------------------------------

Our scenario is to create a Python Lambda function that calls `pdal pipeline`_
over a user-specified bounding area of Entwine Point Tile data

.. _`pdal pipeline`: https://pdal.io/pipeline.html

The U.S. Geological Survey (USGS) has been leading the 3D Elevation Program (3DEP) in
various forms since XXXX. 3DEP funds the acquisition of LiDAR data over
the United States, and the USGS makes raw point cloud data and processed
elevation content available for download via FTP servers – much like the same
distribution scenario the Landsat program operates.

Recently, USGS has begun uploading final 3DEP point cloud data into a
``s3://usgs-lidar`` Requester Pays bucket with 1.4 million tiles `ASPRS LAS`_
tiles compressed using the `LASzip`_ compression encoding in the us-west-2
region. USGS has saved us a heavy lift by pushing these data to the cloud,
but they are not organized in a way that we can conveniently utilize the
point cloud data without significant processing.

Information extraction from massive point clouds is a challenging topic, and
developers reach for cloud computing scenarios to achieve performance with
dynamic workloads. Because point cloud data are spatially partitioned in a
straightforward manner, GPU-based computing and highly parallel processing are
a frequently applied computing approach.

The two most common point cloud data capture scenarios are actively scanned
LiDAR and passively processed coincident imagery. Each have use scenarios that
make them more attractive, but they both have the property of providing
overwhelming data volume. Over the past ten years or so, open source software
to compress, organize, and extract information from these point clouds has been
developed. Users can now combine these tools to take advantage of these data
types.

Cost pressure on LiDAR systems, especially driven by the autonomous vehicle
industry, is regularizing data that was once boutique government information.
Governments, on the other hand, have a history of collecting massive LiDAR
collections and then placing them on the shelf due to their challenging nature.
To date, most of these collections have not been fully utilized beyond simple
elevation modeling. An opportunity to do even more exists, but storage,
processing, and network infrastructure are needed to capitalize upon it.

Open Source Software
................................................................................

As mentioned, open source software has matured to process, extract, and exploit
point cloud data. Open source tools are frequently combined with cloud computing
to build data processing workflows, and the tools for point cloud data are mature
enough to meet the challenge. Some typical point cloud processing challenges and
complimentary software include:

* Compression – https://laszip.org
* Organization – https://entwine.io
* Translation – https://pdal.io
* Exploitation – http://lastools.org, https://pdal.io, https://grass.osgeo.org/
* Visualization – http://potree.org/, CloudCompare, http://plas.io

The opportunity cloud infrastructure provides point cloud processing scenarios
is significant. LiDAR data quickly meet any definition of Big Data, with the
simplest being a collection larger than a single typical laptop can hold. Aerial
LiDAR collections over municipalities quickly meet that definition.

.. _`LASzip`: https://laszip.org
.. _`PDAL`: https://pdal.io
.. _`ASPRS LAS`: https://www.asprs.org/divisions-committees/lidar-division/laser-las-file-format-exchange-activities
.. _`Entwine`: https://entwine.io
.. _`Entwine Point Tile`: https://entwine.io/entwine-point-tile.html
